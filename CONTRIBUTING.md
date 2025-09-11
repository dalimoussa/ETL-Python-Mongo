# Contributing to MongoDB ETL

Thank you for your interest in contributing to the MongoDB ETL project! This document provides guidelines and instructions for contributing.

## Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mongodb-etl.git
   cd mongodb-etl
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Guidelines

### Code Style

We follow PEP 8 style guide for Python code. Key highlights:
- Use 4 spaces for indentation
- Maximum line length of 79 characters
- Use docstrings for functions and classes

You can run the linter with:
```bash
flake8 mongodb_etl
```

### Testing

All new features should include tests. We use pytest for testing:
```bash
pytest tests/
```

For coverage reports:
```bash
pytest --cov=mongodb_etl tests/
```

### Pull Request Process

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit with clear messages:
   ```bash
   git commit -m "Add feature: brief description"
   ```

3. Push your branch and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Ensure all tests pass before requesting a review.

### Documentation

- Update README.md if necessary
- Add/update docstrings for new functions and classes
- Include examples in the examples directory for new features

## Feature Requests & Bug Reports

For feature requests or bug reports, please:
1. Check existing issues to avoid duplicates
2. Create a new issue with a clear description
3. Include steps to reproduce for bugs
4. Tag appropriately (enhancement, bug, etc.)

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.
