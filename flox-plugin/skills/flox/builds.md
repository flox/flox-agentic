# Flox Build System Guide

## Build System Overview

Flox supports two build modes, each with its own strengths:

**Manifest builds** enable you to define your build steps in your manifest and reuse your existing build scripts and toolchains. Flox manifests are declarative artifacts, expressed in TOML.

Manifest builds:
- Make it easy to get started, requiring few if any changes to your existing workflows
- Can run inside a sandbox (using `sandbox = "pure"`) for reproducible builds
- Are best for getting going fast with existing projects

**Nix expression builds** guarantee build-time reproducibility because they're both isolated and purely functional. Their learning curve is steeper because they require proficiency with the Nix language.

Nix expression builds:
- Are isolated by default. The Nix sandbox seals the build off from the host system, so no state leak ins
- Are functional. A Nix build is defined as a pure function of its declared inputs

You can mix both approaches in the same project, but package names must be unique.

## Manifest Builds

Flox treats a **manifest build** as a short, deterministic Bash script that runs inside an activated environment and copies its deliverables into `$out`. Anything copied there becomes a first-class, versioned package that can later be published and installed like any other catalog artifact.

### Critical insights from real-world packaging:
- **Build hooks don't run**: `[hook]` scripts DO NOT execute during `flox build` - only during interactive `flox activate`
- **Guard env vars**: Always use `${FLOX_ENV_CACHE:-}` with default fallback in hooks to avoid build failures
- **Wrapper scripts pattern**: Create launcher scripts in `$out/bin/` that set up runtime environment:
  ```bash
  cat > "$out/bin/myapp" << 'EOF'
  #!/usr/bin/env bash
  APP_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
  export PYTHONPATH="$APP_ROOT/share/myapp:$PYTHONPATH"
  exec python3 "$APP_ROOT/share/myapp/main.py" "$@"
  EOF
  chmod +x "$out/bin/myapp"
  ```
- **User config pattern**: Default to `~/.myapp/` for user configs, not `$FLOX_ENV_CACHE` (packages are immutable)
- **Model/data directories**: Create user directories at runtime, not build time:
  ```bash
  mkdir -p "${MYAPP_DIR:-$HOME/.myapp}/models"
  ```
- **Python package strategy**: Don't bundle Python deps - include `requirements.txt` and setup script:
  ```bash
  # In build, create setup script:
  cat > "$out/bin/myapp-setup" << 'EOF'
  venv="${VENV:-$HOME/.myapp/venv}"
  uv venv "$venv" --python python3
  uv pip install --python "$venv/bin/python" -r "$APP_ROOT/share/myapp/requirements.txt"
  EOF
  ```
- **Dual-environment workflow**: Build in `project-build/`, use package in `project/`:
  ```bash
  cd project-build && flox build myapp
  cd ../project && flox install owner/myapp
  ```

### Build Definition Syntax

```toml
[build.<name>]
command      = '''  # required – Bash, multiline string
  <your build steps>                 # e.g. cargo build, npm run build
  mkdir -p $out/bin
  cp path/to/artifact $out/bin/<name>
'''
version      = "1.2.3"               # optional
description  = "one-line summary"    # optional
sandbox      = "pure" | "off"        # default: off
runtime-packages = [ "id1", "id2" ]  # optional
```

**One table per package.** Multiple `[build.*]` tables let you publish, for example, a stripped release binary and a debug build from the same sources.

**Bash only.** The script executes under `set -euo pipefail`. If you need zsh or fish features, invoke them explicitly inside the script.

**Environment parity.** Before your script runs, Flox performs the equivalent of `flox activate` — so every tool listed in `[install]` is on PATH.

**Package groups and builds.** Only packages in the `toplevel` group (default) are available during builds. Packages with explicit `pkg-group` settings won't be accessible in build commands unless also installed to `toplevel`.

**Referencing other builds.** `${other}` expands to the `$out` of `[build.other]` and forces that build to run first, enabling multi-stage flows (e.g. vendoring → compilation).

## Purity and Sandbox Control

| sandbox value | Filesystem scope | Network | Typical use-case |
|---------------|------------------|---------|------------------|
| `"off"` (default) | Project working tree; complete host FS | allowed | Fast, iterative dev builds |
| `"pure"` | Git-tracked files only, copied to tmp | Linux: blocked<br>macOS: allowed | Reproducible, host-agnostic packages |

Pure mode highlights undeclared inputs early and is mandatory for builds intended for CI/CD publication. When a pure build needs pre-fetched artifacts (e.g. language modules) use a two-stage pattern:

```toml
[build.deps]
command  = '''go mod vendor -o $out/etc/vendor'''
sandbox  = "off"

[build.app]
command  = '''
  cp -r ${deps}/etc/vendor ./vendor
  go build ./...
  mkdir -p $out/bin
  cp app $out/bin/
'''
sandbox  = "pure"
```

## $out Layout and Filesystem Hierarchy

Only files placed under `$out` survive. Follow FHS conventions:

| Path | Purpose |
|------|---------|
| `$out/bin` / `$out/sbin` | CLI and daemon binaries (must be `chmod +x`) |
| `$out/lib`, `$out/libexec` | Shared libraries, helper programs |
| `$out/share/man` | Man pages (gzip them) |
| `$out/etc` | Configuration shipped with the package |

Scripts or binaries stored elsewhere will not end up on callers' paths.

## Running Manifest Builds

```bash
# Build every target in the manifest
flox build

# Build a subset
flox build app docs

# Build a manifest in another directory
flox build -d /path/to/project
```

Results appear as immutable symlinks: `./result-<name>` → `/nix/store/...-<name>-<version>`.

