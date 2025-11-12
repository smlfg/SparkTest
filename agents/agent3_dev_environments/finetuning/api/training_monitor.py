#!/usr/bin/env python3
"""
Training Progress Monitor API
Real-time monitoring of LLaMA Factory fine-tuning jobs via WebSocket
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


app = FastAPI(
    title="LLaMA Factory Training Monitor",
    description="Real-time monitoring API for fine-tuning jobs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global state
active_connections: Dict[str, List[WebSocket]] = {}
training_jobs: Dict[str, Dict] = {}


class TrainingLogParser:
    """Parse LLaMA Factory training logs"""

    @staticmethod
    def parse_loss_line(line: str) -> Optional[Dict]:
        """
        Parse training loss from log line

        Examples:
        - "{'loss': 0.234, 'learning_rate': 1e-4, 'epoch': 2.5}"
        - "Epoch 2/5 | Loss: 0.234 | LR: 1e-4"
        """
        # Try JSON-like format
        if "loss" in line.lower():
            # Extract loss value
            loss_match = re.search(r"['\"]?loss['\"]?\s*:\s*([\d.]+)", line, re.IGNORECASE)
            lr_match = re.search(r"['\"]?learning_rate['\"]?\s*:\s*([\d.e-]+)", line, re.IGNORECASE)
            epoch_match = re.search(r"['\"]?epoch['\"]?\s*:\s*([\d.]+)", line, re.IGNORECASE)

            if loss_match:
                result = {
                    "type": "loss_update",
                    "loss": float(loss_match.group(1)),
                    "timestamp": datetime.now().isoformat()
                }

                if lr_match:
                    result["learning_rate"] = float(lr_match.group(1))
                if epoch_match:
                    result["epoch"] = float(epoch_match.group(1))

                return result

        return None

    @staticmethod
    def parse_progress_line(line: str) -> Optional[Dict]:
        """
        Parse training progress

        Examples:
        - "Training: 50% |████████████          | 500/1000 [00:30<00:30, 16.67it/s]"
        - "Step 500/1000 (50.0%)"
        """
        # Try tqdm-style progress
        progress_match = re.search(r"(\d+)%|(\d+)/(\d+)", line)

        if progress_match:
            if progress_match.group(1):
                # Percentage format
                percent = int(progress_match.group(1))
            elif progress_match.group(2) and progress_match.group(3):
                # Fraction format
                current = int(progress_match.group(2))
                total = int(progress_match.group(3))
                percent = int((current / total) * 100)
            else:
                return None

            return {
                "type": "progress_update",
                "progress": percent,
                "timestamp": datetime.now().isoformat()
            }

        return None

    @staticmethod
    def parse_metric_line(line: str) -> Optional[Dict]:
        """
        Parse evaluation metrics

        Examples:
        - "eval_loss: 0.123"
        - "eval_accuracy: 0.95"
        """
        metric_patterns = [
            (r"eval_loss['\"]?\s*:\s*([\d.]+)", "eval_loss"),
            (r"eval_accuracy['\"]?\s*:\s*([\d.]+)", "eval_accuracy"),
            (r"perplexity['\"]?\s*:\s*([\d.]+)", "perplexity"),
        ]

        for pattern, metric_name in metric_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return {
                    "type": "metric_update",
                    "metric": metric_name,
                    "value": float(match.group(1)),
                    "timestamp": datetime.now().isoformat()
                }

        return None


async def tail_log_file(file_path: Path, websocket: WebSocket, job_id: str):
    """
    Tail a log file and send updates via WebSocket

    Args:
        file_path: Path to log file
        websocket: WebSocket connection
        job_id: Training job ID
    """
    parser = TrainingLogParser()

    try:
        # Open file and seek to end
        with open(file_path, 'r') as f:
            # Go to end of file
            f.seek(0, 2)

            while True:
                line = f.readline()

                if not line:
                    # No new data, wait a bit
                    await asyncio.sleep(1)
                    continue

                # Parse line for different types of information
                parsed_data = (
                    parser.parse_loss_line(line) or
                    parser.parse_progress_line(line) or
                    parser.parse_metric_line(line)
                )

                if parsed_data:
                    parsed_data["job_id"] = job_id
                    await websocket.send_json(parsed_data)

                # Also send raw log line
                await websocket.send_json({
                    "type": "log_line",
                    "job_id": job_id,
                    "line": line.strip(),
                    "timestamp": datetime.now().isoformat()
                })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e),
            "job_id": job_id
        })


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/jobs")
async def list_jobs():
    """List all training jobs"""
    output_dir = Path("/app/output")

    if not output_dir.exists():
        return {"jobs": []}

    jobs = []
    for job_dir in output_dir.iterdir():
        if job_dir.is_dir():
            job_info = {
                "job_id": job_dir.name,
                "created": datetime.fromtimestamp(job_dir.stat().st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(job_dir.stat().st_mtime).isoformat(),
                "status": "unknown"
            }

            # Check for log file
            log_file = job_dir / "training.log"
            if log_file.exists():
                job_info["has_logs"] = True
                job_info["log_size"] = log_file.stat().st_size
            else:
                # Try common log locations
                logs_dir = job_dir / "logs"
                if logs_dir.exists():
                    log_files = list(logs_dir.glob("*.log"))
                    if log_files:
                        job_info["has_logs"] = True
                        job_info["log_file"] = str(log_files[0])

            # Check for checkpoint
            if (job_dir / "checkpoint-final").exists() or list(job_dir.glob("checkpoint-*")):
                job_info["status"] = "completed"
            elif job_info.get("has_logs"):
                job_info["status"] = "running"

            jobs.append(job_info)

    return {"jobs": jobs, "count": len(jobs)}


@app.get("/api/jobs/{job_id}")
async def get_job_info(job_id: str):
    """Get detailed information about a training job"""
    job_dir = Path("/app/output") / job_id

    if not job_dir.exists():
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    info = {
        "job_id": job_id,
        "path": str(job_dir),
        "created": datetime.fromtimestamp(job_dir.stat().st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(job_dir.stat().st_mtime).isoformat(),
    }

    # Find checkpoints
    checkpoints = []
    for ckpt in sorted(job_dir.glob("checkpoint-*")):
        if ckpt.is_dir():
            checkpoints.append({
                "name": ckpt.name,
                "path": str(ckpt),
                "created": datetime.fromtimestamp(ckpt.stat().st_ctime).isoformat()
            })
    info["checkpoints"] = checkpoints

    # Find logs
    log_files = []
    logs_dir = job_dir / "logs"
    if logs_dir.exists():
        for log in logs_dir.glob("*.log"):
            log_files.append({
                "name": log.name,
                "path": str(log),
                "size": log.stat().st_size
            })
    info["log_files"] = log_files

    # Check for config
    config_file = job_dir / "config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                info["config"] = json.load(f)
        except:
            pass

    return info


@app.get("/api/jobs/{job_id}/logs")
async def get_job_logs(job_id: str, lines: int = 100):
    """Get recent log lines from a training job"""
    job_dir = Path("/app/output") / job_id

    if not job_dir.exists():
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Find log file
    log_file = job_dir / "training.log"
    if not log_file.exists():
        logs_dir = job_dir / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                log_file = log_files[0]
            else:
                raise HTTPException(status_code=404, detail="No log file found")
        else:
            raise HTTPException(status_code=404, detail="No log file found")

    # Read last N lines
    with open(log_file) as f:
        all_lines = f.readlines()
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

    return {
        "job_id": job_id,
        "log_file": str(log_file),
        "total_lines": len(all_lines),
        "returned_lines": len(recent_lines),
        "lines": [line.strip() for line in recent_lines]
    }


@app.websocket("/ws/training/{job_id}")
async def training_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time training updates

    Args:
        websocket: WebSocket connection
        job_id: Training job ID to monitor
    """
    await websocket.accept()

    # Add to active connections
    if job_id not in active_connections:
        active_connections[job_id] = []
    active_connections[job_id].append(websocket)

    try:
        # Find log file
        job_dir = Path("/app/output") / job_id

        if not job_dir.exists():
            await websocket.send_json({
                "type": "error",
                "message": f"Job directory not found: {job_id}"
            })
            await websocket.close()
            return

        # Look for log file
        log_file = job_dir / "training.log"
        if not log_file.exists():
            logs_dir = job_dir / "logs"
            if logs_dir.exists():
                log_files = list(logs_dir.glob("*.log"))
                if log_files:
                    log_file = log_files[0]
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No log file found"
                    })
                    await websocket.close()
                    return

        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "log_file": str(log_file),
            "timestamp": datetime.now().isoformat()
        })

        # Start tailing log file
        await tail_log_file(log_file, websocket, job_id)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        print(f"Error in WebSocket: {e}")
    finally:
        # Remove from active connections
        if job_id in active_connections:
            active_connections[job_id].remove(websocket)
            if not active_connections[job_id]:
                del active_connections[job_id]


@app.get("/api/stats")
async def get_stats():
    """Get global statistics"""
    output_dir = Path("/app/output")

    total_jobs = 0
    total_checkpoints = 0
    total_size = 0

    if output_dir.exists():
        for job_dir in output_dir.iterdir():
            if job_dir.is_dir():
                total_jobs += 1

                # Count checkpoints
                checkpoints = list(job_dir.glob("checkpoint-*"))
                total_checkpoints += len(checkpoints)

                # Calculate size
                for item in job_dir.rglob("*"):
                    if item.is_file():
                        total_size += item.stat().st_size

    return {
        "total_jobs": total_jobs,
        "total_checkpoints": total_checkpoints,
        "total_size_bytes": total_size,
        "total_size_gb": round(total_size / (1024**3), 2),
        "active_connections": sum(len(conns) for conns in active_connections.values()),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("MONITOR_PORT", "8000")),
        log_level="info"
    )
