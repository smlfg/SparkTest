# Contributing to Agent 3: Development Environments

Thank you for your interest in contributing to Agent 3! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Submitting Changes](#submitting-changes)
7. [Style Guidelines](#style-guidelines)

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to learn and improve.

## Getting Started

### Prerequisites

- Docker installed and running
- Git configured
- Basic knowledge of shell scripting
- (Optional) Ansible for playbook development

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/SparkTest.git
cd SparkTest

# Add upstream remote
git remote add upstream https://github.com/smlfg/SparkTest.git
```

## Development Setup

### Initial Setup

```bash
# Make scripts executable
chmod +x agent3_launch.sh agent3/playbooks/*.sh agent3/containers/*.sh

# Test basic functionality
./agent3_launch.sh status
```

### Create a Development Branch

```bash
git checkout -b feature/your-feature-name
```

## Making Changes

### Directory Structure

When adding new features, maintain the existing structure:

```
agent3/
├── playbooks/        # Automation scripts (Ansible/Shell)
├── containers/       # Docker configurations
├── templates/        # Environment templates
└── scripts/          # Utility scripts
```

### Adding a New Template

1. Create template file in `agent3/templates/`
2. Follow existing naming convention: `<language>-dev.env`
3. Include standard sections:
   - Project configuration
   - Environment variables
   - Tool settings
   - Echo status message

Example:
```bash
# Template: agent3/templates/node-dev.env
export PROJECT_NAME="node-project"
export NODE_VERSION="20"
export PATH="$HOME/.nvm/versions/node/v$NODE_VERSION/bin:$PATH"
echo "Node.js Development Environment activated"
echo "  Node: $NODE_VERSION"
```

4. Document in `agent3/templates/README.md`

### Adding a New Container

1. Create Dockerfile in `agent3/containers/`
2. Follow naming: `<purpose>-<arch>.Dockerfile`
3. Include:
   - Clear comments
   - Non-root user
   - Entrypoint script
   - Health check (if applicable)

4. Add to `docker-compose.yml` if multi-service

5. Create management scripts:
   - `agent3/playbooks/<purpose>.sh`
   - `agent3/playbooks/<purpose>.yml` (optional Ansible)

6. Document in `agent3/containers/README.md`

### Modifying Launch Script

When modifying `agent3_launch.sh`:

1. Maintain backward compatibility
2. Add new commands to help text
3. Export functions for testing
4. Use logging functions (log_info, log_error, etc.)
5. Update README.md

## Testing

### Manual Testing

```bash
# Test VS Code setup
./agent3_launch.sh vscode --port 8443
curl http://localhost:8443

# Test JAX container
./agent3_launch.sh jax
docker ps | grep jax-dev-environment
docker exec -it jax-dev-environment python -c "import jax; print(jax.__version__)"

# Test templates
source agent3/templates/python-ml.env
echo $JAX_PLATFORM_NAME

# Test status command
./agent3_launch.sh status
```

### Container Testing

```bash
# Build and test container
cd agent3/containers
docker build -f jax-arm64.Dockerfile -t agent3/jax-arm64:test .

# Run tests in container
docker run --rm agent3/jax-arm64:test python -c "
import jax
import numpy as np
print('JAX version:', jax.__version__)
print('Devices:', jax.devices())
"

# Cleanup
docker rmi agent3/jax-arm64:test
```

### Script Testing

```bash
# Test shell scripts
bash -n agent3_launch.sh  # Syntax check
shellcheck agent3_launch.sh  # Linting (if available)

# Test with different options
./agent3_launch.sh vscode --port 9000
./agent3_launch.sh jax --gpus none
./agent3_launch.sh all --ansible
```

## Submitting Changes

### Before Submitting

1. **Test your changes** thoroughly
2. **Update documentation** if needed
3. **Follow style guidelines** (see below)
4. **Write clear commit messages**

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**
```
feat: Add Node.js development template

- Create node-dev.env template with NVM support
- Add npm and yarn configuration
- Include testing and linting tools
- Update templates README with Node.js section

Closes #123
```

### Pull Request Process

1. **Update your branch**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request**
   - Go to GitHub repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in PR template

4. **PR Description should include:**
   - What changes were made
   - Why changes were needed
   - How to test the changes
   - Any breaking changes
   - Related issues

5. **Wait for review**
   - Address reviewer comments
   - Make requested changes
   - Push updates to same branch

## Style Guidelines

### Shell Scripts

```bash
# Use bash shebang
#!/bin/bash

# Set strict mode
set -e  # Exit on error

# Use meaningful variable names
VSCODE_PORT="${VSCODE_PORT:-8443}"

# Use functions for reusability
start_service() {
    local service_name="$1"
    echo "Starting $service_name..."
}

# Comment complex sections
# This function checks if Docker is running
# and returns 0 if available, 1 otherwise
check_docker() {
    command -v docker &> /dev/null
}

# Use consistent indentation (4 spaces)
if [ condition ]; then
    do_something
fi
```

### Dockerfile

```dockerfile
# Use official base images
FROM arm64v8/ubuntu:22.04

# Set labels
LABEL maintainer="Agent3"
LABEL description="Purpose of this image"

# Group related commands
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*

# Use specific versions
ENV PYTHON_VERSION=3.11

# Create non-root user
RUN useradd -m -s /bin/bash username

# Use COPY instead of ADD (unless extracting)
COPY file /destination

# Document exposed ports
EXPOSE 8888

# Use exec form for ENTRYPOINT/CMD
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

### Ansible Playbooks

```yaml
---
# Descriptive comment
- name: Task description
  hosts: localhost
  vars:
    variable_name: value

  tasks:
    - name: Clear task description
      module:
        parameter: value
      when: condition
```

### Documentation

- Use Markdown for all documentation
- Include code examples
- Keep lines under 100 characters
- Use tables for comparisons
- Add links to related documents

### Environment Templates

```bash
# Template: language-purpose.env
# Brief description

# Project settings
export PROJECT_NAME="project-name"
export VERSION="1.0"

# Paths
export TOOL_HOME="$HOME/.tool"
export PATH="$TOOL_HOME/bin:$PATH"

# Configuration
export CONFIG_VAR="value"

# Status message
echo "Template activated"
echo "  Variable: $VALUE"
```

## Getting Help

- Open an issue for bugs
- Start a discussion for questions
- Check existing documentation
- Review closed issues for similar problems

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing! 🚀
