# Flox Environment Composition & Containerization

## Layering vs Composition - Environment Design Guide

| Aspect     | Layering                          | Composition                     |
|------------|-----------------------------------|---------------------------------|
| When       | Runtime (activate order matters) | Build time (deterministic)     |
| Conflicts  | Surface at runtime                | Surface at build time          |
| Flexibility| High                              | Predefined structure           |
| Use case   | Ad hoc tools/services            | Repeatable, shareable stacks   |
| Isolation  | Preserves subshell boundaries    | Merges into single manifest    |

### Creating Layer-Optimized Environments
**Design for runtime stacking with potential conflicts:**
```toml
[vars]
# Prefix vars to avoid masking
MYAPP_PORT = "8080"
MYAPP_HOST = "localhost"

[profile.common]
# Use unique, prefixed function names
myapp_setup() { ... }
myapp_debug() { ... }

[services.myapp-db]  # Prefix service names
command = "..."
```
**Best practices:**
- Single responsibility per environment
- Expect vars/binaries might be overridden by upper layers
- Document what the environment provides/expects
- Keep hooks fast and idempotent

### Creating Composition-Optimized Environments
**Design for clean merging at build time:**
```toml
[install]
# Use pkg-groups to prevent conflicts
gcc.pkg-path = "gcc"
gcc.pkg-group = "compiler"

[vars]
# Never duplicate var names across composed envs
POSTGRES_PORT = "5432"  # Not "PORT"

[hook]
# Check if setup already done (idempotent)
setup_postgres() {
  [ -d "$FLOX_ENV_CACHE/postgres" ] || init_db
}
```
**Best practices:**
- No overlapping vars, services, or function names
- Use explicit, namespaced naming (e.g., `postgres_init` not `init`)
- Minimal hook logic (composed envs run ALL hooks)
- Avoid auto-run logic in `[profile]` (runs once per layer/composition; help displays will repeat)
- Test composability: `flox activate` each env standalone first

**Composition example:**
```toml
[include]
environments = [
    { remote = "team/cuda-base" },
    { remote = "team/cuda-math" },
    { remote = "team/python-ml" }
]
```

### Creating Dual-Purpose Environments
**Design for both patterns:**
```toml
[install]
# Clear package groups
python.pkg-path = "python311"
python.pkg-group = "runtime"

[vars]
# Namespace everything
MYPROJECT_VERSION = "1.0"
MYPROJECT_CONFIG = "$FLOX_ENV_CACHE/config"

[profile.common]
# Defensive function definitions
if ! type myproject_init >/dev/null 2>&1; then
  myproject_init() { ... }
fi
```

### Usage Examples
- **Layer**: `flox activate -r team/postgres -- flox activate -r team/debug`
- **Compose**: `[include] environments = [{ remote = "team/postgres" }]`
- **Both**: Compose base, layer tools on top

## Containerization

### Basic Usage
```bash
# Export to file
flox containerize -f ./mycontainer.tar
docker load -i ./mycontainer.tar

# Export directly to runtime (auto-detects docker/podman)
flox containerize --runtime docker

# Pipe to stdout
flox containerize -f - | docker load

# Tag container
flox containerize --tag v1.0 -f - | docker load
```

### How Containers Behave
**Containers activate the Flox environment on startup** (like `flox activate`):
- **Interactive**: `docker run -it <image>` → Bash shell with environment activated
- **Non-interactive**: `docker run <image> <cmd>` → Runs command with environment activated (like `flox activate -- <cmd>`)
- All packages, variables, and hooks are available inside the container

### Command Options
```bash
flox containerize
  [-f <file>]           # Output file (- for stdout); defaults to {name}-container.tar
  [--runtime <runtime>] # docker/podman (auto-detects if not specified)
  [--tag <tag>]         # Container tag (e.g., v1.0, latest)
  [-d <path>]           # Path to .flox/ directory
  [-r <owner/name>]     # Remote environment from FloxHub
```

### Manifest Configuration
Configure container in `[containerize.config]` (experimental):

```toml
[containerize.config]
user = "appuser"                    # Username or uid:gid format
exposed-ports = ["8080/tcp"]        # Ports to expose (tcp/udp/default:tcp)
cmd = ["python", "app.py"]          # Command to run (receives activated env)
volumes = ["/data", "/config"]      # Mount points for persistent data
working-dir = "/app"                # Working directory
labels = { version = "1.0" }        # Arbitrary metadata
stop-signal = "SIGTERM"             # Signal to stop container
```

**Note**: Flox sets an entrypoint that activates the environment, then runs `cmd` inside that activation.

### Complete Workflow Example
```bash
# Create environment
flox init
flox install python311 flask

# Configure for container
cat >> .flox/env/manifest.toml << 'EOF'
[containerize.config]
exposed-ports = ["5000/tcp"]
cmd = ["python", "-m", "flask", "run", "--host=0.0.0.0"]
working-dir = "/app"
EOF

# Build and run
flox containerize -f - | docker load
docker run -p 5000:5000 -v $(pwd):/app <container-id>
```

### Platform-Specific Notes
**macOS**:
- Requires docker/podman runtime (uses proxy container for builds)
- May prompt for file sharing permissions
- Creates `flox-nix` volume for caching (safe to remove when not building: `docker volume rm flox-nix`)

**Linux**: Direct image creation without proxy

### Common Patterns

**Service containers**:
```toml
[services.web]
command = "python -m http.server 8000"

[containerize.config]
exposed-ports = ["8000/tcp"]
cmd = []  # Service starts automatically
```

**Multi-stage pattern** (build in one env, run in another):
```bash
# Build environment with all dev tools
flox activate -d ./build-env -- flox build myapp

# Runtime environment with minimal deps
cd ./runtime-env
flox install myapp
flox containerize --tag production
```

**Remote environment containers**:
```bash
# Containerize shared team environment
flox containerize -r team/python-ml --tag latest
```