To execute a freshly built binary: `./result-app/bin/app`.

## Multi-Stage Examples

### Rust release binary plus source tar

```toml
[build.bin]
command = '''
  cargo build --release
  mkdir -p $out/bin
  cp target/release/myproject $out/bin/
'''
version = "0.9.0"

[build.src]
command = '''
  git archive --format=tar HEAD | gzip > $out/myproject-${bin.version}.tar.gz
'''
sandbox = "pure"
```

`${bin.version}` resolves because both builds share the same manifest.

## Trimming Runtime Dependencies

By default, every package in the `toplevel` install-group becomes a runtime dependency of your build's closure—even if it was only needed at compile time.

Declare a minimal list instead:

```toml
[install]
clang.pkg-path = "clang"
pytest.pkg-path = "pytest"

[build.cli]
command = '''
  make
  mv build/cli $out/bin/
'''
runtime-packages = [ "clang" ]  # exclude pytest from runtime closure
```

Smaller closures copy faster and occupy less disk when installed on users' systems.

## Version and Description Metadata

Flox surfaces these fields in `flox search`, `flox show`, and during publication.

```toml
[build.mytool]
version.command = "git describe --tags"
description = "High-performance log shipper"
```

Alternative forms:

```toml
version = "1.4.2"            # static string
version.file = "VERSION.txt" # read at build time
```

## Cross-Platform Considerations for Manifest Builds

`flox build` targets the host's systems triple. To ship binaries for additional platforms you must trigger the build on machines (or CI runners) of those architectures:

```
linux-x86_64 → build → publish
darwin-aarch64 → build → publish
```

The manifest can remain identical across hosts.

## Beyond Code — Packaging Assets

Any artifact that can be copied into `$out` can be versioned and installed:

### Nginx baseline config

```toml
[build.nginx_cfg]
command = '''mkdir -p $out/etc && cp nginx.conf $out/etc/'''
```

### Organization-wide .proto schema bundle

```toml
[build.proto]
command = '''
  mkdir -p $out/share/proto
  cp proto/**/*.proto $out/share/proto/
'''
```

Teams install these packages and reference them via `$FLOX_ENV/etc/nginx.conf` or `$FLOX_ENV/share/proto`.

## Command Reference

**`flox build [pkgs…]`** Run builds; default = all.

**`-d, --dir <path>`** Build the environment rooted at `<path>/.flox`.

**`-v` / `-vv`** Increase log verbosity.

**`-q`** Quiet mode.

**`--help`** Detailed CLI help.

## Nix Expression Builds

You can write a Nix expression instead of (or in addition to) defining a manifest build.

Put `*.nix` build files in `.flox/pkgs/` for Nix expression builds. Git add all files before building.

### File Naming
- `hello.nix` → package named `hello`
- `hello/default.nix` → package named `hello`

### Common Patterns

**Shell Script**
```nix
{writeShellApplication, curl}:
writeShellApplication {
  name = "my-ip";
  runtimeInputs = [ curl ];
  text = ''curl icanhazip.com'';
}
```

**Your Project**
```nix
{ rustPlatform, lib }:
rustPlatform.buildRustPackage {
  pname = "my-app";
  version = "0.1.0";
  src = ../../.;
  cargoLock.lockFile = "${src}/Cargo.lock";
}
```

**Update Version**
```nix
{ hello, fetchurl }:
hello.overrideAttrs (finalAttrs: _: {
  version = "2.12.2";
  src = fetchurl {
    url = "mirror://gnu/hello/hello-${finalAttrs.version}.tar.gz";
    hash = "sha256-WpqZbcKSzCTc9BHO6H6S9qrluNE72caBm0x6nc4IGKs=";
  };
})
```

**Apply Patches**
```nix
{ hello }:
hello.overrideAttrs (oldAttrs: {
  patches = (oldAttrs.patches or []) ++ [ ./my.patch ];
})
```

### Hash Generation
1. Use `hash = "";`
2. Run `flox build`
3. Copy hash from error message

### Commands
- `flox build` - build all
- `flox build .#hello` - build specific
- `git add .flox/pkgs/*` - track files

## Publishing to Flox Catalog

### Prerequisites
Before publishing:
- Package defined in `[build]` section or `.flox/pkgs/`
- Environment in Git repo with configured remote
- Clean working tree (no uncommitted changes)
- Current commit pushed to remote
- All build files tracked by Git
- At least one package installed in `[install]`

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

### Key Points
- Personal catalogs: Only visible to you (good for testing)
- Organization catalogs: Shared with team members (paid feature)
- Published packages appear as `<catalog>/<package-name>`
- Example: User "alice" publishes "hello" → available as `alice/hello`
- Packages downloadable via `flox install <catalog>/<package>`

### Build Validation
Flox clones your repo to a temp location and performs a clean build to ensure reproducibility. Only packages that build successfully in this clean environment can be published.

### After Publishing
- Package available in `flox search`, `flox show`, `flox install`
- Metadata sent to Flox servers
- Package binaries uploaded to Catalog Store
- Install with: `flox install <catalog>/<package>`

### Real-world Publishing Workflow
**Fork-based development pattern:**
1. Fork upstream repo (e.g., `user/project` from `upstream/project`)
2. Add `.flox/` to fork with build definitions
3. `git push origin master` (or main - check with `git branch`)
4. `flox publish -o username package-name`

**Common gotchas:**
- **Branch names**: Many repos use `master` not `main` - check with `git branch`
- **Auth required**: Run `flox auth login` before first publish
- **Clean git state**: Commit and push ALL changes before `flox publish`
- **runtime-packages**: List only what package needs at runtime, not build deps
