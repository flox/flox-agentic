---
name: flox-publish
description: Use for publishing user packages to flox for use in Flox environments.  Use for package distribution and sharing of builds defined in a flox environment.
---

# Flox Package Publishing Guide

## Core Commands

```bash
flox publish                    # Publish all packages
flox publish my_package         # Publish single package
flox publish -o myorg package   # Publish to organization
flox publish -o myuser package  # Publish to personal namespace
flox auth login                 # Authenticate before publishing
```

## Publishing to Flox Catalog

### Prerequisites
Before publishing:
- Package defined in `[build]` section or `.flox/pkgs/`
- Environment in Git repo with configured remote
- Clean working tree (no uncommitted changes)
- Current commit pushed to remote
- All build files tracked by Git
- At least one package installed in `[install]`

### Authentication

Run authentication before first publish:
```bash
flox auth login
```

### Publishing Commands

```bash
# Publish single package
flox publish my_package

# Publish all packages
flox publish

# Publish to organization
flox publish -o myorg my_package

# Publish to personal namespace (for testing)
flox publish -o mypersonalhandle my_package
```

### Catalog Types

**Personal catalogs**: Only visible to you (good for testing)
- Published to your personal namespace
- Example: User "alice" publishes "hello" → available as `alice/hello`
- Useful for testing before publishing to organization

**Organization catalogs**: Shared with team members (paid feature)
- Published to organization namespace
- Example: Org "acme" publishes "tool" → available as `acme/tool`
- All organization members can install

### Build Validation

Flox clones your repo to a temp location and performs a clean build to ensure reproducibility. Only packages that build successfully in this clean environment can be published.

This validation ensures:
- All dependencies are declared
- Build is reproducible
- No reliance on local machine state
- Git repository is clean and up-to-date

### After Publishing

- Package available in `flox search`, `flox show`, `flox install`
- Metadata sent to Flox servers
- Package binaries uploaded to Catalog Store
- Install with: `flox install <catalog>/<package>`

Users can then:
```bash
# Search for your package
flox search my_package

# See package details
flox show myorg/my_package

# Install the package
flox install myorg/my_package
```

## Real-world Publishing Workflow

### Fork-based development pattern:
1. Fork upstream repo (e.g., `user/project` from `upstream/project`)
2. Add `.flox/` to fork with build definitions
3. `git push origin master` (or main - check with `git branch`)
4. `flox publish -o username package-name`

### In-house application pattern:
1. Create app repo with `.flox/` directory
2. Define build in `[build.myapp]` section
3. Commit and push to remote
4. `flox publish -o myorg myapp`
5. Team installs with `flox install myorg/myapp`

## Versioning Strategies

### Semantic Versioning

```toml
[build.mytool]
version = "1.2.3"  # Major.Minor.Patch
description = "My awesome tool"
```

### Git-based Versioning

```toml
[build.mytool]
version.command = "git describe --tags"
description = "My awesome tool"
```

### File-based Versioning

```toml
[build.mytool]
version.file = "VERSION.txt"
description = "My awesome tool"
```

### Dynamic Versioning from Source

```toml
[build.rustapp]
version.command = "cargo metadata --no-deps --format-version 1 | jq -r '.packages[0].version'"
```

## Publishing Multiple Variants

You can publish multiple variants of the same project:

```toml
[build.myapp]
command = '''
  cargo build --release
  mkdir -p $out/bin
  cp target/release/myapp $out/bin/
'''
version = "1.0.0"
description = "Production build"
sandbox = "pure"

[build.myapp-debug]
command = '''
  cargo build
  mkdir -p $out/bin
  cp target/debug/myapp $out/bin/myapp-debug
'''
version = "1.0.0"
description = "Debug build with symbols"
sandbox = "off"
```

Both can be published and users can choose which to install.

## Testing Before Publishing

### Local Testing

1. Build the package:
```bash
flox build myapp
```

2. Test the built artifact:
```bash
./result-myapp/bin/myapp --version
```

