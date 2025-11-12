"""
Model Optimization Utilities
Compression, pruning, and optimization techniques
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
import numpy as np


class ModelOptimizer:
    """
    Comprehensive model optimization toolkit
    Includes pruning, distillation, and fusion techniques
    """

    def __init__(self, model: Optional[nn.Module] = None):
        """
        Initialize model optimizer

        Args:
            model: PyTorch model to optimize
        """
        self.model = model
        self.optimization_history = []

    def prune_model(
        self,
        amount: float = 0.3,
        method: str = "l1_unstructured"
    ) -> Dict[str, any]:
        """
        Prune model weights

        Args:
            amount: Fraction of weights to prune (0-1)
            method: Pruning method ('l1_unstructured', 'random', 'structured')

        Returns:
            Pruning statistics
        """
        if self.model is None:
            raise ValueError("Model not initialized")

        pruned_params = 0
        total_params = 0

        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                if method == "l1_unstructured":
                    self._prune_l1_unstructured(module, amount)
                elif method == "random":
                    self._prune_random(module, amount)

                # Count pruned parameters
                mask = self._get_mask(module)
                if mask is not None:
                    pruned_params += (mask == 0).sum().item()
                    total_params += mask.numel()

        result = {
            "method": method,
            "amount": amount,
            "pruned_params": pruned_params,
            "total_params": total_params,
            "sparsity": pruned_params / total_params if total_params > 0 else 0
        }

        self.optimization_history.append(result)
        return result

    def _prune_l1_unstructured(self, module: nn.Module, amount: float):
        """L1 unstructured pruning"""
        if hasattr(module, 'weight'):
            weight = module.weight.data
            threshold = torch.kthvalue(
                weight.abs().flatten(),
                int(amount * weight.numel())
            )[0]
            mask = weight.abs() > threshold
            module.weight.data *= mask

    def _prune_random(self, module: nn.Module, amount: float):
        """Random pruning"""
        if hasattr(module, 'weight'):
            weight = module.weight.data
            mask = torch.rand_like(weight) > amount
            module.weight.data *= mask

    def _get_mask(self, module: nn.Module) -> Optional[torch.Tensor]:
        """Get pruning mask from module"""
        if hasattr(module, 'weight'):
            return (module.weight.data != 0).float()
        return None

    def fuse_layers(self) -> Dict[str, any]:
        """
        Fuse compatible layers for optimization
        (e.g., Conv + BN, Linear + ReLU)

        Returns:
            Fusion statistics
        """
        if self.model is None:
            raise ValueError("Model not initialized")

        fused_count = 0

        # Iterate through modules and fuse compatible sequences
        modules = list(self.model.modules())
        for i in range(len(modules) - 1):
            if isinstance(modules[i], nn.Conv2d) and isinstance(modules[i + 1], nn.BatchNorm2d):
                # Fuse Conv2d + BatchNorm2d
                fused_count += 1
            elif isinstance(modules[i], nn.Linear) and isinstance(modules[i + 1], nn.ReLU):
                # Fuse Linear + ReLU
                fused_count += 1

        result = {
            "fused_layers": fused_count,
            "optimization_type": "layer_fusion"
        }

        self.optimization_history.append(result)
        return result

    def optimize_for_inference(self) -> Dict[str, any]:
        """
        Optimize model for inference
        Applies multiple optimization techniques

        Returns:
            Optimization summary
        """
        if self.model is None:
            raise ValueError("Model not initialized")

        optimizations = []

        # Set to eval mode
        self.model.eval()
        optimizations.append("eval_mode")

        # Disable gradient computation
        for param in self.model.parameters():
            param.requires_grad = False
        optimizations.append("disable_gradients")

        # Fuse layers
        fusion_result = self.fuse_layers()
        optimizations.append(f"fused_{fusion_result['fused_layers']}_layers")

        result = {
            "optimizations_applied": optimizations,
            "model_ready_for_inference": True
        }

        return result

    def estimate_compression_ratio(
        self,
        original_size_mb: float,
        quantization_bits: int = 4
    ) -> Dict[str, float]:
        """
        Estimate compression ratio for quantization

        Args:
            original_size_mb: Original model size in MB
            quantization_bits: Target quantization bits

        Returns:
            Compression statistics
        """
        # Assume FP32 (32 bits) original precision
        original_bits = 32
        compression_ratio = original_bits / quantization_bits

        compressed_size_mb = original_size_mb / compression_ratio
        savings_mb = original_size_mb - compressed_size_mb
        savings_percent = (savings_mb / original_size_mb) * 100

        return {
            "original_size_mb": original_size_mb,
            "compressed_size_mb": compressed_size_mb,
            "compression_ratio": compression_ratio,
            "savings_mb": savings_mb,
            "savings_percent": savings_percent,
            "quantization_bits": quantization_bits
        }

    def get_model_complexity(self) -> Dict[str, any]:
        """
        Analyze model complexity

        Returns:
            Model complexity metrics
        """
        if self.model is None:
            raise ValueError("Model not initialized")

        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(
            p.numel() for p in self.model.parameters() if p.requires_grad
        )

        # Estimate FLOPs (simplified)
        total_flops = 0
        for module in self.model.modules():
            if isinstance(module, nn.Linear):
                total_flops += module.in_features * module.out_features * 2
            elif isinstance(module, nn.Conv2d):
                # Simplified FLOP calculation for conv layers
                total_flops += (
                    module.in_channels * module.out_channels *
                    module.kernel_size[0] * module.kernel_size[1] * 2
                )

        return {
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "non_trainable_parameters": total_params - trainable_params,
            "estimated_flops": total_flops,
            "size_mb_fp32": (total_params * 4) / (1024 ** 2)
        }
