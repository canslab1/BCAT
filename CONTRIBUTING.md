# Contributing to BCAT

Thank you for your interest in contributing to BCAT! This document provides guidelines for contributing to this project.

## How to Contribute

## Reporting Issues

If you encounter bugs or unexpected behavior, please use the [GitHub Issues](https://github.com/canslab1/BCAT/issues) page. When reporting a bug, please include:
1. A clear description of the problem
2. Steps to reproduce
3. Parameter settings used
4. Python version and OS information

## Suggesting Enhancements

Feature requests and suggestions are welcome via GitHub issues. Please describe:
1. The proposed enhancement
2. The motivation or use case
3. Any relevant references

## Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Ensure the code runs without errors
5. Submit a pull request with a clear description

## Development Setup

```bash
git clone https://github.com/canslab1/BCAT.git
cd BCAT
pip install -r requirements.txt
python3 BCAT.py  # Verify the GUI launches correctly
```

### Code Style

- Follow PEP 8 conventions for Python code
- Use type hints where practical.
- Include comments in both English and Traditional Chinese where appropriate (consistent with the existing codebase)
- Document any new parameters or functions

## Project Architecture

| Module | Responsibility |
|--------|---------------|
| `BCAT.py` | Main application with Tkinter GUI and simulation engine |
| `English - best game no one played.nlogo` | NetLogo reference implementation |
| `test_scenarios/` | Parameter configuration files for paper reproduction |

## Questions

For questions about the model or its implementation, please contact the corresponding author:

- **Sheng-Wen Wang** -- swwang@nkust.edu.tw
