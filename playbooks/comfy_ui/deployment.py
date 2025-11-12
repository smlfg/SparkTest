"""
ComfyUI Deployment Playbook
Advanced image generation interface with node-based workflow editor

Dependencies: Agent 4/5 (inference), Agent 8 (multi-modal)
"""

import asyncio
import aiohttp
import json
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class WorkflowNode:
    """Represents a node in the ComfyUI workflow"""
    node_id: str
    class_type: str
    inputs: Dict[str, Any]


@dataclass
class ComfyWorkflow:
    """Complete ComfyUI workflow definition"""
    nodes: Dict[str, WorkflowNode]
    prompt: str
    seed: Optional[int] = None


class ComfyUIClient:
    """
    Client for interacting with ComfyUI API
    Integrates with Agent 4/5 for model inference and Agent 8 for multi-modal processing
    """

    def __init__(self, base_url: str = "http://localhost:8188"):
        self.base_url = base_url
        self.client_id = str(uuid.uuid4())

    async def check_health(self) -> bool:
        """Check if ComfyUI server is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/system_stats") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def get_models(self) -> List[str]:
        """Retrieve available models from inference agents"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/object_info") as response:
                    if response.status == 200:
                        data = await response.json()
                        # Extract checkpoint models
                        checkpoints = data.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]
                        return checkpoints
                    return []
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []

    def create_txt2img_workflow(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        seed: Optional[int] = None,
        model: str = "sd_xl_base_1.0.safetensors"
    ) -> Dict[str, Any]:
        """
        Create a text-to-image workflow for ComfyUI

        Args:
            prompt: Positive prompt for image generation
            negative_prompt: Negative prompt
            width: Image width
            height: Image height
            steps: Number of inference steps
            cfg_scale: Classifier-free guidance scale
            seed: Random seed (None for random)
            model: Model checkpoint name

        Returns:
            Workflow dictionary ready for ComfyUI API
        """
        if seed is None:
            seed = int.from_bytes(uuid.uuid4().bytes[:4], 'big') % (2**31)

        workflow = {
            "3": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {
                    "ckpt_name": model
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "5": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "6": {
                "inputs": {
                    "text": prompt,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode"
            },
            "9": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage"
            }
        }

        return workflow

    async def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """
        Queue a workflow for execution

        Args:
            workflow: ComfyUI workflow dictionary

        Returns:
            Prompt ID for tracking execution
        """
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/prompt",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["prompt_id"]
                else:
                    raise Exception(f"Failed to queue prompt: {response.status}")

    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get execution history for a prompt"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/history/{prompt_id}") as response:
                if response.status == 200:
                    return await response.json()
                return {}

    async def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Download generated image"""
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/view", params=params) as response:
                if response.status == 200:
                    return await response.read()
                raise Exception(f"Failed to get image: {response.status}")

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        timeout: int = 300
    ) -> Optional[bytes]:
        """
        High-level method to generate an image

        Args:
            prompt: Text prompt for image generation
            negative_prompt: Negative prompt
            width: Image width
            height: Image height
            steps: Number of inference steps
            timeout: Maximum time to wait for generation

        Returns:
            Image bytes or None if failed
        """
        # Create workflow
        workflow = self.create_txt2img_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps
        )

        # Queue the workflow
        prompt_id = await self.queue_prompt(workflow)
        logger.info(f"Queued prompt {prompt_id}")

        # Poll for completion
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            history = await self.get_history(prompt_id)

            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})

                # Find the SaveImage node output
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        images = node_output["images"]
                        if images:
                            # Get the first image
                            img_info = images[0]
                            return await self.get_image(
                                img_info["filename"],
                                img_info.get("subfolder", ""),
                                img_info.get("type", "output")
                            )

            await asyncio.sleep(2)

        logger.error("Timeout waiting for image generation")
        return None


class ComfyUIDeployment:
    """Manages ComfyUI deployment and configuration"""

    def __init__(self, port: int = 8188):
        self.port = port
        self.client = ComfyUIClient(f"http://localhost:{port}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        is_healthy = await self.client.check_health()

        result = {
            "status": "healthy" if is_healthy else "unhealthy",
            "port": self.port,
            "url": f"http://localhost:{self.port}"
        }

        if is_healthy:
            models = await self.client.get_models()
            result["available_models"] = len(models)
            result["models"] = models[:5]  # First 5 models

        return result

    def get_docker_compose_config(self) -> str:
        """Generate Docker Compose configuration for ComfyUI deployment"""
        return f"""version: '3.8'

services:
  comfyui:
    image: comfyui/comfyui:latest
    ports:
      - "{self.port}:8188"
    volumes:
      - ./models:/app/models
      - ./input:/app/input
      - ./output:/app/output
      - ./custom_nodes:/app/custom_nodes
    environment:
      - CLI_ARGS=--listen 0.0.0.0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  # Integration with Agent 4/5 inference services
  inference-proxy:
    image: nginx:alpine
    ports:
      - "8189:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - comfyui
    restart: unless-stopped
"""


async def main():
    """Demo ComfyUI deployment and usage"""
    print("ComfyUI Deployment Playbook")
    print("=" * 50)

    deployment = ComfyUIDeployment(port=8188)

    # Health check
    print("\nPerforming health check...")
    health = await deployment.health_check()
    print(f"Status: {health['status']}")
    print(f"URL: {health['url']}")

    if health['status'] == 'healthy':
        print(f"Available models: {health['available_models']}")

        # Example: Generate an image
        print("\nExample: Text-to-Image Generation")
        print("-" * 50)

        client = deployment.client
        prompt = "A beautiful sunset over mountains, highly detailed, 4k"
        negative_prompt = "blurry, low quality, distorted"

        print(f"Prompt: {prompt}")
        print("Generating image...")

        # Note: This will actually attempt to generate if ComfyUI is running
        # image_bytes = await client.generate_image(
        #     prompt=prompt,
        #     negative_prompt=negative_prompt,
        #     width=512,
        #     height=512,
        #     steps=20
        # )
        #
        # if image_bytes:
        #     print(f"Successfully generated image ({len(image_bytes)} bytes)")

    # Print Docker Compose config
    print("\n" + "=" * 50)
    print("Docker Compose Configuration:")
    print("=" * 50)
    print(deployment.get_docker_compose_config())


if __name__ == "__main__":
    asyncio.run(main())
