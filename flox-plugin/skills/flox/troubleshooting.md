# Flox Troubleshooting & Quick Tips

## Environment Variable Convention

Use variables like `POSTGRES_HOST`, `POSTGRES_PORT` to define where services run.

These store connection details *separately*:
- `*_HOST` is the hostname or IP address (e.g., `localhost`, `db.example.com`)
- `*_PORT` is the network port number (e.g., `5432`, `6379`)

This pattern ensures users can override them at runtime:
```bash
POSTGRES_HOST=db.internal POSTGRES_PORT=6543 flox activate
```

Use consistent naming across services so the meaning is clear to any system or person reading the variables.

## Quick Tips for [install] Section

### Tricky Dependencies
- If we need `libstdc++`, we get this from the `gcc-unwrapped` package, not from `gcc`
- If we need to have both in the same environment, we use either package groups or assign priorities
- If user is working with python and requests `uv`, they typically do not mean `uvicorn`; clarify which package user wants

### Conflicts
If packages conflict, use different `pkg-group` values or adjust `priority`. **CUDA packages require explicit priorities** (see language-patterns.md for CUDA details).

### Versions
Start loose (`"^1.0"`), tighten if needed (`"1.2.3"`)

### Platforms
Only restrict `systems` when package is platform-specific. **CUDA is Linux-only**: `["aarch64-linux", "x86_64-linux"]`

### Naming
Install ID can differ from pkg-path (e.g., `gcc.pkg-path = "gcc13"`)

### Search
Use `flox search` to find correct pkg-paths before installing

## Common Pitfalls

### Hooks Run Every Activation
Hooks run EVERY activation (keep them fast/idempotent)

### Hook vs Profile Functions
Hook functions are not available to users in the interactive shell; use `[profile]` for user-invokable commands/aliases

### Profile Code in Layered Environments
Profile code runs for each layered/composed environment; keep auto-run display logic in `[hook]` to avoid repetition

### Services Don't Preserve State
Services see fresh environment (no preserved state between restarts)

### Build Network Access
Build commands can't access network in pure mode (pre-fetch deps)

### Manifest Syntax Errors
Manifest syntax errors prevent ALL flox commands from working

### Package Search Case Sensitivity
Package search is case-sensitive; use `flox search --all` for broader results

## Debugging Tips

### Service Issues
- When debugging services, run the exact command from manifest manually first
- Check service logs: `flox services logs <service-name>`
- Test activation with `flox activate -- <command>` before adding to services

### Hook Issues
- Use `return` not `exit` in hooks
- Define env vars with `${VAR:-default}`
- Guard FLOX_ENV_CACHE usage: `${FLOX_ENV_CACHE:-}` with fallback

### Build Issues
- **Build hooks don't run**: `[hook]` scripts DO NOT execute during `flox build` - only during interactive `flox activate`
- Only packages in the `toplevel` group (default) are available during builds
- Packages with explicit `pkg-group` settings won't be accessible in build commands unless also installed to `toplevel`

### Understanding Build vs Runtime
Build commands run in activated environment but hooks don't execute. Wrapper scripts in `$out/bin/` handle runtime setup.

## Best Practices for Composed Environments
- Use descriptive, prefixed function names in composed envs
- Cache downloads in `$FLOX_ENV_CACHE`
- Log service output to `$FLOX_ENV_CACHE/logs/`
- Test composability: `flox activate` each env standalone first
