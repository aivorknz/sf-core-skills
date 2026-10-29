---
name: dx-org-switch
description: Switches the active Salesforce org (default target-org) using the Salesforce
  CLI. Use whenever someone wants to change which org CLI commands run against — whether
  they say "switch org", "change default org", "set my org to", "use alias", "point
  to", or describe wanting to work against a specific org, scratch org, sandbox, or
  production.
metadata:
  version: '1.0'
  domains:
  - Developer Experience
  cliTools:
  - tool:
    - sf
    semver: '>=2.0.0'
---

<!-- Modified for GitHub Copilot by sf-core-skills; upstream copyright and license retained. -->

> **Copilot compatibility:** Resolve resources relative to this skill's installed
> directory. Read related skills from the sibling skill directories. Use the
> `.github/skills/` installation in place of historical `.claude/skills/`, `.vibe/skills/`,
> or Pi skill-path examples. Resolve these paths before executing embedded commands.
> Use available Copilot file, search, terminal, and question capabilities instead of assuming
> Claude/Pi tool names exist. MCP names in this playbook identify required services
> and operations, not guaranteed Copilot tool IDs: discover the actual connected
> tools and inspect their schemas first. Do not invent a tool or silently replace
> a mandatory MCP operation with CLI. Report missing dependencies before live work.
> Skill metadata and instructions do not enforce tool permissions or supply Pi's
> runtime guardrails. Keep Copilot approvals and organizational controls in effect.

> **Standalone Copilot setup:** Use Copilot's terminal and file tools for
> the Bash/Read/Write/Edit capabilities named below. This collection does not install
> MCP servers, plugin hooks, language servers, or related skills outside its selection.
> Use the local CLI workflows documented by this skill; mandatory MCP steps remain
> mandatory. Check a related skill exists before invoking it. For a missing setup or
> specialist helper, report the requirement instead of claiming it ran. Use an explicit
> authorized target-org alias for live commands and keep authentication output private.
> Command-reference files containing placeholders such as `<org>` or `<id>` are
> templates: substitute verified values before using individual commands, rather than
> executing the reference file unchanged.


## Steps

1. Identify the org: the user provides a username or alias (`orgIdentifier`). If not provided, run `sf org list` to show authenticated orgs and ask the user which one to use.
2. Set the default org:
   - Local (default): `sf config set target-org <orgIdentifier>`
     - Applies only within the current project directory. Use this for normal project work.
   - Global (only if user explicitly requests): `sf config set target-org <orgIdentifier> --global`
     - Applies system-wide across all directories. Use when working outside a project or when the user asks for global scope.
   - If this fails, report the error and suggest running `sf org login web` if the org may not be authorized.
3. Verify:
   - `sf config get target-org --json`
   - Note: the JSON output does not include a scope/location field — it cannot confirm whether the value is local or global. Confirm the value only, e.g.: `target-org is now set to: <value>`
   - If it fails, report the error and advise running `sf config get target-org`.

## Notes

- Unified CLI uses keys like `target-org` and `target-dev-hub`. Legacy sfdx keys (`defaultusername`, `defaultdevhubusername`) are deprecated in this context.
- The sf CLI does not have `--local` or `--scope` flags for config set. Local scope is the default behavior.
- If the org does not change after setting the config, check whether `SF_TARGET_ORG` is set — environment variables override config values.
- Salesforce CLI config (unified) reference: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_config_commands_unified.htm#cli_reference_config_set_unified
