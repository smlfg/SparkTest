#!/bin/bash
# JAX Container Entrypoint Script

set -e

echo "========================================="
echo "JAX ARM64 Container"
echo "========================================="
echo "Python version: $(python --version)"
echo "JAX version: $(python -c 'import jax; print(jax.__version__)')"
echo "JAX devices: $(python -c 'import jax; print(jax.devices())')"
echo "========================================="

# Run JAX device check
python3 <<EOF
import jax
import jax.numpy as jnp

print("\n[JAX Configuration]")
print(f"JAX version: {jax.__version__}")
print(f"Available devices: {jax.devices()}")
print(f"Default backend: {jax.default_backend()}")

# Simple computation test
x = jnp.array([1, 2, 3, 4, 5])
y = jnp.sum(x ** 2)
print(f"\nTest computation: sum([1,2,3,4,5]^2) = {y}")
print("\n[JAX Ready!]")
EOF

# Execute the main command
exec "$@"
