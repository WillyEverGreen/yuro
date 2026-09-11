# Contributing to Yuro

Thank you for your interest in contributing to **Yuro**!

## How to Contribute

1. **Fork the Repository**: Create your own feature branch from `main`.
2. **Setup Environment**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/token-saver.git
   cd token-saver
   pip install -e .
   ```
3. **Make Changes**: Follow clean Python code formatting and preserve existing unit tests.
4. **Run Tests**:
   ```bash
   py -m unittest discover -s tests -t . -p "test_*.py"
   ```
5. **Submit a Pull Request**: Provide a clear explanation of your changes and test verification results.

## Code Guidelines
- Keep function signatures backwards-compatible.
- Ensure all AST structural compression changes enforce the invariant $\text{executable\_ast\_before} == \text{executable\_ast\_after}$.
- Maintain 100% local-first privacy.

Thank you for helping make Yuro even better!
