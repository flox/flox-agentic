# Flox Agentic Tools

This repository provides tools and integrations for AI agents to work with Flox, offering expert guidance and automation for Flox development environments, builds, services, and deployments.

## Overview

This project includes specialized knowledge and tooling for Flox workflows, best practices, and patterns. It provides a comprehensive set of skills covering the entire Flox development lifecycle, from environment setup to production deployment, accessible through multiple AI agent platforms.

## Components

### Skills Library

The repository includes four specialized skills, each focused on a specific aspect of Flox:

#### 1. **flox-environments**
Manage reproducible development environments with Flox. This is the foundational skill that should be used first when creating any new project. Covers:
- Installing packages and managing dependencies
- Python, Node.js, and Go environment setup
- Environment configuration and secrets management
- Reproducible development workflows
- Sharing, composing, and layering environments — composition via `[include]`, remote environments, FloxHub, team collaboration (see `references/sharing.md`)
- Running services, background processes, and databases (see `references/services.md`)
- Building and packaging applications — manifest/Nix builds, sandbox modes, multi-stage builds (see `references/builds.md`)

#### 2. **flox-containers**
Containerizing Flox environments with Docker/Podman. Covers:
- Creating container images from Flox environments
- OCI exports
- Multi-stage container builds
- Deployment workflows

#### 3. **flox-publish**
Publishing packages to Flox for distribution and sharing. Covers:
- Package publishing workflows
- Organization and personal namespace management
- Package versioning and distribution
- Sharing built packages across teams

#### 4. **flox-cuda**
CUDA and GPU development with Flox (Linux only). Covers:
- NVIDIA CUDA toolkit setup
- GPU computing workflows
- Deep learning framework integration
- cuDNN configuration
- Cross-platform GPU/CPU development

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
- Creating a new project, or setting up services/databases? The **flox-environments** skill activates first
- Building packages? The **flox-builds** skill helps with manifest or Nix builds
- Deploying containers? The **flox-containers** skill assists with containerization

#### Other Agents (Cursor, Copilot, Windsurf, Gemini, and more)

For agents that support the [skills.sh](https://skills.sh) standard, you
can install the full Flox skills library with a single command (requires
Node.js):

```bash
npx skills add flox/flox-agentic
```

This installs all six Flox skills into your agent's context, covering
environments (including sharing/composition), services, builds, containers, publishing, and CUDA.
Supported agents include Cursor, GitHub Copilot, Windsurf, Gemini, and
[many others](https://skills.sh).

> **Note:** skills.sh is a third-party tool, not maintained by Flox.
> See [skills.sh](https://skills.sh) for supported agents and documentation.

## Documentation

For detailed documentation on each skill, see the individual SKILL.md files in the `skills/` directory:
- `skills/flox-environments/SKILL.md`
- `skills/flox-containers/SKILL.md`
- `skills/flox-publish/SKILL.md`
- `skills/flox-cuda/SKILL.md`

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

See LICENSE file for details.
