> **Optional hooks are not installed:** Bundled Claude PostToolUse/LSP scripts
> are retained as upstream resources, not registered Copilot hooks. In particular,
> `scripts/lwc-lsp-validate.py` expects an external `lsp-engine` and LWC language server.
> Do not run it as a standalone check or assume it ran automatically. Use the project's
> configured Jest, lint/build, and Salesforce validation commands for the checks they
> actually provide, and report any requested LSP check as unavailable until configured.