3. Install locally to test:
```bash
flox install ./result-myapp
```

### Personal Catalog Testing

Publish to your personal namespace first:
```bash
flox publish -o myusername myapp
```

Then test installation:
```bash
flox install myusername/myapp
```

Once validated, republish to organization:
```bash
flox publish -o myorg myapp
```

## Common Gotchas

### Branch names
Many repos use `master` not `main` - check with `git branch`

### Auth required
Run `flox auth login` before first publish

### Clean git state
Commit and push ALL changes before `flox publish`:
```bash
git status  # Check for uncommitted changes
git add .flox/
git commit -m "Add flox build configuration"
git push origin master
```

### runtime-packages
List only what package needs at runtime, not build deps:
```toml
[install]
gcc.pkg-path = "gcc"
make.pkg-path = "make"

[build.myapp]
command = '''make && cp myapp $out/bin/'''
runtime-packages = []  # No runtime deps needed
```

### Git-tracked files only
All files referenced in build must be tracked:
```bash
git add .flox/pkgs/*
git add src/
git commit -m "Add build files"
```

## Publishing Nix Expression Builds

For Nix expression builds in `.flox/pkgs/`:

1. Create the Nix expression:
```bash
mkdir -p .flox/pkgs
cat > .flox/pkgs/hello.nix << 'EOF'
{ hello }:
hello.overrideAttrs (oldAttrs: {
  patches = (oldAttrs.patches or []) ++ [ ./my.patch ];
})
EOF
```

2. Track with Git:
```bash
git add .flox/pkgs/*
git commit -m "Add hello package"
git push
```

3. Publish:
```bash
flox publish hello
```

## Publishing Configuration and Assets

You can publish non-code artifacts:

### Configuration templates

```toml
[build.nginx-config]
command = '''
  mkdir -p $out/etc
  cp nginx.conf $out/etc/
  cp -r conf.d $out/etc/
'''
version = "1.0.0"
description = "Organization Nginx configuration"
```

### Protocol buffers

```toml
[build.api-proto]
command = '''
  mkdir -p $out/share/proto
  cp proto/**/*.proto $out/share/proto/
'''
version = "2.1.0"
description = "API protocol definitions"
```

Teams install and reference via `$FLOX_ENV/etc/` or `$FLOX_ENV/share/`.

## Continuous Integration Publishing

### GitHub Actions Example

```yaml
name: Publish to Flox

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Flox
        run: |
          curl -fsSL https://downloads.flox.dev/by-env/stable/install | bash

      - name: Authenticate
        env:
          FLOX_AUTH_TOKEN: ${{ secrets.FLOX_AUTH_TOKEN }}
        run: flox auth login --token "$FLOX_AUTH_TOKEN"

      - name: Publish package
        run: flox publish -o myorg mypackage
```

### GitLab CI Example

```yaml
publish:
  stage: deploy
  only:
    - tags
  script:
    - curl -fsSL https://downloads.flox.dev/by-env/stable/install | bash
    - flox auth login --token "$FLOX_AUTH_TOKEN"
    - flox publish -o myorg mypackage
```

## Package Metadata Best Practices

### Good Descriptions

```toml
[build.cli]
description = "High-performance log shipper with filtering"  # Good: specific, descriptive

# Avoid:
# description = "My tool"  # Too vague
# description = "CLI"      # Not descriptive enough
```

### Proper Versioning

- Use semantic versioning: MAJOR.MINOR.PATCH
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes

### Runtime Dependencies

Only include what's actually needed at runtime:

```toml
[install]
# Build-time only
gcc.pkg-path = "gcc"
make.pkg-path = "make"
# Runtime dependency
libssl.pkg-path = "openssl"

[build.myapp]
runtime-packages = ["libssl"]  # Only runtime deps
```

## Related Skills

- **flox-builds** - Building packages before publishing
- **flox-environments** - Setting up build environments
- **flox-sharing** - Sharing environments vs publishing packages
