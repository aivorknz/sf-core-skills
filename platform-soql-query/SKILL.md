---
name: platform-soql-query
description: 'Use when the user needs SOQL/SOSL authoring or optimization: natural-language-to-query
  generation, relationship queries, aggregates, query-plan/selectivity analysis, and
  performance or safety improvements. TRIGGER when the user writes, optimizes, or
  debugs SOQL/SOSL, touches .soql files, or asks about relationship queries, aggregates,
  or query performance. DO NOT TRIGGER for bulk data operations (use platform-data-manage),
  Apex DML logic (use platform-apex-generate), or report/dashboard queries.'
metadata:
  version: '1.1'
  domains:
  - Platform
  relatedSkills:
  - experience-lwc-generate
  - platform-apex-generate
  - platform-apex-logs-debug
  - platform-apex-test-run
  - platform-data-manage
  cliTools:
  - tool:
    - jq
    semver: '>=1.6.0'
  - tool:
    - python3
    semver: '>=3.10.0'
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


# platform-soql-query: Salesforce SOQL Query Expert

Use this skill when the user needs **SOQL/SOSL authoring or optimization**: natural-language-to-query generation, relationship queries, aggregates, query-plan analysis, and performance/safety improvements for Salesforce queries.

## When This Skill Owns the Task

Use `platform-soql-query` when the work involves:
- `.soql` files
- query generation from natural language
- relationship queries and aggregate queries
- query optimization and selectivity analysis
- SOQL/SOSL syntax and governor-aware design

Delegate elsewhere when the user is:
- performing bulk data operations → [platform-data-manage](../platform-data-manage/SKILL.md)
- embedding query logic inside broader Apex implementation → [platform-apex-generate](../platform-apex-generate/SKILL.md)
- debugging via logs rather than query shape → [platform-apex-logs-debug](../platform-apex-logs-debug/SKILL.md)

---

## Required Context to Gather First

Ask for or infer:
- target object(s)
- fields needed
- filter criteria
- sort / limit requirements
- whether the query is for display, automation, reporting-like analysis, or Apex usage
- whether performance / selectivity is already a concern

---

## Recommended Workflow

### 1. Generate the simplest correct query
Prefer:
- only needed fields
- clear WHERE criteria
- reasonable LIMIT when appropriate
- relationship depth only as deep as necessary

### 2. Choose the right query shape
| Need | Default pattern |
|---|---|
| parent data from child | child-to-parent traversal |
| child rows from parent | subquery |
| counts / rollups | aggregate query |
| records with / without related rows | semi-join / anti-join |
| text search across objects | SOSL |

### 3. Optimize for selectivity and safety
Check:
- indexed / selective filters
- no unnecessary fields
- no avoidable wildcard or scan-heavy patterns
- security enforcement expectations

### 4. Validate execution path if needed
If the user wants runtime verification, hand off execution to:
- [platform-data-manage](../platform-data-manage/SKILL.md)

---

## High-Signal Rules

- never use `SELECT *` style thinking; query only required fields
- do not query inside loops in Apex contexts
- prefer filtering in SOQL rather than post-filtering in Apex
- use aggregates for counts and grouped summaries instead of loading unnecessary records
- evaluate wildcard usage carefully; leading wildcards often defeat indexes
- account for security mode / field access requirements when queries move into Apex

---

## Output Format

When finishing, report in this order:
1. **Query purpose**
2. **Final SOQL/SOSL**
3. **Why this shape was chosen**
4. **Optimization or security notes**
5. **Execution suggestion if needed**

Suggested shape — use `references/soql-syntax-reference.md` for exact syntax:

```text
Query goal: <summary>
Query: <soql or sosl>
Design: <relationship / aggregate / filter choices>
Notes: <selectivity, limits, security, governor awareness>
Next step: <run in platform-data-manage or embed in Apex>
```

---

## Cross-Skill Integration

| Need | Delegate to | Reason |
|---|---|---|
| run the query against an org | [platform-data-manage](../platform-data-manage/SKILL.md) | execution and export |
| embed the query in services/selectors | [platform-apex-generate](../platform-apex-generate/SKILL.md) | implementation context |
| analyze slow-query symptoms from logs | [platform-apex-logs-debug](../platform-apex-logs-debug/SKILL.md) | runtime evidence |
| wire query-backed UI | [experience-lwc-generate](../experience-lwc-generate/SKILL.md) | frontend integration |
| validate query behavior in tests | [platform-apex-test-run](../platform-apex-test-run/SKILL.md) | test coverage for query logic |

---

## Score Guide

| Score | Meaning |
|---|---|
| 90+ | production-optimized query |
| 80–89 | good query with minor improvements possible |
| 70–79 | functional but performance concerns remain |
| < 70 | needs revision before production use |

---

## Reference File Index

| File | When to read |
|------|-------------|
| `references/soql-syntax-reference.md` | Syntax, operators, date literals, relationship query patterns |
| `references/query-optimization.md` | Selectivity rules, indexing strategy, governor limits, security patterns |
| `references/soql-reference.md` | Quick reference — operators, date functions, aggregate functions, WITH clauses |
| `references/anti-patterns.md` | Common SOQL mistakes and their fixes — read before finalizing any query |
| `references/selector-patterns.md` | Apex selector layer patterns — read when embedding queries in Apex classes |
| `references/field-coverage-rules.md` | Field coverage validation — read when generating SOQL used inside Apex code |
| `references/cli-commands.md` | sf CLI query execution, bulk export, query plan commands |
| `assets/basic-queries.soql` | Starter query examples for common objects |
| `assets/relationship-queries.soql` | Parent-to-child and child-to-parent relationship query patterns |
| `assets/aggregate-queries.soql` | COUNT, SUM, GROUP BY, ROLLUP query patterns |
| `assets/optimization-patterns.soql` | Selective filter and index-aware query patterns |
| `assets/bulkified-query-pattern.cls` | Apex Map-based bulk query pattern for trigger contexts |
| `assets/selector-class.cls` | Full selector class implementation template |
| `scripts/post-tool-validate.py` | Post-write hook — runs static SOQL validation and live query plan analysis after `.soql` file edits |
