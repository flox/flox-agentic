---
name: flox
description: Expert guidance for creating and managing Flox environments. Use this when working with Flox manifests, package installation, services, builds, or environment composition.
---

# Flox Environment Creation Quick Guide

## Quick Navigation Guide - "How do I...?"

### Getting Started
- **Create my first environment** → See below: Flox Basics, Core Commands
- **Find and install packages** → See below: Core Commands, The [install] Section
- **Understand the manifest structure** → See below: Manifest Structure

### Common Development Tasks
- **Set up Python with virtual environments** → See `language-patterns.md`
- **Set up C/C++ development** → See `language-patterns.md`
- **Set up Node.js projects** → See `language-patterns.md`
- **Set up CUDA/GPU development** → See `language-patterns.md`
- **Handle package conflicts** → See below: The [install] Section; also see `troubleshooting.md`

### Services & Background Processes
- **Run a database or web server** → See `services.md`
- **Make services network-accessible** → See `services.md`
- **Debug a failing service** → See `services.md` and `troubleshooting.md`

### Building & Publishing
- **Package my application** → See `builds.md`
- **Create reproducible builds** → See `builds.md`
- **Use Nix expressions** → See `builds.md`
- **Publish to team catalog** → See `builds.md`
- **Package configuration/assets** → See `builds.md`

### Environment Composition
- **Layer multiple environments** → See `composition.md`
- **Compose reusable environments** → See `composition.md`
- **Design environments for both** → See `composition.md`
- **Containerize environments** → See `composition.md`

### Platform-Specific
- **Handle Linux-only packages** → See below: The [install] Section; also see `language-patterns.md`
- **Handle macOS-specific frameworks** → See `language-patterns.md`
- **Support multiple platforms** → See `language-patterns.md`

### Troubleshooting
- **Fix package conflicts** → See `troubleshooting.md`
- **Debug hooks not working** → See `troubleshooting.md`
- **Understand build vs runtime** → See `troubleshooting.md` and `builds.md`
- **Fix service startup issues** → See `services.md` and `troubleshooting.md`

### Advanced Topics
- **Create multi-stage builds** → See `builds.md`
- **Minimize runtime dependencies** → See `builds.md`
- **Edit manifests programmatically** → See below: Editing Manifests Non-Interactively

## Working Style & Structure

- Use **modular, idempotent bash functions** in hooks
- Never, ever use absolute paths. Flox environments are designed to be reproducible. Use Flox's environment variables (see Flox Basics below) instead
- I REPEAT: NEVER, EVER USE ABSOLUTE PATHS. Don't do it. Use `$FLOX_ENV` for environment-specific runtime dependencies; use `$FLOX_ENV_PROJECT` for the project directory. See Flox Basics below
- Name functions descriptively (e.g., `setup_postgres()`)
- Consider using **gum** for styled output when creating environments for interactive use; this is an anti-pattern in CI
- Put persistent data/configs in `$FLOX_ENV_CACHE`
- Return to `$FLOX_ENV_PROJECT` at end of hooks
- Use `mktemp` for temp files, clean up immediately
- Do not over-engineer: e.g., do not create unnecessary echo statements or superfluous comments; do not print unnecessary information displays in `[hook]` or `[profile]`; do not create helper functions or aliases without the user requesting these explicitly

## Configuration & Secrets

- Support `VARIABLE=value flox activate` pattern for runtime overrides
- Never store secrets in manifest; use:
  - Environment variables
  - `~/.config/<env_name>/` for persistent secrets
  - Existing config files (e.g., `~/.aws/credentials`)

## Flox Basics

- Flox is built on Nix; fully Nix-compatible
- Flox uses nixpkgs as its upstream; packages are _usually_ named the same; unlike nixpkgs, Flox Catalog has millions of historical package-version combinations
- Key paths:
  - `.flox/env/manifest.toml`: Environment definition
  - `.flox/env.json`: Environment metadata
  - `$FLOX_ENV_CACHE`: Persistent, local-only storage (survives `flox delete`)
  - `$FLOX_ENV_PROJECT`: Project root directory (where .flox/ lives)
  - `$FLOX_ENV`: basically the path to `/usr`: contains all the libs, includes, bins, configs, etc. available to a specific flox environment
- Always use `flox init` to create environments
- Manifest changes take effect on next `flox activate` (not live reload)

## Core Commands

