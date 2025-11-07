# Flox Plugin for Claude Code

This repository contains the official Flox plugin for Claude Code, providing expert guidance and automation for Flox development environments, builds, services, and deployments.

## Overview

The Flox plugin enhances Claude Code with specialized knowledge about Flox workflows, best practices, and patterns. It includes a comprehensive set of skills covering the entire Flox development lifecycle, from environment setup to production deployment.

## Getting Started

Once installed, the plugin automatically activates. Claude Code will use the appropriate skill based on your task:

- Creating a new project? The **flox-environments** skill activates first
- Setting up services? The **flox-services** skill provides guidance
- Building packages? The **flox-builds** skill helps with manifest or Nix builds
- Deploying containers? The **flox-containers** skill assists with containerization

## Installation

### Install the Plugin

To install the Flox plugin in Claude Code:

```bash
/plugin marketplace add flox/flox-agentic
/plugin install flox@flox
```

### Install the Flox MCP Server

To enable the Flox MCP server functionality, install the Flox package into an environment, ideally your default environment.
Since the MCP server uses the `stdio` transport, there's no service that runs and as long as `flox-mcp` is on path, it should work.

```bash
flox install flox/flox-mcp-server
```

Or you can run it directly without installation using the `flox/flox-mcp-server` remote environment.

```bash
flox activate -r flox/flox-mcp-server
```

The MCP server provides enhanced integration between Claude (and other agents) and Flox,
enabling seamless environment management and workflow automation.
Better gaurdrails can be established since all environment management happens through MCP tool commands and does not require `bash` access.

#### For Other Agents

The Claude plugin handles configuration for the MCP server when used.  But it can be used alone and with other agents.

##### Claude

```bash
# To install for Claude Code (per project):
claude mcp add flox -- flox-mcp

# To install for Claude Code (per user):
claude mcp add --scope user flox -- flox-mcp
```

##### Cursor

Make sure the MCP server is available (see Install above), and add it to your MCP configuration file at ~/.cursor/mcp.json:

```json
{
  "mcpServers": {
    "flox": {
      "command": "flox-mcp"
    }
  }
}
```

## Requirements

- Flox CLI installed and configured
- Claude Code
- For GPU development: Linux system with NVIDIA GPU (aarch64-linux or x86_64-linux)

## Components

### Claude Code Plugin

The plugin provides Claude Code with deep expertise in Flox, including:
- Package management and dependency resolution
- Environment composition and layering
- Service orchestration and background processes
- Build system configuration (both manifest and Nix expression builds)
- Containerization workflows
- Package publishing and distribution
- Team collaboration patterns
- CUDA and GPU development support

### Included Skills

The plugin includes seven specialized skills, each focused on a specific aspect of Flox:

#### 1. **flox-environments**
Manage reproducible development environments with Flox. This is the foundational skill that should be used first when creating any new project. Covers:
- Installing packages and managing dependencies
- Python, Node.js, and Go environment setup
- Environment configuration and secrets management
- Reproducible development workflows

#### 2. **flox-services**
Running services and background processes in Flox environments. Covers:
- Service configuration and lifecycle management
- Network services (HTTP servers, databases, etc.)
- Logging and debugging patterns
- Service orchestration

#### 3. **flox-builds**
Building and packaging applications with Flox. Covers:
- Manifest builds for quick iteration
- Nix expression builds for guaranteed reproducibility
- Sandbox modes and build isolation
- Multi-stage builds
- Packaging assets and artifacts

#### 4. **flox-containers**
Containerizing Flox environments with Docker/Podman. Covers:
- Creating container images from Flox environments
- OCI exports
- Multi-stage container builds
- Deployment workflows

#### 5. **flox-publish**
Publishing packages to Flox for distribution and sharing. Covers:
- Package publishing workflows
- Organization and personal namespace management
- Package versioning and distribution
- Sharing built packages across teams

#### 6. **flox-sharing**
Sharing and composing Flox environments. Covers:
- Environment composition and layering
- Remote environments via FloxHub
- Team collaboration patterns
- Reusable environment stacks

#### 7. **flox-cuda**
CUDA and GPU development with Flox (Linux only). Covers:
- NVIDIA CUDA toolkit setup
- GPU computing workflows
- Deep learning framework integration
- cuDNN configuration
- Cross-platform GPU/CPU development

### Flox MCP Server

This repository also includes the Flox MCP (Model Context Protocol) server configuration, which provides Claude Code with direct access to Flox functionality through structured tool interfaces.

## Documentation

For detailed documentation on each skill, see the individual SKILL.md files in the `skills/` directory:
- `skills/flox-environments/SKILL.md`
- `skills/flox-services/SKILL.md`
- `skills/flox-builds/SKILL.md`
- `skills/flox-containers/SKILL.md`
- `skills/flox-publish/SKILL.md`
- `skills/flox-sharing/SKILL.md`
- `skills/flox-cuda/SKILL.md`

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

See LICENSE file for details.
