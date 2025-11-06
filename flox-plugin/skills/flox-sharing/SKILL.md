---
name: flox-sharing
description: Sharing and composing Flox environments. Use for environment composition, remote environments, FloxHub, and team collaboration patterns.
---

# Flox Environment Sharing & Composition Guide

## Core Concepts

**Composition**: Build-time merging of environments (deterministic)
**Remote Environments**: Shared environments via FloxHub
**Team Collaboration**: Reusable, shareable environment stacks

## Core Commands

```bash
# Activate remote environment
flox activate -r owner/environment-name

# Pull remote environment locally
flox pull owner/environment-name

# Push local environment to FloxHub
flox push

# Compose environments in manifest
# (see [include] section below)
```

## Environment Composition

### Basic Composition

Merge environments at build time using `[include]`:

```toml
[include]
environments = [
    { remote = "team/postgres" },
    { remote = "team/redis" },
    { remote = "team/python-base" }
]
```

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

### Composition Example: Full Stack

```toml
# .flox/env/manifest.toml
[include]
environments = [
    { remote = "team/postgres" },
    { remote = "team/redis" },
    { remote = "team/nodejs" },
    { remote = "team/monitoring" }
]

[vars]
# Override composed environment variables
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5433"  # Non-standard port
```

### Use Cases for Composition

**Reproducible stacks:**
```toml
[include]
environments = [
    { remote = "team/cuda-base" },
    { remote = "team/cuda-math" },
    { remote = "team/python-ml" }
]
```

**Shared base configuration:**
```toml
[include]
environments = [
    { remote = "org/standards" },  # Company-wide settings
    { remote = "team/backend" }    # Team-specific tools
]
```

## Creating Dual-Purpose Environments

**Design for both layering and composition:**

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

## Remote Environments

### Activating Remote Environments

```bash
# Activate remote environment directly
flox activate -r owner/environment-name

# Activate and run a command
flox activate -r owner/environment-name -- npm test
```

### Pulling Remote Environments

```bash
# Pull to work on locally
flox pull owner/environment-name

# Now it's in your local .flox/
flox activate
```

### Pushing Environments to FloxHub

```bash
# Initialize Git repo if needed
git init
git add .flox/
git commit -m "Initial environment"

# Push to FloxHub
flox push

# Others can now activate with:
# flox activate -r yourusername/your-repo
```

## Team Collaboration Patterns

### Base + Specialization

**Create base environment:**
```toml
# team/base
[install]
git.pkg-path = "git"
gh.pkg-path = "gh"
jq.pkg-path = "jq"

[vars]
ORG_REGISTRY = "registry.company.com"
```

**Specialize for teams:**
```toml
# team/frontend
[include]
environments = [{ remote = "team/base" }]

[install]
nodejs.pkg-path = "nodejs"
pnpm.pkg-path = "pnpm"
```

```toml
# team/backend
[include]
environments = [{ remote = "team/base" }]

[install]
python.pkg-path = "python311Full"
uv.pkg-path = "uv"
```

### Service Libraries

**Create reusable service environments:**

```toml
# team/postgres-service
[install]
postgresql.pkg-path = "postgresql"

[services.postgres]
command = '''
  mkdir -p "$FLOX_ENV_CACHE/postgres"
  if [ ! -d "$FLOX_ENV_CACHE/postgres/data" ]; then
    initdb -D "$FLOX_ENV_CACHE/postgres/data"
  fi
  exec postgres -D "$FLOX_ENV_CACHE/postgres/data" \
    -h "$POSTGRES_HOST" -p "$POSTGRES_PORT"
'''
is-daemon = true

[vars]
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
```

**Compose into projects:**
```toml
# my-project
[include]
environments = [
    { remote = "team/postgres-service" },
    { remote = "team/redis-service" }
]
```

### Development vs Production

**Development environment (permissive):**
```toml
# project/dev
[install]
debugpy.pkg-path = "python311Packages.debugpy"
pytest.pkg-path = "python311Packages.pytest"

[vars]
DEBUG = "true"
LOG_LEVEL = "debug"
```

**Production environment (minimal):**
```toml
# project/prod
[install]
python.pkg-path = "python311"
# No dev tools

[vars]
DEBUG = "false"
LOG_LEVEL = "info"
```

**Use separately or compose:**
```bash
# Activate prod environment
flox activate -r project/prod

# Or activate dev environment
flox activate -r project/dev
```

(See **flox-environments** skill for layering environments at runtime)

## Composition with Local Packages

Combine composed environments with local packages:

```toml
# Compose base services
[include]
environments = [
    { remote = "team/database-services" },
    { remote = "team/cache-services" }
]

# Add project-specific packages
[install]
myapp.pkg-path = "company/myapp"
```

See **flox-environments** skill for layering environments at runtime.

## Best Practices

### For Shareable Environments

1. **Use descriptive names**: `team/postgres-service` not `db`
2. **Document expectations**: What vars/ports/services are provided
3. **Namespace everything**: Prefix vars, functions, services
4. **Keep focused**: One responsibility per environment
5. **Test standalone**: `flox activate` should work without composition

### For Composed Environments

1. **No name collisions**: Check for overlapping vars/services
2. **Idempotent hooks**: Can run multiple times safely
3. **Minimal auto-run**: Avoid output in `[profile]`
4. **Clear dependencies**: Document what environments are needed

(For layering best practices, see **flox-environments** skill)

## Version Management

### Pin Specific Versions

```toml
[include]
environments = [
    { remote = "team/base", version = "v1.2.3" }
]
```

### Use Latest

```toml
[include]
environments = [
    { remote = "team/base" }  # Uses latest
]
```

## Troubleshooting

### Conflicts in Composition

If composed environments conflict:
1. Use different `pkg-group` values
2. Adjust `priority` for file conflicts
3. Namespace variables to avoid collisions
4. Test each environment standalone first

(For layering troubleshooting, see **flox-environments** skill)

### Remote Environment Not Found

```bash
# Check available remote environments
flox search --remote owner/

# Pull and inspect locally
flox pull owner/environment-name
flox list -c
```

## Related Skills

- **flox-environments** - Creating base environments
- **flox-services** - Sharing service configurations
- **flox-containers** - Deploying shared environments
- **flox-publish** - Publishing packages vs environments
