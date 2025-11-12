# Agent 3: Development Environment Templates

This directory contains pre-configured development environment templates for various programming languages and frameworks.

## Available Templates

### 1. **Python Machine Learning** (`python-ml.env`)
Environment for Python-based machine learning development with JAX.

**Setup:**
```bash
source agent3/templates/python-ml.env
python -m venv .venv
source .venv/bin/activate
pip install jax jaxlib numpy scipy jupyter
```

**Features:**
- JAX optimized configuration
- Jupyter Lab integration
- TensorBoard support
- Testing with pytest

### 2. **Rust Development** (`rust-dev.env`)
Environment for Rust development with ARM64 cross-compilation.

**Setup:**
```bash
source agent3/templates/rust-dev.env
rustup install stable
rustup target add aarch64-unknown-linux-gnu
```

**Features:**
- ARM64 cross-compilation
- Incremental compilation
- Fast linking with lld
- Clippy linting

### 3. **Go Development** (`go-dev.env`)
Environment for Go development with module support.

**Setup:**
```bash
source agent3/templates/go-dev.env
go mod init <project-name>
go mod tidy
```

**Features:**
- Go modules enabled
- ARM64 architecture support
- Race detection in tests
- Coverage reporting

### 4. **C/C++ Development** (`cpp-dev.env`)
Environment for modern C/C++ development with CMake.

**Setup:**
```bash
source agent3/templates/cpp-dev.env
cmake -B build -G Ninja
cmake --build build
```

**Features:**
- C++20 standard
- Clang/LLVM toolchain
- Ninja build system
- Address/UB sanitizers

### 5. **Dev Container** (`devcontainer.json`)
VS Code Dev Container configuration for containerized development.

**Setup:**
1. Open project in VS Code
2. Install "Dev Containers" extension
3. Run: "Dev Containers: Reopen in Container"

**Features:**
- Full IDE in container
- Pre-installed extensions
- Port forwarding
- Git integration

## Usage

### Quick Start

1. Choose a template based on your project type
2. Source the environment file:
   ```bash
   source agent3/templates/<template-name>.env
   ```
3. Follow the specific setup instructions above

### Combining Templates

You can source multiple templates for polyglot projects:
```bash
source agent3/templates/python-ml.env
source agent3/templates/cpp-dev.env
```

### Custom Modifications

Copy a template and modify it for your specific needs:
```bash
cp agent3/templates/python-ml.env .env.local
# Edit .env.local with your customizations
source .env.local
```

## Integration with Agent 3

These templates work seamlessly with Agent 3 launch scripts:

```bash
# Launch VS Code Server with Python ML template
source agent3/templates/python-ml.env
./agent3_launch.sh --vscode

# Launch JAX container with custom template
source agent3/templates/python-ml.env
./agent3_launch.sh --jax
```

## Environment Variables Reference

Common variables across templates:

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Project identifier | `<lang>-project` |
| `PATH` | Extended path with tools | System + tools |
| `*_HOME` | Tool home directories | Language specific |

### Python ML Specific
- `JAX_PLATFORM_NAME`: JAX backend (cpu/gpu)
- `JUPYTER_PORT`: Jupyter server port
- `PYTHONPATH`: Python module search path

### Rust Specific
- `CARGO_BUILD_TARGET`: Cross-compilation target
- `RUSTFLAGS`: Compiler flags
- `RUST_BACKTRACE`: Error stack traces

### Go Specific
- `GOARCH`: Target architecture
- `GOPROXY`: Module proxy
- `GOMAXPROCS`: Parallel execution

### C/C++ Specific
- `CMAKE_BUILD_TYPE`: Build configuration
- `CMAKE_GENERATOR`: Build system
- `ASAN_OPTIONS`: Sanitizer options

## Best Practices

1. **Source at project root**: Always run from your project's root directory
2. **Virtual environments**: Use language-specific isolation (venv, cargo workspace, etc.)
3. **Version control**: Add `.env.local` to `.gitignore` for local customizations
4. **Docker integration**: Templates work inside containers via volume mounts
5. **CI/CD**: Source templates in CI scripts for consistent builds

## Troubleshooting

### Template not working
```bash
# Check if template file exists
ls -la agent3/templates/

# Verify sourcing
echo $PROJECT_NAME
```

### Path conflicts
```bash
# Reset PATH before sourcing
export PATH="/usr/local/bin:/usr/bin:/bin"
source agent3/templates/<template>.env
```

### Tool not found
```bash
# Install missing tools
# For Python
pip install -r requirements.txt

# For Rust
rustup component add clippy rustfmt

# For Go
go install <tool>@latest

# For C++
sudo apt install clang cmake ninja-build
```

## Contributing

To add a new template:

1. Create `<language>-dev.env` in `agent3/templates/`
2. Follow the existing format
3. Add documentation to this README
4. Test with `agent3_launch.sh`

## See Also

- [VS Code Playbook](../playbooks/vscode.yml)
- [JAX Container](../containers/jax-arm64.Dockerfile)
- [Launch Script](../../agent3_launch.sh)