```bash
flox init                       # Create new env
flox search <string> [--all]    # Search for a package
flox show <pkg>                 # Show available historical versions of a package
flox install <pkg>              # Add package
flox list [-e | -c | -n | -a]   # List installed packages: `-e` = default; `-c` = shows the raw contents of the manifest; `-n` = shows only the install ID of each package; `-a` = shows all available package information including priority and license.
flox activate                   # Enter env
flox activate -s                # Start services
flox activate -- <cmd>          # Run without subshell
flox build <target>             # Build defined target
flox containerize               # Export as OCI image
```

## Manifest Structure

- `[install]`: Package list with descriptors (see detailed section below)
- `[vars]`: Static variables
- `[hook]`: Non-interactive setup scripts
- `[profile]`: Shell-specific functions/aliases
- `[services]`: Service definitions with commands and optional shutdown (see `services.md`)
- `[build]`: Reproducible build commands (see `builds.md`)
- `[include]`: Compose other environments (see `composition.md`)
- `[options]`: Activation mode, supported systems

## The [install] Section

### Package Installation Basics

The `[install]` table specifies packages to install.

```toml
[install]
ripgrep.pkg-path = "ripgrep"
pip.pkg-path = "python310Packages.pip"
```

### Package Descriptors

Each entry has:
- **Key**: Install ID (e.g., `ripgrep`, `pip`) - your reference name for the package
- **Value**: Package descriptor - specifies what to install

### Catalog Descriptors (Most Common)

Options for packages from the Flox catalog:

```toml
[install]
example.pkg-path = "package-name"           # Required: location in catalog
example.pkg-group = "mygroup"               # Optional: group packages together
example.version = "1.2.3"                   # Optional: exact or semver range
example.systems = ["x86_64-linux"]          # Optional: limit to specific platforms
example.priority = 3                        # Optional: resolve file conflicts (lower = higher priority)
```

#### Key Options Explained:

**pkg-path** (required)
- Location in the package catalog
- Can be simple (`"ripgrep"`) or nested (`"python310Packages.pip"`)
- Can use array format: `["python310Packages", "pip"]`

**pkg-group**
- Groups packages that work well together
- Packages without explicit group belong to default group
- Groups upgrade together to maintain compatibility
- Use different groups to avoid version conflicts

**version**
- Exact: `"1.2.3"`
- Semver ranges: `"^1.2"`, `">=2.0"`
- Partial versions act as wildcards: `"1.2"` = latest 1.2.X

**systems**
- Constrains package to specific platforms
- Options: `"x86_64-linux"`, `"x86_64-darwin"`, `"aarch64-linux"`, `"aarch64-darwin"`
- Defaults to manifest's `options.systems` if omitted

**priority**
- Resolves file conflicts between packages
- Default: 5
- Lower number = higher priority wins conflicts
- **Critical for CUDA packages** (see `language-patterns.md`)

### Practical Examples

```toml
# Platform-specific Python
[install]
python.pkg-path = "python311Full"
uv.pkg-path = "uv" # installs uv, modern rust-based successor to uvicorn
systems = ["x86_64-linux", "aarch64-linux"]  # Linux only

# Version-pinned with custom priority
[nodejs]
nodejs.pkg-path = "nodejs"
version = "^20.0"
priority = 1  # Takes precedence in conflicts

# Multiple package groups to avoid conflicts
[install]
gcc.pkg-path = "gcc12"
gcc.pkg-group = "stable"
```

## Best Practices

- Check manifest before installing new packages
- Use `return` not `exit` in hooks
- Define env vars with `${VAR:-default}`
- Use descriptive, prefixed function names in composed envs
- Cache downloads in `$FLOX_ENV_CACHE`
- Log service output to `$FLOX_ENV_CACHE/logs/`
- Test activation with `flox activate -- <command>` before adding to services
- When debugging services, run the exact command from manifest manually first
- Use `--quiet` flag with uv/pip in hooks to reduce noise

## Editing Manifests Non-Interactively

```bash
flox list -c > /tmp/manifest.toml
# Edit with sed/awk
flox edit -f /tmp/manifest.toml
```

## Additional Resources

For detailed information on specific topics, see these additional files:

- **services.md** - Running services, network configuration, logging patterns
- **builds.md** - Build system, manifest builds, Nix expressions, publishing
- **composition.md** - Environment layering, composition, containerization
- **language-patterns.md** - Python, C/C++, Node.js, CUDA development patterns
- **troubleshooting.md** - Common pitfalls, debugging tips, quick tips

---

**Note**: Claude will automatically read these additional files as needed when specific topics are requested.
