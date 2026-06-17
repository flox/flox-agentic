# Flox Agentic Tools

This repository provides tools and integrations for AI agents to work with Flox, offering expert guidance and automation for Flox development environments, builds, services, and deployments.

## Overview

This project includes specialized knowledge and tooling for Flox workflows, best practices, and patterns. It provides a comprehensive set of skills covering the entire Flox development lifecycle, from environment setup to production deployment, accessible through multiple AI agent platforms.

## Components

### The Flox Skill

The repository provides a single `flox` skill (`flox-environments`) covering the
entire Flox development lifecycle. The top `SKILL.md` holds the core guidance and
routes to detailed **reference files** for specialized topics (progressive
disclosure). It is the foundational skill that should be used first when creating
any new project. Covers:

- Installing packages and managing dependencies
- Python, Node.js, and Go environment setup
- Environment configuration and secrets management
- Reproducible development workflows
- Sharing, composing, and layering environments — composition via `[include]`, remote environments, FloxHub, team collaboration (see `references/sharing.md`)
- Running services, background processes, and databases (see `references/services.md`)
- Building and packaging applications — manifest/Nix builds, sandbox modes, multi-stage builds (see `references/builds.md`)
- Containerizing environments with Docker/Podman — OCI exports, multi-stage container builds, deployment (see `references/containers.md`)
- Publishing packages/builds to FloxHub — org/personal namespaces, versioning, distribution (see `references/publish.md`)
- CUDA and GPU development (Linux) — NVIDIA CUDA toolkit, cuDNN, deep-learning frameworks, cross-platform GPU/CPU (see `references/cuda.md`)

## Installation

### Prerequisites

- Flox CLI installed and configured
- For GPU development: Linux system with NVIDIA GPU (aarch64-linux or x86_64-linux)

### Application-Specific Setup

#### Claude Code

The Flox plugin for Claude Code provides comprehensive Flox integration, including package management, environment composition, service orchestration, build system configuration, containerization, publishing, and CUDA support. The plugin provides the Skills library as native Claude skills.

**Install the Plugin:**

From within Claude Code:

```bash
/plugin marketplace add flox/flox-agentic
/plugin install flox@flox-agentic
```

Or from the command line:

```bash
claude plugin marketplace add flox/flox-agentic
claude plugin install flox@flox-agentic
```

**Getting Started:**

Once installed, the plugin automatically activates. Claude Code will use the appropriate skill based on your task:
- Creating a new project, setting up services/databases, building, containerizing, or publishing? The **flox-environments** skill activates first

#### Other Agents (Cursor, Copilot, Windsurf, Gemini, and more)

For agents that support the [skills.sh](https://skills.sh) standard, you
can install the full Flox skills library with a single command (requires
Node.js):

```bash
npx skills add flox/flox-agentic
```

This installs the Flox skill into your agent's context, covering environments
plus sharing/composition, services, builds, containers, publishing, and CUDA/GPU
(via its reference files).
Supported agents include Cursor, GitHub Copilot, Windsurf, Gemini, and
[many others](https://skills.sh).

> **Note:** skills.sh is a third-party tool, not maintained by Flox.
> See [skills.sh](https://skills.sh) for supported agents and documentation.

## Documentation

The Flox skill lives in `skills/flox-environments/`:
- `skills/flox-environments/SKILL.md` — core guidance + routing
- `skills/flox-environments/references/` — detailed references: `sharing.md`, `services.md`,
  `builds.md`, `containers.md`, `publish.md`, `cuda.md`

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

See LICENSE file for details.
