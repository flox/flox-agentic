# Flox Agentic Tools

This repository provides skills for AI agents to work with Flox. Both Claude 
and Codex plugins are available.

## Components

### Flox MCP Server

The Flox MCP (Model Context Protocol) server provides agents with direct access
to Flox functionality through structured tool interfaces. It enables seamless
environment management and workflow automation with better guardrails, since all
environment management happens through MCP tool commands and does not require
`bash` access.

The MCP server uses the `stdio` transport, so there's no service that runs—as
long as `flox-mcp` is on your PATH, it will work.

### Skills Library

The repository includes seven specialized skills, each focused on a specific
aspect of Flox:

#### 1. **flox-environments**
Manage reproducible development environments with Flox. This is the
foundational skill that should be used first when creating any new project.
Covers:
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
- For GPU development: Linux system with NVIDIA GPU (aarch64-linux or
  x86_64-linux)

### Install the Flox MCP Server

First, install the Flox MCP server package into an environment, ideally your
default environment:

```bash
flox install flox/flox-mcp-server
```

Or you can make it available without installing by running the
`flox/flox-mcp-server` remote environment:

```bash
flox activate -r flox/flox-mcp-server
```

### Plugin Setup

Flox ships first-class plugin manifests for both Claude Code and Codex. Both
plugins use the same shared skill library in `flox-plugin/skills` and the same
Flox MCP server configuration in `flox-plugin/.mcp.json`.

#### Claude Code

The Flox plugin for Claude Code is defined in
`flox-plugin/.claude-plugin/plugin.json`. It provides native Claude skills for
Flox environment setup, services, builds, containers, publishing, sharing, and
CUDA workflows.

Install the plugin from within Claude Code:

```bash
/plugin marketplace add flox/flox-agentic
/plugin install flox@flox-agentic
```

Or install it from the command line:

```bash
claude plugin marketplace add flox/flox-agentic
claude plugin install flox@flox-agentic
```

The plugin includes MCP server configuration. You can also configure the MCP
server manually:

```bash
# Per project:
claude mcp add flox -- flox-mcp

# Per user:
claude mcp add --scope user flox -- flox-mcp
```

#### Codex

The Flox plugin for Codex is defined in `flox-plugin/.codex-plugin/plugin.json`.
It provides native Codex skills for Flox environment setup, services, builds,
containers, publishing, sharing, and CUDA workflows.

For local development, add this repository as a Codex marketplace and install
the plugin:

```bash
codex plugin marketplace add . # in top-level directory for this repo
codex plugin add flox@flox-agentic
```

This registers the local marketplace in your Codex user configuration and
enables the plugin for new Codex sessions.

#### Getting Started

Once installed, Codex or Claude Code will use the appropriate Flox skill based
on your task:
- Creating a new project? The **flox-environments** skill activates first
- Setting up services? The **flox-services** skill provides guidance
- Building packages? The **flox-builds** skill helps with manifest or Nix builds
- Deploying containers? The **flox-containers** skill assists with
  containerization

### MCP-Only Setup

#### Cursor

Make sure the MCP server is available (see "Install the Flox MCP Server"
above), then add it to your MCP configuration file at `~/.cursor/mcp.json`:

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

For Kiro, create a configuration file in `.kiro/settings/mcp.json` for
workspace-specific settings or `~/.kiro/settings/mcp.json` for user-wide
settings:

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

#### Other Agents (Cursor, Copilot, Windsurf, Gemini, and more)

For agents that support the [skills.sh](https://skills.sh) standard, you
can install the full Flox skills library with a single command (requires
Node.js):

```bash
npx skills add flox/flox-agentic
```

This installs all seven Flox skills into your agent's context, covering
environments, services, builds, containers, publishing, sharing, and CUDA.
Supported agents include Cursor, GitHub Copilot, Windsurf, Gemini, and
[many others](https://skills.sh).

> **Note:** skills.sh is a third-party tool, not maintained by Flox.
> See [skills.sh](https://skills.sh) for supported agents and documentation.

For MCP tool access, the Flox MCP server works with any agent that supports
the Model Context Protocol. Configure it per your agent's requirements,
ensuring `flox-mcp` is available in your PATH.

## Documentation

For detailed documentation on each skill, see the individual SKILL.md files in
the `flox-plugin/skills/` directory:
- `flox-plugin/skills/flox-environments/SKILL.md`
- `flox-plugin/skills/flox-services/SKILL.md`
- `flox-plugin/skills/flox-builds/SKILL.md`
- `flox-plugin/skills/flox-containers/SKILL.md`
- `flox-plugin/skills/flox-publish/SKILL.md`
- `flox-plugin/skills/flox-sharing/SKILL.md`
- `flox-plugin/skills/flox-cuda/SKILL.md`

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

See LICENSE file for details.
