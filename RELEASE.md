# Release Checklist

This document outlines the process for releasing a new version of dialtor to PyPI.

## Pre-Release Checklist

### 1. Code Quality
- [ ] All tests pass: `poetry run pytest -v`
- [ ] Test coverage >80%: `poetry run pytest --cov=dialtor --cov-report=term`
- [ ] Type checking passes: `poetry run mypy dialtor`
- [ ] Linting passes: `poetry run ruff check dialtor`
- [ ] Code formatting: `poetry run black --check dialtor`
- [ ] No security vulnerabilities: `poetry audit` or `safety check`

### 2. Documentation
- [ ] README.md is up to date
- [ ] CHANGELOG.md updated with new version
- [ ] API.md reflects current API
- [ ] Man pages updated if commands changed
- [ ] Example scripts tested and working
- [ ] All command help text accurate

### 3. Version Management
- [ ] Update version in `pyproject.toml`
- [ ] Update version in man pages (`docs/man/dialtor.1`)
- [ ] Update CHANGELOG.md with release date
- [ ] Create version tag: `git tag -a v0.1.0 -m "Release v0.1.0"`

### 4. Dependencies
- [ ] All dependencies have version constraints
- [ ] Development dependencies separated from production
- [ ] No unnecessary dependencies
- [ ] Compatible with declared Python versions (3.10+)

### 5. Package Metadata
- [ ] pyproject.toml has complete metadata:
  - [ ] Name, version, description
  - [ ] Authors and maintainers
  - [ ] License (MIT)
  - [ ] Homepage, repository, documentation URLs
  - [ ] Keywords
  - [ ] Classifiers
  - [ ] Include/exclude files configured
- [ ] LICENSE file present
- [ ] README.md exists and renders on PyPI

## Build and Test

### 1. Clean Build Environment
```bash
# Remove old build artifacts
rm -rf dist/ build/ *.egg-info

# Ensure clean working directory
git status  # Should be clean
```

### 2. Build Package
```bash
# Build source distribution and wheel
poetry build

# Verify build artifacts
ls -lh dist/
```

Expected output:
- `dialtor-0.1.0.tar.gz` (source distribution)
- `dialtor-0.1.0-py3-none-any.whl` (wheel)

### 3. Inspect Package Contents
```bash
# Extract and inspect the wheel
unzip -l dist/dialtor-0.1.0-py3-none-any.whl

# Verify all necessary files included:
# - dialtor/ (package code)
# - docs/ (documentation)
# - LICENSE
# - README.md
```

### 4. Test Installation Locally
```bash
# Create test virtualenv
python -m venv test_venv
source test_venv/bin/activate  # On Windows: test_venv\Scripts\activate

# Install from wheel
pip install dist/dialtor-0.1.0-py3-none-any.whl

# Test basic commands
dialtor --help
dialtor --version
dialtor connect verify

# Deactivate and remove test env
deactivate
rm -rf test_venv
```

### 5. Test on TestPyPI (Optional but Recommended)

Upload to TestPyPI first:
```bash
# Install twine if not present
poetry run pip install twine

# Upload to TestPyPI
poetry run twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ dialtor
```

## Publishing to PyPI

### 1. Configure PyPI Token

**Option A: Using Poetry**
```bash
poetry config pypi-token.pypi <your-token>
```

**Option B: Using .pypirc**
Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = <your-token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <your-testpypi-token>
```

Secure the file:
```bash
chmod 600 ~/.pypirc
```

### 2. Upload to PyPI

**Using Poetry:**
```bash
poetry publish
```

**Using Twine:**
```bash
poetry run twine upload dist/*
```

### 3. Verify Publication
- Visit: https://pypi.org/project/dialtor/
- Check metadata, description, links
- Verify README renders correctly
- Test installation: `pip install dialtor`

## Post-Release

### 1. Git Tag and Push
```bash
# Create annotated tag
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push tag to GitHub
git push origin v0.1.0

# Push any remaining commits
git push origin main
```

### 2. GitHub Release
1. Go to: https://github.com/jacoinnz/dialtor/releases/new
2. Select tag: `v0.1.0`
3. Title: `v0.1.0 - Release Name`
4. Description: Copy relevant section from CHANGELOG.md
5. Attach build artifacts (optional):
   - `dialtor-0.1.0.tar.gz`
   - `dialtor-0.1.0-py3-none-any.whl`
6. Publish release

### 3. Announcement
- [ ] Update repository README badges if needed
- [ ] Announce on relevant forums/communities (if appropriate)
- [ ] Update documentation website (if exists)
- [ ] Social media announcement (if applicable)

### 4. Prepare for Next Development Cycle
```bash
# Bump version to next development version
# In pyproject.toml: 0.1.0 -> 0.2.0-dev

# Add [Unreleased] section to CHANGELOG.md
```

## Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):

### Version Format: MAJOR.MINOR.PATCH

- **MAJOR** (0.x.x → 1.0.0): Breaking changes, incompatible API changes
- **MINOR** (0.1.x → 0.2.0): New features, backwards-compatible
- **PATCH** (0.1.0 → 0.1.1): Bug fixes, backwards-compatible

### Pre-Release Versions
- **Alpha**: `0.2.0-alpha.1` - Early development, unstable
- **Beta**: `0.2.0-beta.1` - Feature complete, testing
- **RC**: `0.2.0-rc.1` - Release candidate, final testing

## Rollback Procedure

If a release has critical issues:

### 1. Yank the Release on PyPI
```bash
# Using twine
poetry run twine upload --skip-existing --repository pypi dist/*
# Then manually yank on PyPI web interface
```

### 2. Fix and Re-Release
- Fix the issue in code
- Increment PATCH version (e.g., 0.1.0 → 0.1.1)
- Follow full release process
- Document issue in CHANGELOG.md

## Common Issues

### Build Fails
- Ensure `poetry.lock` is up to date: `poetry lock`
- Clear cache: `poetry cache clear . --all`
- Verify Python version matches constraints

### Upload Fails
- Check PyPI token is correct and has necessary permissions
- Ensure version doesn't already exist on PyPI
- Verify network connection

### Installation Fails
- Check dependency version conflicts
- Ensure wheels are compatible with target platforms
- Verify README.md doesn't have syntax errors (affects PyPI rendering)

## Security Considerations

- **Never commit PyPI tokens** to version control
- **Use PyPI trusted publishers** when available (GitHub Actions)
- **Sign releases** with GPG if possible
- **Scan for vulnerabilities** before release
- **Review all dependencies** for security issues

## Automation (Future)

Consider GitHub Actions workflow for:
- Automated testing on push
- Automatic PyPI publish on tag creation
- Changelog generation
- GitHub Release creation
- Documentation deployment

Example workflow trigger:
```yaml
on:
  push:
    tags:
      - 'v*'
```

## Resources

- [Poetry Publishing Docs](https://python-poetry.org/docs/libraries/#publishing-to-pypi)
- [PyPI Help](https://pypi.org/help/)
- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
