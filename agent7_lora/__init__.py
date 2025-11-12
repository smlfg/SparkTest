"""
Agent 7: LoRA Fine-tuning System
Efficient fine-tuning with Unsloth, LLaMA Factory, and VLM support
"""

__version__ = "1.0.0"
__author__ = "Agent 7 Team"

from pathlib import Path

# Package information
PACKAGE_ROOT = Path(__file__).parent
WORKSPACE_DIR = PACKAGE_ROOT.parent / "workspace"

# Ensure workspace exists
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
(WORKSPACE_DIR / "loras").mkdir(parents=True, exist_ok=True)

__all__ = [
    "pipelines",
    "ui",
    "vlm",
    "adapters",
    "scripts",
    "configs"
]
