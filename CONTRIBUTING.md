# Contributing to SparkTest

Thank you for your interest in contributing to SparkTest! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/yourusername/SparkTest.git
cd SparkTest
```

2. **Install development dependencies**

```bash
pip install -r requirements.test.txt
pip install flake8 black isort mypy
```

3. **Start the development environment**

```bash
./agent10_deploy.sh
```

4. **Verify the setup**

```bash
./run_integration_tests.sh smoke
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical fixes
- `docs/` - Documentation updates
- `test/` - Test improvements
- `refactor/` - Code refactoring

### 2. Make Your Changes

- Write clean, readable code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
./run_integration_tests.sh

# Run specific test types
./run_integration_tests.sh smoke
./run_integration_tests.sh integration

# Run tests for specific agent
./run_integration_tests.sh agent 1
```

### 4. Run Code Quality Checks

```bash
# Format code
black .

# Sort imports
isort .

# Check linting
flake8 .

# Type checking
mypy services/
```

### 5. Commit Your Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat: add new data ingestion capability"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Build/tool changes

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Maximum line length: 120 characters
- Use type hints where possible
- Write docstrings for functions and classes

Example:

```python
def process_data(data: List[Dict[str, Any]],
                 filter_key: str) -> pd.DataFrame:
    """
    Process raw data and return DataFrame.

    Args:
        data: List of data dictionaries
        filter_key: Key to filter on

    Returns:
        Processed DataFrame

    Raises:
        ValueError: If data is empty
    """
    if not data:
        raise ValueError("Data cannot be empty")

    # Implementation here
    return df
```

### Testing Guidelines

1. **Write tests for all new features**

```python
def test_new_feature():
    """Test that new feature works correctly"""
    result = new_feature(input_data)
    assert result == expected_output
```

2. **Use appropriate markers**

```python
@pytest.mark.integration
@pytest.mark.agent1
def test_data_ingestion():
    """Integration test for data ingestion"""
    pass
```

3. **Use fixtures for setup/teardown**

```python
@pytest.fixture
def sample_data():
    """Provide sample data for testing"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### Documentation

1. **Update README.md** for user-facing changes
2. **Update ARCHITECTURE.md** for architectural changes
3. **Add docstrings** to all public functions/classes
4. **Comment complex logic** inline

### Git Commit Best Practices

- Keep commits atomic (one logical change per commit)
- Write descriptive commit messages
- Reference issue numbers: `fix: resolve bug #123`
- Don't commit generated files or secrets

## Testing Requirements

### Before Submitting PR

- [ ] All tests pass: `./run_integration_tests.sh`
- [ ] Code is formatted: `black .`
- [ ] Imports are sorted: `isort .`
- [ ] Linting passes: `flake8 .`
- [ ] Documentation is updated
- [ ] CHANGELOG is updated (if applicable)

### Test Coverage

- Maintain or improve code coverage
- Aim for >90% coverage on new code
- Write tests for edge cases

## Pull Request Process

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
```

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by at least one maintainer
3. **Testing** on staging environment
4. **Approval** from project maintainers

### After Approval

- Maintainers will merge using **squash and merge**
- Branch will be automatically deleted
- Changes will be deployed to staging

## Issue Reporting

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Docker version, etc.)
- Relevant logs or error messages

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if any)
- Alternative solutions considered

## Agent-Specific Guidelines

### Agent 1: Data Ingestion
- Handle various data formats
- Validate input data
- Proper error handling for malformed data

### Agent 2: Data Processing
- Efficient transformations
- Handle null values appropriately
- Memory-efficient operations

### Agent 3-9
Follow similar patterns established in existing agents

### Agent 10: Integration + Testing
- Comprehensive test coverage
- Clear test documentation
- Performance benchmarks for changes

## Performance Considerations

- Use Spark DataFrames efficiently
- Cache DataFrames when reused
- Avoid collecting large datasets to driver
- Use appropriate partitioning
- Profile code for bottlenecks

## Security Guidelines

- Never commit secrets or credentials
- Use environment variables for configuration
- Validate all user inputs
- Follow OWASP security practices
- Report security issues privately

## Documentation Standards

### Code Comments

```python
# Good: Explains why
# Use binary search because dataset is sorted and large

# Bad: Explains what (obvious from code)
# Loop through items
for item in items:
    process(item)
```

### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int = 0) -> bool:
    """
    One-line summary.

    More detailed description if needed.
    Multiple paragraphs are fine.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer

    Example:
        >>> complex_function("test", 5)
        True
    """
    pass
```

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- MAJOR.MINOR.PATCH (e.g., 1.2.3)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Checklist

- [ ] Update version number
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create release tag
- [ ] Deploy to production
- [ ] Announce release

## Getting Help

- **Documentation**: Check README.md and ARCHITECTURE.md
- **Issues**: Search existing issues on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Contact**: Email sparktest@example.com

## Recognition

Contributors will be:
- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Recognized in project documentation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to SparkTest! 🚀
