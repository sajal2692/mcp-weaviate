# Release Process for mcp-weaviate

This document outlines the release process for publishing new versions of `mcp-weaviate` to PyPI.

## Prerequisites

Before starting a release:

- [ ] Ensure all tests pass on the `main` branch
- [ ] Review and merge all planned PRs for this release
- [ ] Ensure your local `main` branch is up to date:
  ```bash
  git checkout main
  git pull origin main
  ```

## Release Workflow

We use a semi-automated release process that combines GitHub Actions with manual release creation.

### Step 1: Prepare the Release

Run the **Prepare Release** workflow to automatically bump the version and create a PR:

1. Go to [Actions → Prepare Release](https://github.com/sajal2692/mcp-weaviate/actions/workflows/prepare-release.yml)
2. Click **"Run workflow"**
3. Select the version bump type:
   - `patch`: For bug fixes and minor changes (0.1.0 → 0.1.1)
   - `minor`: For new features, backwards compatible (0.1.0 → 0.2.0)
   - `major`: For breaking changes (0.1.0 → 1.0.0)
4. Click **"Run workflow"** (green button)

This will:
- Calculate the new version number
- Update `pyproject.toml` with the new version
- Create a PR titled "Release: vX.Y.Z"

### Step 2: Review and Merge the Release PR

1. Go to [Pull Requests](https://github.com/sajal2692/mcp-weaviate/pulls)
2. Review the automatically created PR "Release: vX.Y.Z"
3. Verify the version bump is correct in `pyproject.toml`
4. Consider updating the PR description with notable changes
5. Merge the PR into `main`

### Step 3: Create the GitHub Release

After merging the version bump PR:

1. Go to [Releases → New Release](https://github.com/sajal2692/mcp-weaviate/releases/new)
2. **Create the tag**:
   - Click "Choose a tag"
   - Type: `vX.Y.Z` (e.g., `v0.2.0`)
   - Select "Create new tag: vX.Y.Z on publish"
3. **Release details**:
   - **Target**: `main` (default)
   - **Release title**: `vX.Y.Z`
   - **Release notes**: Use the template below
4. Click **"Publish release"**

#### Release Notes Template

```markdown
## What's Changed

* Brief summary of major changes
* List key features or fixes
* Credit contributors if applicable

## Features
- 🎯 Feature 1: Description
- 🔧 Feature 2: Description
- 🐛 Bug fix: Description

## Breaking Changes (if any)
- Description of breaking changes
- Migration instructions

## Installation
\```bash
pip install mcp-weaviate==X.Y.Z
\```

## Full Changelog
**Full Changelog**: https://github.com/sajal2692/mcp-weaviate/compare/vPREVIOUS...vX.Y.Z
```

### Step 4: Monitor the Release

1. Go to the [Actions tab](https://github.com/sajal2692/mcp-weaviate/actions)
2. Watch the **"Publish to PyPI"** workflow that was triggered by the release
3. Ensure it completes successfully (takes ~1-2 minutes)

### Step 5: Verify the Release

Once the workflow completes:

1. **Check PyPI**: https://pypi.org/project/mcp-weaviate/
2. **Verify the new version is available**
3. **Test installation**:
   ```bash
   # Create a test environment
   uv venv test-release
   source test-release/bin/activate  # On Windows: test-release\Scripts\activate

   # Install the new version
   uv pip install mcp-weaviate==X.Y.Z

   # Verify version
   python -c "import importlib.metadata; print(importlib.metadata.version('mcp-weaviate'))"
   ```

## Manual Release Process (Alternative)

If you prefer to release manually without the automation:

1. **Update version in `pyproject.toml`**:
   ```bash
   # Edit pyproject.toml and update the version field
   version = "X.Y.Z"
   ```

2. **Commit and push the change**:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to X.Y.Z"
   git push origin main
   ```

3. **Create and push a tag**:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

4. **Create the GitHub Release** (follow Step 3 above)

## Automated Workflows

### Continuous Integration (CI)

- **Trigger**: Every push to `main` and all PRs
- **Actions**: Runs tests, linting (ruff), type checking (mypy)
- **File**: `.github/workflows/ci.yml`

### Publish to PyPI

- **Trigger**: When a GitHub Release is published
- **Actions**: Builds package and publishes to PyPI
- **File**: `.github/workflows/publish.yml`
- **Requirements**: `PYPI_API_TOKEN` secret must be configured

### Version Check

- **Trigger**: When a GitHub Release is created
- **Actions**: Verifies git tag matches `pyproject.toml` version
- **File**: `.github/workflows/version-check.yml`

### Prepare Release

- **Trigger**: Manual workflow dispatch
- **Actions**: Bumps version and creates release PR
- **File**: `.github/workflows/prepare-release.yml`

## Troubleshooting

### PyPI Publication Failed

1. **Check the error in Actions tab**
2. **Common issues**:
   - **Token error**: Verify `PYPI_API_TOKEN` secret is set correctly
   - **Version exists**: Version already published (can't overwrite)
   - **Build error**: Test locally with `uv build`

### Version Mismatch

If the version check fails:
- Ensure the git tag matches the version in `pyproject.toml`
- Tag format should be `vX.Y.Z` (with the `v` prefix)

### First Release

For the very first release to PyPI:
- Ensure your PyPI API token has "Entire account" scope
- The package name must not already exist on PyPI

## Testing with TestPyPI (Optional)

Before releasing to production PyPI, you can test with TestPyPI:

1. Create a TestPyPI account at https://test.pypi.org/
2. Generate an API token
3. Add it as `TEST_PYPI_API_TOKEN` in GitHub Secrets
4. Run the test publish workflow manually

## Version Numbering Guidelines

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking API changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

### Examples:
- Adding a new tool: Minor bump
- Fixing a bug: Patch bump
- Changing tool parameters: Major bump
- Updating dependencies: Usually patch bump

## Post-Release Tasks

After a successful release:

- [ ] Announce on relevant channels (if applicable)
- [ ] Update documentation if needed
- [ ] Close related issues/milestones
- [ ] Plan next release features

## Quick Reference

```bash
# Update local main
git checkout main && git pull

# After merging release PR, create release on GitHub
# Tag: vX.Y.Z
# Title: vX.Y.Z

# Verify installation works
uv pip install mcp-weaviate==X.Y.Z

# Check PyPI page
open https://pypi.org/project/mcp-weaviate/
```

## Support

If you encounter issues with the release process:
1. Check the [Actions tab](https://github.com/sajal2692/mcp-weaviate/actions) for workflow logs
2. Review this documentation
3. Ensure all secrets are properly configured
4. Test the build locally with `uv build`
