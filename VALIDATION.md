# Validation and import provenance

Prepared on 29 October 2026 on branch `codex/expand-skills-upstream-sync`.

- Started from `sf-core-skills` commit `33d1512`, containing the original 16 skills.
- Reused 32 existing Copilot-adapted skills from the local Salesforce Copilot mirror,
  pinned to official Salesforce commit `e5164d94d7511c00fa02a5b8b60754b2361e178f`.
- `platform-role-hierarchy-apply` was absent from that mirror. Adapted it from official
  Salesforce commit `985407c7f7896030759d3310fe47d652265916b3` with the same conversion.
- The original 16 already reflected `985407c7f7896030759d3310fe47d652265916b3`.
- A fresh fetch of official `main` confirmed `985407c7f7896030759d3310fe47d652265916b3`
  remained the latest source. Both source revisions were fetched to establish a
  genuine baseline for the updater test, rather than treating all files as new.
- The pre-update, read-only comparison found **six changed upstream files in five
  skills**, with no additions/removals. The changes affect custom fields, custom
  metadata types, custom objects, custom settings, and value sets. They improve
  metadata-context routing, BusinessProcess naming guidance, and standard picklist
  value guidance.

## Regression checks completed before writing the target repository

The initial **12 updater/installer regression tests passed** before writing the target repository. After the real network test exposed a macOS temporary-path issue, a dedicated regression was added; all **13 tests passed in the new repository**. They cover read-only change
detection, applying a new source commit while retaining Copilot notes, exact
replacement conflicts, local-edit and executable-mode protection, added/removed
resources, preservation of unrelated files, symlinks, unexpected origins, dirty
upstream checkouts, unsafe selections, quiet handling of unrelated upstream commits,
adapter regeneration, consumer installation, and report-path protection.

## Real repository execution

Executed using the new repository's own `.venv` and scripts in
`/Users/weiwu/Developer/sf-core-skills`:

| Check | Actual result |
|---|---|
| Fresh-network pre-update comparison | Exit **2**: correctly found six modified selected files, zero added/removed files |
| Fresh-network update | Exit **0**: accepted official commit `985407c7f7896030759d3310fe47d652265916b3`; 55 generated/provenance files changed, including reapplying Copilot guidance across the collection |
| Local integrity | Exit **0**: **3,388 managed files** verified |
| Locked regeneration from a clean official checkout | Exit **0**: **zero changes** |
| Fresh-network post-update comparison | Exit **0**: **zero selected source changes** |
| Scheduled `--update-if-needed` path on the accepted source | Exit **0**: no changes; lock hash and modification time unchanged |
| Actual consumer-project installation | Exit **0**: all **49 skills** installed; repeated `--check` reported zero changes |
| Independent resource comparison | All **3,384 skill-file inventories and executable bits** match the pinned source; non-`SKILL.md` resources match byte-for-byte |
| Updater/installer regressions in the new environment | **13 passed**, including new-commit updates, maintained-note retention, local-edit protection, exact-replacement conflicts, and the macOS temporary-directory regression |
| Workflow definitions | Both YAML files parsed; scheduled/manual and PR/push triggers checked. GitHub-hosted execution was not performed |

The first fresh-network check stopped before writing any generated file because
macOS exposes its temporary directory through `/var -> /private/var`. Canonicalizing
the temporary checkout root fixed that false positive, while tests still reject
symlinks inside managed content. The check was rerun and returned the expected
six-file difference before the successful update.

Private local run reports are ignored under `.sync/before-update.json`,
`.sync/applied-update.json`, and `.sync/after-update.json`. They record the actual
candidate commit and selected source-file differences. No installed dependency,
virtual environment, temporary consumer project, or report is included in Git.

The 49-skill collection contains **five declared MCP-service users**. The updater
does not turn them into CLI-only skills; their requirements remain visible in
`DEPENDENCIES.md` and the individual playbooks.

No Salesforce org operations are part of the updater. Skill runtime behavior and
the scheduled GitHub workflow are separate validation scopes.
