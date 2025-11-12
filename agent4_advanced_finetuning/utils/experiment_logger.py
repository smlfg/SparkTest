"""
Experiment Tracking System for Agent 4
Logs configuration, metrics, and metadata for reproducibility
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib


class ExperimentLogger:
    """
    Comprehensive experiment tracking for fine-tuning workflows

    Tracks:
    - Configuration parameters
    - Metrics per epoch
    - Timestamps
    - Git commit hash (if available)
    - Hardware information
    - Dataset metadata
    """

    def __init__(self, experiment_name: str, output_dir: str = "/workspace/experiments"):
        """
        Initialize experiment logger

        Args:
            experiment_name: Unique identifier for this experiment
            output_dir: Directory to save experiment logs
        """
        self.experiment_name = experiment_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.experiment = {
            "name": experiment_name,
            "started": datetime.now().isoformat(),
            "ended": None,
            "status": "running",
            "config": {},
            "metrics": [],
            "metadata": {
                "git_commit": self._get_git_commit(),
                "hostname": self._get_hostname(),
                "gpu_info": self._get_gpu_info()
            }
        }

        print(f"📊 Experiment Logger initialized: {experiment_name}")
        print(f"📁 Output directory: {self.output_dir}")

    def log_config(self, config: Dict[str, Any]):
        """
        Log experiment configuration

        Args:
            config: Configuration dictionary (hyperparameters, model settings, etc.)
        """
        self.experiment["config"] = config
        print(f"⚙️  Configuration logged: {len(config)} parameters")

    def log_metric(self, epoch: int, metrics: Dict[str, float]):
        """
        Log metrics for a specific epoch

        Args:
            epoch: Epoch number
            metrics: Dictionary of metric name -> value
        """
        metric_entry = {
            "epoch": epoch,
            "timestamp": datetime.now().isoformat(),
            **metrics
        }
        self.experiment["metrics"].append(metric_entry)

        # Print summary
        metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in metrics.items()])
        print(f"📈 Epoch {epoch}: {metrics_str}")

    def log_dataset_info(self, dataset_info: Dict[str, Any]):
        """
        Log dataset metadata

        Args:
            dataset_info: Dataset statistics (size, splits, hash, etc.)
        """
        self.experiment["metadata"]["dataset"] = dataset_info
        print(f"📚 Dataset info logged: {dataset_info.get('name', 'unknown')}")

    def log_checkpoint(self, epoch: int, checkpoint_path: str):
        """
        Log checkpoint location

        Args:
            epoch: Epoch number
            checkpoint_path: Path to saved checkpoint
        """
        if "checkpoints" not in self.experiment:
            self.experiment["checkpoints"] = []

        self.experiment["checkpoints"].append({
            "epoch": epoch,
            "path": checkpoint_path,
            "timestamp": datetime.now().isoformat()
        })
        print(f"💾 Checkpoint logged: epoch {epoch} -> {checkpoint_path}")

    def log_error(self, error_message: str):
        """
        Log error information

        Args:
            error_message: Error description
        """
        self.experiment["status"] = "failed"
        self.experiment["error"] = {
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        print(f"❌ Error logged: {error_message}")

    def finalize(self, status: str = "completed"):
        """
        Mark experiment as finished

        Args:
            status: Final status (completed, failed, interrupted)
        """
        self.experiment["ended"] = datetime.now().isoformat()
        self.experiment["status"] = status

        # Calculate duration
        start = datetime.fromisoformat(self.experiment["started"])
        end = datetime.fromisoformat(self.experiment["ended"])
        duration = (end - start).total_seconds()
        self.experiment["duration_seconds"] = duration

        print(f"🏁 Experiment finalized: {status}")
        print(f"⏱️  Duration: {duration:.1f} seconds")

    def save(self, filename: Optional[str] = None):
        """
        Save experiment log to JSON file

        Args:
            filename: Optional custom filename (defaults to experiment_name.json)
        """
        if filename is None:
            filename = f"{self.experiment_name}.json"

        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(self.experiment, f, indent=2)

        print(f"📊 Experiment saved: {filepath}")
        return str(filepath)

    def get_best_epoch(self, metric: str = "val_loss", mode: str = "min") -> Optional[int]:
        """
        Get epoch with best metric value

        Args:
            metric: Metric name to optimize
            mode: 'min' or 'max'

        Returns:
            Best epoch number or None if no metrics logged
        """
        if not self.experiment["metrics"]:
            return None

        metrics_with_epoch = [
            (m["epoch"], m.get(metric))
            for m in self.experiment["metrics"]
            if metric in m
        ]

        if not metrics_with_epoch:
            return None

        if mode == "min":
            best_epoch = min(metrics_with_epoch, key=lambda x: x[1])[0]
        else:
            best_epoch = max(metrics_with_epoch, key=lambda x: x[1])[0]

        return best_epoch

    def plot_metrics(self, metrics: List[str], save_path: Optional[str] = None):
        """
        Plot training metrics

        Args:
            metrics: List of metric names to plot
            save_path: Optional path to save plot image
        """
        try:
            import matplotlib.pyplot as plt

            epochs = [m["epoch"] for m in self.experiment["metrics"]]

            fig, axes = plt.subplots(len(metrics), 1, figsize=(10, 4 * len(metrics)))
            if len(metrics) == 1:
                axes = [axes]

            for ax, metric in zip(axes, metrics):
                values = [m.get(metric) for m in self.experiment["metrics"]]
                values = [v for v in values if v is not None]

                if values:
                    ax.plot(epochs[:len(values)], values, marker='o')
                    ax.set_xlabel("Epoch")
                    ax.set_ylabel(metric)
                    ax.set_title(f"{metric} over epochs")
                    ax.grid(True)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path)
                print(f"📊 Plot saved: {save_path}")
            else:
                plt.show()

        except ImportError:
            print("⚠️  matplotlib not available, skipping plot")

    # Private helper methods

    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def _get_hostname(self) -> str:
        """Get system hostname"""
        try:
            import socket
            return socket.gethostname()
        except:
            return "unknown"

    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                gpus = []
                for line in lines:
                    parts = line.split(", ")
                    if len(parts) == 2:
                        gpus.append({
                            "name": parts[0],
                            "memory": parts[1]
                        })
                return {"gpus": gpus, "count": len(gpus)}
        except:
            pass
        return {"gpus": [], "count": 0}


def compute_dataset_hash(dataset_path: str) -> str:
    """
    Compute hash of dataset file for versioning

    Args:
        dataset_path: Path to dataset file

    Returns:
        SHA256 hash of file
    """
    sha256_hash = hashlib.sha256()
    with open(dataset_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_experiment(experiment_path: str) -> Dict[str, Any]:
    """
    Load experiment from JSON file

    Args:
        experiment_path: Path to experiment JSON

    Returns:
        Experiment dictionary
    """
    with open(experiment_path) as f:
        return json.load(f)


def compare_experiments(experiment_paths: List[str], metric: str = "val_loss") -> Dict[str, Any]:
    """
    Compare multiple experiments

    Args:
        experiment_paths: List of paths to experiment JSON files
        metric: Metric to compare

    Returns:
        Comparison dictionary
    """
    experiments = [load_experiment(path) for path in experiment_paths]

    comparison = {
        "experiments": [],
        "best_experiment": None,
        "metric": metric
    }

    best_value = float('inf')
    best_exp = None

    for exp_path, exp in zip(experiment_paths, experiments):
        if not exp["metrics"]:
            continue

        # Get final metric value
        final_metrics = exp["metrics"][-1]
        metric_value = final_metrics.get(metric)

        if metric_value is None:
            continue

        exp_summary = {
            "name": exp["name"],
            "path": exp_path,
            "final_" + metric: metric_value,
            "epochs": len(exp["metrics"]),
            "duration": exp.get("duration_seconds", 0),
            "config": exp["config"]
        }

        comparison["experiments"].append(exp_summary)

        if metric_value < best_value:
            best_value = metric_value
            best_exp = exp_summary

    comparison["best_experiment"] = best_exp

    return comparison


if __name__ == "__main__":
    # Example usage
    print("=" * 70)
    print("Experiment Logger - Example Usage")
    print("=" * 70)

    # Create logger
    logger = ExperimentLogger("test-experiment-001")

    # Log configuration
    logger.log_config({
        "model": "Llama-3.1-8B",
        "lora_r": 8,
        "lora_alpha": 16,
        "learning_rate": 2e-4,
        "batch_size": 4,
        "num_epochs": 3
    })

    # Log dataset info
    logger.log_dataset_info({
        "name": "student-chat",
        "num_samples": 1000,
        "splits": {"train": 800, "val": 200}
    })

    # Simulate training
    for epoch in range(1, 4):
        import random
        train_loss = 2.5 - (epoch * 0.3) + random.uniform(-0.1, 0.1)
        val_loss = 2.3 - (epoch * 0.25) + random.uniform(-0.1, 0.1)
        learning_rate = 2e-4 * (0.9 ** epoch)

        logger.log_metric(epoch, {
            "train_loss": train_loss,
            "val_loss": val_loss,
            "learning_rate": learning_rate
        })

        logger.log_checkpoint(epoch, f"/workspace/checkpoints/epoch_{epoch}.pt")

    # Get best epoch
    best_epoch = logger.get_best_epoch("val_loss", "min")
    print(f"\n🏆 Best epoch: {best_epoch}")

    # Finalize and save
    logger.finalize("completed")
    saved_path = logger.save()

    print("\n" + "=" * 70)
    print(f"✅ Experiment completed and saved to: {saved_path}")
    print("=" * 70)
