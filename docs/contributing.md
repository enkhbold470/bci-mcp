# Contributing to BCI-MCP

Thank you for your interest in contributing to the Brain-Computer Interface Model Context Protocol (BCI-MCP) project! This document outlines the process for contributing to the project and provides guidelines to help make the contribution process smooth for everyone.

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

If you find a bug in the codebase, please submit an issue using the bug report template. Before creating a bug report, please check that it hasn't already been reported. In your report, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior and actual behavior
- Any relevant logs or error messages
- Environment details (OS, Python version, etc.)

### Suggesting Enhancements

We welcome suggestions for new features or improvements. Please submit an issue using the feature request template, including:

- A clear description of the enhancement
- The motivation behind it
- Any alternatives you've considered
- If applicable, a sketch or mockup of the enhancement

### Pull Requests

We actively welcome pull requests:

1. Fork the repository and create a branch from `main`
2. If you've added code, add tests that cover your changes
3. Ensure your code passes all tests
4. Update any relevant documentation
5. Submit a pull request

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/enkhbold470/bci-mcp.git
   cd bci-mcp
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Coding Guidelines

### Python Style Guide

We follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. Some key points:

- Use 4 spaces for indentation (not tabs)
- Use snake_case for variable and function names
- Use CamelCase for class names
- Maximum line length of 88 characters (following Black formatting)
- Add docstrings for all functions, classes, and modules

### Documentation

- Use [Google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for Python code
- Update the documentation when adding or modifying features
- For the MkDocs site, follow the existing format and structure

### Testing

- Write unit tests for all new functionality
- Make sure all tests pass before submitting a pull request
- Aim for high test coverage of your code

Run tests with:
```bash
pytest
```

## Git Workflow

1. Create a new branch for each feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
   ```

2. Make frequent, small commits with clear messages:
   ```bash
   git commit -m "Add clear description of the changes made"
   ```

3. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a pull request to the `main` branch of the original repository

## Release Process

The project follows [Semantic Versioning](https://semver.org/):

- MAJOR version for incompatible API changes
- MINOR version for backward-compatible functionality additions
- PATCH version for backward-compatible bug fixes

## Communication

- Submit issues for bug reports and feature requests
- Join the discussion in the issue tracker
- Contact the maintainers directly for security issues or CoC violations

## Attribution

This contribution guide is adapted from the [Atom Contributing Guide](https://github.com/atom/atom/blob/master/CONTRIBUTING.md) and the [Contributor Covenant](https://www.contributor-covenant.org/).

Thank you for contributing to BCI-MCP! 