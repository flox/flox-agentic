# Flox Skills

This directory is the shared skill library for the Flox Codex and Claude Code
plugins. Each subdirectory contains one skill, with its instructions in
`SKILL.md`.

## How Plugins Use These Skills

Both plugin manifests live one directory up, in `flox-plugin/`, and point at
this directory with the same relative path:

```json
{
  "skills": "./skills/"
}
```

- Codex manifest: `../.codex-plugin/plugin.json`
- Claude Code manifest: `../.claude-plugin/plugin.json`

Keep the skill directory layout compatible with both plugin systems unless a
platform-specific difference is intentional.

## Skill Inventory

- `flox-environments`: Create and manage reproducible Flox environments,
  install packages, configure hooks, and set up language toolchains.
- `flox-services`: Configure and operate services inside Flox environments,
  including logs, lifecycle commands, and service-specific runtime setup.
- `flox-builds`: Build packages with Flox manifest builds or Nix expression
  builds, including sandboxing and multi-stage build patterns.
- `flox-containers`: Export Flox environments as container images for Docker,
  Podman, OCI archives, and deployment workflows.
- `flox-publish`: Publish built packages to Flox for distribution through
  personal or organization namespaces.
- `flox-sharing`: Share, compose, and layer Flox environments through Git,
  FloxHub, and reusable team environment patterns.
- `flox-cuda`: Configure CUDA and GPU development workflows on supported Linux
  systems.

## Maintenance Notes

- Keep each skill in its own directory with a `SKILL.md` file.
- Preserve the YAML front matter at the top of each `SKILL.md`; plugin loaders
  use it for the skill name and description.
- When adding, renaming, or removing a skill, update this README and the
  top-level repository README together.
- Installation instructions belong in the top-level README. This file is for
  explaining the skill library itself.
