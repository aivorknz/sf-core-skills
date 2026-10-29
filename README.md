# sf-core-skills

**49 Salesforce skills adapted for GitHub Copilot**, with their bundled references,
scripts, templates, and schema files. Modified from
[forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills).

The skills are industry-agnostic: they apply across Salesforce implementations,
not to a single product or vertical. This collection contains the original 16
skills plus the 33 requested additions. It does not install Pi or require a Pi
runtime. Copilot adaptations are maintained separately so upstream updates can
be reviewed and applied repeatedly.

- [Skill catalog](CATALOG.md): all selected skills and their descriptions.
- [Dependencies](DEPENDENCIES.md): declared MCP services, CLI tools, and related skills.
- [Validation](VALIDATION.md): import provenance and the actual updater tests.

## Install in a Salesforce project

Use Python 3.10+ and Git for maintenance/installation:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/sync.py --verify
.venv/bin/python scripts/install.py --target /absolute/path/to/salesforce-project
```

The target must exist. The installer copies the 49 skill directories into the
project's `.github/skills/`, retains license notices, and records ownership in
`.github/sf-core-skills.lock.json`. It preserves unrelated project files and refuses
existing collisions or edits to files it previously installed. Re-run it after
accepting an update. Add `--check` to compare an installation without writing.

This repository keeps skills in top-level folders. Opening this collection alone
does not install them into Copilot's default `.github/skills` discovery path.
No custom Copilot agent is bundled; use your normal Copilot agent or an existing
project-specific custom agent.

### Copilot CLI

Install the official GitHub Copilot CLI, sign in with your Copilot account, then
start it from the installed Salesforce project:

```bash
copilot login
cd /absolute/path/to/salesforce-project
copilot
```

In the interactive chat, use `/skills list` to inspect discovery and
`/skills info platform-apex-test-generate` to inspect a skill. Use `/skills reload`
after an update, or start a fresh session. For example:

```text
Use platform-apex-test-generate to review force-app/main/default/classes/MyClassTest.cls.
Invoke the skill and read its relevant references. Report the actual paths read.
Do not edit files, access authentication files, deploy, or run live tests.
```

### VS Code UI

1. Open the installed Salesforce project.
2. Run **Chat: Open Agents window** from the Command Palette.
3. Choose the workspace and **Copilot** session type, and check the signed-in account.
4. Open **Customizations → Skills** and confirm the installed skills are loaded.
5. Use your normal Copilot agent, send the prompt above, and inspect the completed
   steps for an actual skill invocation and file reads.

The earlier 16-skill collection was exercised through Copilot CLI and VS Code's
Agents-window Copilot runtime. This expanded collection's updater tests are
recorded separately in `VALIDATION.md`; discovery is not proof that every skill's
org operation works in your environment.

## Runtime dependencies

Local source review does not need a Salesforce connection. Org inspection, live
Apex tests, deployment, data changes, and configuration work need Salesforce CLI,
an authenticated explicit target, and appropriate permissions/features. Other
tasks can need Node/npm, Python, jq, Java, Code Analyzer, TypeScript, Vlocity Build,
or external API access. None of these is supplied by copying skill folders.

**The original "15 without mandatory MCP" count does not apply to all 49 skills.**
Five selected skills declare MCP services: Flow generation, custom fields,
FlexiPages, reports, and value sets. Their required versus optional steps remain
defined by each playbook; the named services are not bundled or configured here.
See `DEPENDENCIES.md` before using them. The role-hierarchy skill also needs its
specific bulk API entitlement, and ApexGuru needs access to its scan service.

Plugin hooks and language servers from other clients are not automatically active
in Copilot. The collection retains upstream resources but does not provide Pi's
guardrails or the Salesforce plugin's production-deploy hook.

## Check and update from Salesforce

```bash
# Verify local generated hashes and the recorded adapter/config inputs; no network.
.venv/bin/python scripts/sync.py --verify

# Fetch official main; check selected upstream content without changing skill files.
# Exit 0: no selected changes. Exit 2: selected changes found. Exit 1: failure/blocker.
.venv/bin/python scripts/sync.py --check-upstream --report .sync/upstream-report.json

# Fetch official main, reapply maintained adaptations, and update the local snapshot.
.venv/bin/python scripts/sync.py

# Reproduce the exact accepted commit without writing changes.
.venv/bin/python scripts/sync.py --locked --check

# Run updater/installer regression tests. These use local fixtures, not Salesforce orgs.
.venv/bin/python -m unittest discover -s tests -v
```

`--source /path/to/clean/sf-skills` uses an existing official checkout. Its origin,
clean status, and commit are checked. `--check` compares full regeneration without
writing and exits 2 for drift. `--update-if-needed` updates only when selected
upstream content or adapter/config inputs change, ignoring unrelated upstream
commits. Check-only reports may be written to `.sync/` or outside the repository.

`upstream.json` selects skills and the tracked ref. `upstream.lock.json` records
the accepted upstream commit, original source hashes, generated hashes/modes, and
adapter/config fingerprints. Scripts, templates, and references are preserved
byte-for-byte unless an explicit maintained replacement targets them. Updates
fetch source; they never install or execute upstream scripts.

### Preserve our modified versions

Keep modifications in the maintained inputs, then regenerate:

- `adapters/copilot.md`: shared Copilot guidance.
- `adapters/notes/<skill>.md`: skill-specific additions.
- `adapters/replacements.json`: exact, reviewed changes to an upstream body/resource.

For an exact replacement, use an entry with `skill`, skill-relative `path`, `old`,
and `new` strings. The old text must match **exactly once**. An upstream change
that breaks this match stops the update before any generated file is written.

Do not edit generated files directly. A direct edit or executable-mode change
blocks updates and installation instead of being overwritten. Move intentional
guidance to an adapter and restore the generated baseline before regenerating.
Missing/renamed upstream skills also stop for review; they are not silently dropped.
Review source changes, adapters, and `DEPENDENCIES.md` before accepting an update.

### Weekly update checks

`.github/workflows/sync-upstream.yml` checks official Salesforce main every
**Sunday at 20:23 UTC**, and supports manual runs. When selected source or adapter
inputs change, it regenerates, runs tests/integrity/locked checks, then opens or
updates the **`automation/salesforce-upstream-sync` pull request**. It never merges
the PR. Unrelated upstream commits do not create update PRs. A replacement conflict
or local-edit blocker fails the run for review without overwriting those files.

The schedule becomes active only after the workflow reaches the repository's
default branch and GitHub Actions is enabled. The repository/organization must allow
Actions to create pull requests and permit `contents: write` and `pull-requests: write`
for this job, plus the referenced Actions. No Salesforce credentials are needed.
Actions-created PRs may require a manual validation run under your repository's
workflow policies; the sync job performs its own checks before proposing the PR.

The separate validation workflow runs on PRs, pushes to `main`, and manual requests.
After merging an accepted update, pull it and reinstall it in consumer projects;
existing installed copies are not automatically changed.

## License

Licensed under the [Apache License, Version 2.0](LICENSE). Salesforce attribution
is retained in [NOTICE](NOTICE), and the pinned upstream license is retained under
`upstream/LICENSE.txt`. This independent compatibility collection is not an official
Salesforce product and does not imply Salesforce endorsement.
