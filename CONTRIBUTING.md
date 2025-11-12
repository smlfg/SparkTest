# Contributing to DGX Spark Playbooks

Thank you for your interest in contributing to DGX Spark Playbooks! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions with the community.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/dgx-spark-playbooks.git
   cd dgx-spark-playbooks
   ```
3. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites
- Docker with GPU support (NVIDIA Container Toolkit)
- Python 3.10+
- NVIDIA GPU with CUDA 12.0+ (for GPU-dependent features)

### Installation
```bash
# Install dependencies
make install

# Or manually
pip install -r requirements.txt
```

## Making Changes

### Code Style
We follow PEP 8 guidelines with some modifications:
- Maximum line length: 100 characters
- Use black for code formatting
- Use isort for import sorting

Format your code before committing:
```bash
make format
```

### Code Quality Checks
Run all quality checks:
```bash
make qa
```

Or run individual checks:
```bash
make lint        # Linting with flake8
make type-check  # Type checking with mypy
```

### Testing

#### Write Tests
- Add unit tests for new functionality in `tests/unit/`
- Add integration tests in `tests/integration/`
- Ensure test coverage remains above 80%

#### Run Tests
```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# With coverage
make test-coverage
```

### Commit Guidelines

#### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

#### Examples
```bash
feat(agent1): add GPU memory monitoring

Implement GPU memory usage tracking in the infrastructure agent.
Adds new endpoint /gpu/memory to report current GPU memory usage.

Closes #123
```

```bash
fix(health_check): handle connection timeout correctly

Previously, connection timeouts were not properly caught and logged.
Now they are handled gracefully with appropriate error messages.
```

## Adding a New Agent

1. Create agent directory:
   ```bash
   mkdir -p agents/agent11_new_feature/{data,logs}
   ```

2. Create required files:
   - `config.yaml` - Agent configuration
   - `main.py` - Agent implementation
   - `Dockerfile` - Container configuration
   - `README.md` - Agent documentation

3. Follow the template from existing agents (e.g., `agent1_infra/`)

4. Add agent to `docker-compose.yml`

5. Add tests in `tests/integration/`

6. Update main README.md

## Shared Interface Changes

If you need to modify shared interfaces:

1. Update the interface in `shared/`
2. Update all affected agents
3. Update tests
4. Update documentation
5. Ensure backward compatibility or provide migration path

## Pull Request Process

1. Update documentation for any changed functionality
2. Add or update tests as needed
3. Ensure all tests pass: `make test`
4. Ensure code quality checks pass: `make qa`
5. Update CHANGELOG.md (if exists) with your changes
6. Submit a pull request with:
   - Clear title and description
   - Reference to any related issues
   - Screenshots (if applicable)

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] No breaking changes (or documented)
```

## Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, your PR will be merged

## Reporting Issues

### Bug Reports
Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Docker version, GPU model, etc.)
- Relevant logs

### Feature Requests
Include:
- Description of the feature
- Use case and motivation
- Proposed implementation (if any)
- Potential impact on existing functionality

## Development Best Practices

### Docker Best Practices
- Use multi-stage builds when appropriate
- Minimize layer count
- Use .dockerignore to exclude unnecessary files
- Pin base image versions

### Python Best Practices
- Use type hints
- Write docstrings for public functions and classes
- Follow the Zen of Python
- Keep functions small and focused
- Use meaningful variable names

### Testing Best Practices
- Write tests before fixing bugs
- Aim for high test coverage (>80%)
- Use descriptive test names
- Test edge cases and error conditions
- Mock external dependencies

### Documentation Best Practices
- Keep README files up to date
- Document all configuration options
- Provide usage examples
- Include troubleshooting tips
- Use clear and concise language

## Project Structure Conventions

```
agents/agentN_name/
├── config.yaml      # Configuration following shared schema
├── main.py          # Main application entry point
├── Dockerfile       # Container definition
├── README.md        # Agent-specific documentation
├── data/            # Agent data (gitignored)
└── logs/            # Agent logs (gitignored)

shared/
├── base.Dockerfile  # Base image definition
├── config_schema.yaml  # Configuration schema
├── health_check.py  # Health check utilities
└── utils/           # Shared utilities

tests/
├── unit/            # Unit tests
└── integration/     # Integration tests
```

## Getting Help

- Review existing documentation
- Check existing issues and PRs
- Open a new issue with your question
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to DGX Spark Playbooks! 🚀
