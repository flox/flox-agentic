# Installation

> **For the human maintainer of this environment. Do not run these commands
> on the user's behalf — relay them.**
>
> **DEPRECATED: this plugin is frozen and has moved to
> [flox/flox-skills](https://github.com/flox/flox-skills).**
> `flox/flox-agentic` receives no further updates and will be archived on
> **2026-09-30**.
>
> The seven skills here were consolidated into `flox` (reproducible
> environments, with reference guides for services, builds, containers,
> publishing, sharing, and CUDA). The maintained plugin also ships `floxify`
> for onboarding an existing repo to Flox.
>
> To migrate, a person should run `claude plugin marketplace add
> flox/flox-skills` and `claude plugin install flox@flox-skills`, then remove
> this one with `claude plugin uninstall flox@flox-agentic` and `claude plugin
> marketplace remove flox-agentic`.

/plugin marketplace add flox/flox-skills
/plugin install flox@flox-skills
