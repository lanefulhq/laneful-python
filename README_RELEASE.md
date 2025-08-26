# Release Process for Laneful Python

This document describes the automated release process for the Laneful Python client library.

## 🔄 **Automatic Releases (TestPyPI)**

Every push to `main` automatically:
1. ✅ Runs full test suite
2. 🏗️ Builds package 
3. 📦 Publishes to [TestPyPI](https://test.pypi.org/project/laneful-python/)

### Testing from TestPyPI
```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
           --extra-index-url https://pypi.org/simple/ \
           laneful-python

# Test the package
python -c "import laneful; print(laneful.__version__)"
```

## 🚀 **Production Releases (PyPI)**

Production releases to PyPI are **manual** and **tag-driven**:

### Option 1: Using the Release Script (Recommended)
```bash
# Make sure you're on main with latest changes
git checkout main
git pull origin main

# Run the release script
./scripts/release.sh 1.0.0
```

The script will:
- ✅ Validate version format
- ✅ Check you're on main branch
- ✅ Check for uncommitted changes
- 📝 Update version in `pyproject.toml`
- 💾 Commit the version change
- 🏷️ Create and push git tag
- 🚀 Trigger automated PyPI release

### Option 2: Manual Release
```bash
# 1. Update version to release version
python scripts/bump_version.py --release 1.0.0

# 2. Commit the change
git add pyproject.toml
git commit -m "Release v1.0.0"

# 3. Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin main
git push origin v1.0.0
```

## 📋 **Version Management**

### Development Versions
```bash
# Set to dev version (for TestPyPI)
python scripts/bump_version.py --dev
# Creates: 1.0.0.dev123 (where 123 is git commit count)
```

### Release Versions  
```bash
# Set to release version (for PyPI)
python scripts/bump_version.py --release 1.0.0
# Creates: 1.0.0
```

### Check Current Version
```bash
python scripts/bump_version.py --show
```

## 🎯 **Release Triggers**

| Trigger | Destination | Version Type | Automatic |
|---------|-------------|--------------|-----------|
| Push to `main` | TestPyPI | `x.y.z.devN` | ✅ Yes |
| Create tag `v*.*.*` | PyPI | `x.y.z` | ✅ Yes |
| Manual dispatch | Either | Any | 🔧 Manual |

## 🔍 **Monitoring Releases**

### GitHub Actions
- [CI Workflow](../../actions/workflows/ci.yml) - Tests and quality checks
- [Release Workflow](../../actions/workflows/release.yml) - Publishing
- [Test Release](../../actions/workflows/test-release.yml) - Release testing

### Package Repositories
- **TestPyPI**: https://test.pypi.org/project/laneful-python/
- **PyPI**: https://pypi.org/project/laneful-python/

### GitHub Releases
- Automatically created for each PyPI release
- Includes changelog and installation instructions
- Available at: https://github.com/owner/repo/releases

## 🛡️ **Security & Trust**

- **Trusted Publishing**: No API tokens needed, uses OIDC
- **Environment Protection**: PyPI releases require manual approval (optional)
- **Artifact Verification**: SHA256 hashes published with each release

## 🧪 **Testing Releases**

### Before Release
```bash
# Test local build
uv build
pip install dist/*.whl

# Test version script
python scripts/bump_version.py --show

# Run test release workflow
# (manually trigger in GitHub Actions)
```

### After TestPyPI Release
```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
           --extra-index-url https://pypi.org/simple/ \
           laneful-python

# Run installation check
python examples/check_installation.py
```

### After PyPI Release
```bash
# Install from PyPI
pip install laneful-python

# Verify version
python -c "import laneful; print(laneful.__version__)"
```

## 🚨 **Troubleshooting**

### Failed Release
1. Check [GitHub Actions](../../actions) for error details
2. Verify version format: `x.y.z` for releases, `x.y.z.devN` for dev
3. Ensure tag format: `vx.y.z` (with 'v' prefix)

### Version Conflicts
```bash
# Reset to dev version
python scripts/bump_version.py --dev

# Or set specific version
python scripts/bump_version.py --release 1.0.1
```

### TestPyPI Issues
- TestPyPI packages are automatically deleted after some time
- Use `--extra-index-url https://pypi.org/simple/` for dependencies

## 📚 **References**

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [TestPyPI Documentation](https://test.pypi.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
