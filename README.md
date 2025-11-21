# Flox Agentic Tools

This repository provides tools and integrations for AI agents to work with Flox, offering expert guidance and automation for Flox development environments, builds, services, and deployments.

## Overview

This project includes specialized knowledge and tooling for Flox workflows, best practices, and patterns. It provides a comprehensive set of skills covering the entire Flox development lifecycle, from environment setup to production deployment, accessible through multiple AI agent platforms.

## Components

### Flox MCP Server

The Flox MCP (Model Context Protocol) server provides agents with direct access to Flox functionality through structured tool interfaces. It enables seamless environment management and workflow automation with better guardrails, since all environment management happens through MCP tool commands and does not require `bash` access.

The MCP server uses the `stdio` transport, so there's no service that runs—as long as `flox-mcp` is on your path, it will work.

### Skills Library

The repository includes seven specialized skills, each focused on a specific aspect of Flox:

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

## Installation

### Prerequisites

- Flox CLI installed and configured
- For GPU development: Linux system with NVIDIA GPU (aarch64-linux or x86_64-linux)

### Install the Flox MCP Server

First, install the Flox MCP server package into an environment, ideally your default environment:

```bash
flox install flox/flox-mcp-server
```

Or you can run it directly without installation using the `flox/flox-mcp-server` remote environment:

```bash
flox activate -r flox/flox-mcp-server
```

### Application-Specific Setup

#### Claude Code

The Flox plugin for Claude Code provides deep expertise in Flox, including package management, environment composition, service orchestration, build system configuration, containerization, publishing, and CUDA support.

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

**Configure MCP Server:**

The plugin handles MCP server configuration automatically when used. You can also configure it manually:

```bash
# Per project:
claude mcp add flox -- flox-mcp

# Per user:
claude mcp add --scope user flox -- flox-mcp
```

**Getting Started:**

Once installed, the plugin automatically activates. Claude Code will use the appropriate skill based on your task:
- Creating a new project? The **flox-environments** skill activates first
- Setting up services? The **flox-services** skill provides guidance
- Building packages? The **flox-builds** skill helps with manifest or Nix builds
- Deploying containers? The **flox-containers** skill assists with containerization

#### Cursor

Make sure the MCP server is available (see "Install the Flox MCP Server" above), then add it to your MCP configuration file at `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "flox": {
      "command": "flox-mcp"
    }
  }
}
```

#### Kiro

For Kiro, create a configuration file in `.kiro/settings/mcp.json` for workspace-specific settings or `~/.kiro/settings/mcp.json` for user-wide settings:

```json
{
  "mcpServers": {
    "flox": {
      "command": "flox-mcp",
      "args": []
    }
  }
}
```

#### Other Agents

The Flox MCP server can be used with any agent that supports the Model Context Protocol. Configure it according to your agent's MCP configuration requirements, ensuring `flox-mcp` is available in your PATH.

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
