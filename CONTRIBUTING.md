# Contributing to Opinometer

Thank you for your interest in contributing to Opinometer! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment**:
   ```bash
   # Install Python 3.10+ and uv
   # uv handles Python versions and dependencies automatically
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Development Process

### Project Structure

- `planning/` - Project planning and analysis documents
- `database/` - Database schema and migrations
- `docs/` - Documentation (when implemented)
- `src/` - Source code (when implemented)
- `tests/` - Test suite (when implemented)

### Planning-First Development

This project follows a planning-first approach:

1. **Document first** - All major features start with planning documents
2. **Review plans** - Discuss architectural decisions before implementation
3. **Iterate** - Update plans based on learnings during implementation

### Code Standards (Future)

When implementation begins, we'll follow:

- **Python 3.10+** with modern type hints
- **Code formatting** with Black and Ruff
- **Type checking** with mypy
- **Testing** with pytest
- **Documentation** with clear docstrings

## Contributing Guidelines

### 1. Issues

- **Search existing issues** before creating new ones
- **Use issue templates** when available
- **Provide context** - include relevant details about your environment
- **Be specific** - describe expected vs actual behavior

### 2. Pull Requests

- **One feature per PR** - keep changes focused and reviewable
- **Update documentation** - include relevant updates to planning docs
- **Add tests** - ensure your changes are well-tested (when test framework exists)
- **Follow commit conventions**:
  ```
  feat: add sentiment analysis for comments
  fix: handle API rate limiting properly
  docs: update installation instructions
  ```

### 3. Planning Documents

- **Use descriptive filenames** with ISO dates: `2025-09-25-feature-name.md`
- **Include rationale** - explain why decisions were made
- **Consider alternatives** - document what was considered but not chosen
- **Keep it readable** - planning docs should be accessible to all contributors

### 4. Code Review Process

1. **Automated checks** must pass (when implemented)
2. **Peer review** - at least one maintainer review required
3. **Testing** - verify changes work as expected
4. **Documentation** - ensure docs are updated accordingly

## Development Setup (Future)

When the codebase is implemented:

```bash
# Clone the repository
git clone https://github.com/joernpreuss/opinometer.git
cd opinometer

# Initialize uv project (handles venv and dependencies automatically)
uv init
uv add --dev pytest ruff black mypy

# Run tests
uv run pytest

# Run linting
uv run ruff check src/ tests/
uv run black --check src/ tests/
```

## Current Development Status

🚧 **Planning Phase** - We're currently in the planning phase. The best way to contribute right now is:

- **Review planning documents** in `planning/`
- **Suggest improvements** to the architecture
- **Identify potential issues** early in the design phase
- **Contribute to documentation** and project structure

## Questions or Need Help?

- **Open an issue** for questions about the project
- **Check planning documents** for context on architectural decisions
- **Review existing discussions** in issues and pull requests

## Code of Conduct

- **Be respectful** and constructive in all interactions
- **Focus on the technical merits** of ideas and code
- **Help others learn** - explain your reasoning and be patient with questions
- **Assume positive intent** - give others the benefit of the doubt

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Documentation acknowledgments

---

**Note**: This project is in early development. These guidelines will evolve as the project matures. Feel free to suggest improvements to this document as well!