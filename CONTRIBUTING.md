# Contributing to Opinometer

Thank you for your interest in contributing to Opinometer! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment**:
   ```bash
   # Install Python 3.13+ and uv
   # uv handles Python versions and dependencies automatically
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv sync
   ```

## Development Process

### Project Structure

- `planning/` - Project planning and analysis documents
- `src/` - Source code
  - `platforms/` - Platform-specific data collectors (Reddit, HackerNews)
  - `main.py` - Main application
- `results/` - Analysis output (JSON/CSV files)
- `database/` - Database schema and migrations (planned)
- `docs/` - Documentation (planned)
- `tests/` - Test suite (planned)

### Planning-First Development

This project follows a planning-first approach:

1. **Document first** - All major features start with planning documents
2. **Review plans** - Discuss architectural decisions before implementation
3. **Iterate** - Update plans based on learnings during implementation

### Code Standards (Future)

When implementation begins, we'll follow:

- **Python 3.13+** with modern type hints
- **Code formatting** with Ruff
- **Type checking** with mypy
- **Testing** with pytest (planned)
- **Documentation** with clear docstrings
- **httpx** for async HTTP requests (Reddit and HackerNews APIs)
- **No API keys required** - uses public JSON endpoints

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

# Install dependencies
uv sync

# Run the application
uv run src/main.py

# Run tests (when implemented)
uv run pytest

# Run QA checks
uv run ruff format src/ --check --diff
uv run ruff check src/
uv run mypy src/
```

## Current Development Status

✅ **Prototype Phase** - Working multi-source sentiment analysis prototype! The best way to contribute:

- **Test the application** with different search queries
- **Review the codebase** in `src/` for improvements
- **Suggest new platforms** to add to the analysis
- **Contribute to documentation** and expand features

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