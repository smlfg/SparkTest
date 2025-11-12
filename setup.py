"""
Setup script for Agent 8: Model Optimization
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
with open(requirements_file) as f:
    requirements = [
        line.strip() for line in f
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="agent8-model-optimization",
    version="1.0.0",
    author="SparkTest Team",
    description="Model quantization, compression, and multi-modal inference",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/smlfg/SparkTest",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "agent8-quantize=agent8.cli:quantize_cli",
            "agent8-infer=agent8.cli:inference_cli",
            "agent8-benchmark=agent8.cli:benchmark_cli",
        ],
    },
    include_package_data=True,
    package_data={
        "agent8": [
            "playbooks/*.sh",
            "config/*.json",
        ],
    },
)
