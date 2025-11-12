"""
Agent Integration Utilities
Agent 6: Integration with Agent 1 (multi-node) and Agent 4 (inference)

This module provides utilities for integrating Agent 6 with other agents
in the system for distributed training and validation.
"""

import os
import sys
import requests
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from agent6_training_config import AGENT_INTEGRATION


class Agent1Connector:
    """
    Connector for Agent 1 multi-node orchestration.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize Agent 1 connector.

        Args:
            endpoint: Agent 1 API endpoint
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint or AGENT_INTEGRATION["agent1"]["multi_node_endpoint"]
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def discover_nodes(self) -> List[Dict[str, Any]]:
        """
        Discover available nodes from Agent 1.

        Returns:
            List of node information dictionaries
        """
        try:
            response = requests.get(
                f"{self.endpoint}/discover",
                timeout=self.timeout,
            )
            response.raise_for_status()
            nodes = response.json().get("nodes", [])
            self.logger.info(f"Discovered {len(nodes)} nodes from Agent 1")
            return nodes
        except requests.RequestException as e:
            self.logger.error(f"Failed to discover nodes: {e}")
            return []

    def register_training_job(
        self,
        job_id: str,
        config: Dict[str, Any],
    ) -> bool:
        """
        Register a training job with Agent 1.

        Args:
            job_id: Unique job identifier
            config: Job configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "job_id": job_id,
                "agent": "agent6",
                "config": config,
            }
            response = requests.post(
                f"{self.endpoint}/register",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            self.logger.info(f"Registered training job {job_id} with Agent 1")
            return True
        except requests.RequestException as e:
            self.logger.error(f"Failed to register job: {e}")
            return False

    def sync_checkpoint(
        self,
        checkpoint_path: str,
        node_ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Synchronize checkpoint across nodes via Agent 1.

        Args:
            checkpoint_path: Path to checkpoint
            node_ids: Target node IDs (None for all nodes)

        Returns:
            True if successful, False otherwise
        """
        if not AGENT_INTEGRATION["agent1"]["sync_checkpoints"]:
            return True

        try:
            payload = {
                "checkpoint_path": checkpoint_path,
                "node_ids": node_ids,
            }
            response = requests.post(
                f"{self.endpoint}/sync_checkpoint",
                json=payload,
                timeout=self.timeout * 2,  # Longer timeout for file sync
            )
            response.raise_for_status()
            self.logger.info(f"Synchronized checkpoint {checkpoint_path}")
            return True
        except requests.RequestException as e:
            self.logger.error(f"Failed to sync checkpoint: {e}")
            return False

    def get_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific node.

        Args:
            node_id: Node identifier

        Returns:
            Node status dictionary or None if failed
        """
        try:
            response = requests.get(
                f"{self.endpoint}/nodes/{node_id}/status",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to get node status: {e}")
            return None


class Agent4Connector:
    """
    Connector for Agent 4 inference validation.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        timeout: int = 60,
    ):
        """
        Initialize Agent 4 connector.

        Args:
            endpoint: Agent 4 API endpoint
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint or AGENT_INTEGRATION["agent4"]["inference_endpoint"]
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def run_inference(
        self,
        model_path: str,
        prompt: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Run inference using Agent 4.

        Args:
            model_path: Path to model checkpoint
            prompt: Input prompt
            config: Inference configuration

        Returns:
            Generated text or None if failed
        """
        try:
            payload = {
                "model_path": model_path,
                "prompt": prompt,
                "config": config or {},
            }
            response = requests.post(
                f"{self.endpoint}/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("generated_text")
        except requests.RequestException as e:
            self.logger.error(f"Failed to run inference: {e}")
            return None

    def validate_checkpoint(
        self,
        checkpoint_path: str,
        validation_prompts: List[str],
        metrics: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Validate checkpoint using Agent 4.

        Args:
            checkpoint_path: Path to checkpoint
            validation_prompts: List of validation prompts
            metrics: Metrics to compute

        Returns:
            Validation results or None if failed
        """
        try:
            payload = {
                "checkpoint_path": checkpoint_path,
                "prompts": validation_prompts,
                "metrics": metrics or ["perplexity", "quality"],
            }
            response = requests.post(
                f"{self.endpoint}/validate",
                json=payload,
                timeout=self.timeout * len(validation_prompts),
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to validate checkpoint: {e}")
            return None

    def batch_inference(
        self,
        model_path: str,
        prompts: List[str],
        batch_size: int = 8,
    ) -> List[Optional[str]]:
        """
        Run batch inference using Agent 4.

        Args:
            model_path: Path to model checkpoint
            prompts: List of input prompts
            batch_size: Batch size for inference

        Returns:
            List of generated texts
        """
        try:
            payload = {
                "model_path": model_path,
                "prompts": prompts,
                "batch_size": batch_size,
            }
            response = requests.post(
                f"{self.endpoint}/batch_generate",
                json=payload,
                timeout=self.timeout * (len(prompts) // batch_size + 1),
            )
            response.raise_for_status()
            result = response.json()
            return result.get("generated_texts", [])
        except requests.RequestException as e:
            self.logger.error(f"Failed to run batch inference: {e}")
            return [None] * len(prompts)


class TrainingValidator:
    """
    Integrated training validator using Agent 4.
    """

    def __init__(
        self,
        agent4_connector: Optional[Agent4Connector] = None,
        validation_interval: Optional[int] = None,
        validation_prompts: Optional[List[str]] = None,
    ):
        """
        Initialize training validator.

        Args:
            agent4_connector: Agent 4 connector
            validation_interval: Steps between validations
            validation_prompts: Prompts for validation
        """
        self.agent4 = agent4_connector or Agent4Connector()
        self.validation_interval = (
            validation_interval or
            AGENT_INTEGRATION["agent4"]["validation_interval"]
        )
        self.validation_prompts = validation_prompts or [
            "The quick brown fox",
            "Once upon a time",
            "In a galaxy far away",
        ]
        self.logger = logging.getLogger(__name__)
        self.validation_history = []

    def should_validate(self, step: int) -> bool:
        """Check if validation should run at this step."""
        return step % self.validation_interval == 0

    def validate_step(
        self,
        checkpoint_path: str,
        step: int,
        metrics: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Run validation at a training step.

        Args:
            checkpoint_path: Path to checkpoint
            step: Training step
            metrics: Training metrics

        Returns:
            Validation results
        """
        self.logger.info(f"Running validation at step {step}")

        # Run inference validation
        results = self.agent4.validate_checkpoint(
            checkpoint_path,
            self.validation_prompts,
        )

        if results:
            validation_data = {
                "step": step,
                "checkpoint": checkpoint_path,
                "training_metrics": metrics or {},
                "validation_results": results,
            }
            self.validation_history.append(validation_data)
            self.logger.info(f"Validation completed: {results}")
            return validation_data
        else:
            self.logger.warning("Validation failed")
            return {"step": step, "status": "failed"}

    def get_validation_history(self) -> List[Dict[str, Any]]:
        """Get validation history."""
        return self.validation_history

    def save_validation_history(self, output_path: str):
        """Save validation history to file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.validation_history, f, indent=2)
        self.logger.info(f"Validation history saved to {output_path}")


def setup_multi_node_training(
    num_nodes: int,
    master_addr: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Setup multi-node training environment using Agent 1.

    Args:
        num_nodes: Number of nodes to use
        master_addr: Master node address (discovered if None)

    Returns:
        Multi-node configuration
    """
    logger = logging.getLogger(__name__)

    # Connect to Agent 1
    agent1 = Agent1Connector()

    # Discover nodes
    nodes = agent1.discover_nodes()

    if len(nodes) < num_nodes:
        logger.warning(
            f"Requested {num_nodes} nodes but only {len(nodes)} available"
        )
        num_nodes = len(nodes)

    # Select nodes
    selected_nodes = nodes[:num_nodes]

    # Determine master
    if master_addr is None:
        master_addr = selected_nodes[0]["address"]

    config = {
        "num_nodes": num_nodes,
        "master_addr": master_addr,
        "master_port": 29500,
        "nodes": selected_nodes,
    }

    logger.info(f"Multi-node configuration: {config}")
    return config


def main():
    """Example usage of agent integration utilities."""
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Agent Integration Utilities")
    print("=" * 60)

    # Test Agent 1 connection
    print("\nTesting Agent 1 connection...")
    agent1 = Agent1Connector()
    nodes = agent1.discover_nodes()
    print(f"Found {len(nodes)} nodes")

    # Test Agent 4 connection
    print("\nTesting Agent 4 connection...")
    agent4 = Agent4Connector()
    # result = agent4.run_inference(
    #     model_path="/workspace/checkpoints/test",
    #     prompt="Hello, world!",
    # )
    print("Agent 4 connector initialized")

    # Setup validator
    print("\nSetting up training validator...")
    validator = TrainingValidator()
    print(f"Validation interval: {validator.validation_interval} steps")


if __name__ == "__main__":
    main()
