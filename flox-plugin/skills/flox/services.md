# Flox Services Guide

## Running Services in Flox Environments

- Start with `flox activate --start-services` or `flox activate -s`
- Define `is-daemon`, `shutdown.command` for background processes
- Keep services running using `tail -f /dev/null`
- Use `flox services status/logs/restart` to manage (must be in activated env)
- Service commands don't inherit hook activations; explicitly source/activate what you need

## Network Services Pattern

Always make host/port configurable via vars:

```toml
[services.webapp]
command = '''exec app --host "$APP_HOST" --port "$APP_PORT"'''
vars.APP_HOST = "0.0.0.0"  # Network-accessible
vars.APP_PORT = "8080"
```

## Service Logging Pattern

Always pipe to `$FLOX_ENV_CACHE/logs/` for debugging:

```toml
command = '''exec app 2>&1 | tee -a "$FLOX_ENV_CACHE/logs/app.log"'''
```

## Python venv Pattern for Services

Services must activate venv independently:

```toml
command = '''
  [ -f "$FLOX_ENV_CACHE/venv/bin/activate" ] && \
    source "$FLOX_ENV_CACHE/venv/bin/activate"
  exec python-app "$@"
'''
```

## Using Packaged Services

Override package's service by redefining with same name.

## Example: Database Service

```toml
[services.database]
command = "postgres start"
vars.PGUSER = "myuser"
vars.PGPASSWORD = "super-secret"
vars.PGDATABASE = "mydb"
vars.PGPORT = "9001"
```

## Environment Variable Convention

Use variables like `POSTGRES_HOST`, `POSTGRES_PORT` to define where services run.
- `*_HOST` is the hostname or IP address (e.g., `localhost`, `db.example.com`)
- `*_PORT` is the network port number (e.g., `5432`, `6379`)

This pattern ensures users can override them at runtime:
```bash
POSTGRES_HOST=db.internal POSTGRES_PORT=6543 flox activate
```
