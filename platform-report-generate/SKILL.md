---
name: platform-report-generate
description: Use when users create, generate, or validate Salesforce Lightning Report
  metadata (.report-meta.xml) — tabular, summary, matrix, or joined reports with columns,
  groupings, filters, charts, cross-filters, buckets, formulas, or time-frame filters.
  Triggers on "create a report", "build a report", "add a chart", or .report-meta.xml
  deploy errors. Do NOT trigger for Custom Report Type metadata (use platform-custom-report-type-generate),
  dashboards, list views, running reports in the UI, or SOQL.
metadata:
  version: '1.0'
  domains:
  - Platform
  minApiVersion: '60.0'
  relatedSkills:
  - platform-custom-report-type-generate
  mcpTools:
    salesforce-api-context:
      tools:
      - get_metadata_type_context
      - get_metadata_type_sections
      - get_metadata_type_shape
      semver: '>=1.0.0'
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

> **Declared service:** This skill declares `salesforce-api-context` metadata
> context tools. Those services are not installed here. Discover the actual tools
> before following a required service step and report missing capabilities.

## Overview

Lightning Reports define how Salesforce data is queried, grouped, filtered, and displayed. Each report is a single `.report-meta.xml` file placed under `reports/<FolderName>/` within the project's source directory (check `sfdx-project.json` → `packageDirectories[].path` for the source root).

## Critical Rules (Read First)

**TOP DEPLOYMENT KILLERS — check these BEFORE generating any report:**
1. **Grouping fields in columns** — Fields in `<groupingsDown>` or `<groupingsAcross>` must NEVER also appear in `<columns>`
2. **Wrong column names** — Column names are report-type-specific. ALWAYS call MCP tools to verify (see `references/column-names.md`)
3. **Wrong scope** — LeadList uses `org`, not `organization`
4. **Filter column dot notation** — Filter `<column>` values use FLAT names (`INDUSTRY`, `TYPE`) NOT dot notation (`ACCOUNT.INDUSTRY` is INVALID)
5. **Multi-value picklist filters** — Use ONE `<criteriaItems>` with comma-separated `<value>` (e.g., `Technology,Financial Services`). Do NOT split into multiple criteriaItems with booleanFilter

### Rule 1: Format Determines Required Elements

| Format | `<groupingsDown>` | `<groupingsAcross>` | `<block>` |
|--------|-------------------|---------------------|-----------|
| `Tabular` | Not allowed | Not allowed | No |
| `Summary` | At least 1 (max 3) | Not allowed | No |
| `Matrix` | At least 1 (max 3) | At least 1 (max 3) | No |
| `Joined` | Not at top level | Not at top level | At least 2 (max 5) |

### Rule 2: Use Platform Column Names

Report metadata uses **platform report column names**, NOT raw API field names. **ALWAYS call `get_metadata_type_sections` or `get_metadata_type_context` to confirm valid column names.** See `references/column-names.md` for common mappings per report type.

### Rule 3: Valid Report Type Required

`<reportType>` must be a standard API name (e.g., `Opportunity`, `AccountList`, `CaseList`, `LeadList`, `AccountContactRole`) or a deployed custom report type developer name.

### Rule 4–5: Chart & Aggregates Require Summary/Matrix

Charts and `<aggregateTypes>` (Sum, Average, etc.) only work in Summary and Matrix reports.

### Rule 6–8: Limits

- Max **3 cross-filters** per report, each with up to **5 criteria items**
- `<filterLogic>` must reference all filters sequentially (e.g., `1 AND (2 OR 3)`)
- Joined reports: 2–5 blocks, each block format must be Summary or Matrix (not Tabular)

### Rule 9: Folder Structure

Reports must live inside a folder with a corresponding folder metadata file:
```xml
<sourceDir>/reports/<FolderName>/<ReportName>.report-meta.xml
<sourceDir>/reports/<FolderName>-meta.xml
```
Determine `<sourceDir>` from `sfdx-project.json` (commonly `force-app/main/default`, but this is configurable).

### Rule 10–11: Date Columns & Scope

- Date columns use platform names (`CLOSE_DATE`, not `CloseDate`)
- LeadList scope is `org`; Opportunity/AccountList/CaseList use `organization`

### Rule 12–13: Description & Groupings

- `<description>` max **255 characters**
- Grouping fields must NOT appear in `<columns>` — automatic deployment failure

### Rule 14: Folder Metadata Requires `<sharedTo>`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ReportFolder xmlns="http://soap.sforce.com/2006/04/metadata">
    <folderShares>
        <accessLevel>Manage</accessLevel>
        <sharedTo>AllInternalUsers</sharedTo>
        <sharedToType>Group</sharedToType>
    </folderShares>
    <name>My Report Folder</name>
</ReportFolder>
```

### Rule 15: Valid Date Intervals Only

Use `INTERVAL_CURRENT` for "this quarter", `INTERVAL_CURY` for "this year", `INTERVAL_LAST30` for last 30 days. Do NOT use `INTERVAL_CURQ` — it is not valid. See `references/date-intervals.md` for the full list.

## Top-Level Elements

| Element | Required | Notes |
|---------|----------|-------|
| `<name>` | Yes | Report name (max 40 chars) |
| `<reportType>` | Yes | Report type API name |
| `<format>` | Yes | `Tabular`, `Summary`, `Matrix`, or `Joined` |
| `<scope>` | Recommended | `organization` (or `org` for LeadList) |
| `<columns>` | Yes | Field columns — each has `<field>` and optional `<aggregateTypes>` |
| `<filter>` | No | Contains `<criteriaItems>` with `<column>`, `<operator>`, `<value>` |
| `<groupingsDown>` | Conditional | Row groupings: `<field>`, `<dateGranularity>`, `<sortOrder>` |
| `<groupingsAcross>` | Conditional | Column groupings (Matrix only) |
| `<timeFrameFilter>` | Recommended | `<dateColumn>`, `<interval>`, optional `<startDate>`/`<endDate>` |
| `<chart>` | No | See `references/chart-types.md` |
| `<buckets>` | No | Bucket field definitions |
| `<crossFilters>` | No | Cross-object filters (`with`/`without`) |
| `<showDetails>` | Recommended | `true`/`false` |
| `<showGrandTotal>` | Recommended | `true`/`false` |
| `<showSubTotals>` | Recommended | `true`/`false` |
| `<description>` | Recommended | Business purpose (max 255 chars) |
| `<block>` | Conditional | Joined format blocks |

## Filter Syntax

```xml
<filter>
    <criteriaItems>
        <column>STAGE_NAME</column>
        <operator>equals</operator>
        <value>Closed Won</value>
    </criteriaItems>
</filter>
```

**Multi-value picklist:** Use ONE criteriaItem with comma-separated values:
```xml
<criteriaItems>
    <column>INDUSTRY</column>
    <operator>equals</operator>
    <value>Technology,Financial Services</value>
</criteriaItems>
```

Common operators: `equals`, `notEqual`, `lessThan`, `greaterThan`, `contains`, `startsWith`, `includes`, `excludes`, `isBlank`, `notBlank`. Full list in `references/filter-operations.md`.

## Generation Workflow

1. **Gather Requirements** — object, fields, groupings, filters, chart needs
2. **Determine Format** — no groupings → Tabular; row groupings → Summary; row + column → Matrix; multiple objects → Joined
3. **Identify Column Names** — call `get_metadata_type_sections` MCP tool to get valid platform column names for the report type
4. **Author Metadata** — start from closest example in `examples/` and adapt
5. **Create Folder** — generate folder directory + `<FolderName>-meta.xml` with `<folderShares>`
6. **Validate** — run through `references/verification-checklist.md`

## Reference File Index

| File | When to read |
|------|--------------|
| `references/column-names.md` | Step 3 — column name mappings per report type |
| `references/date-intervals.md` | When setting timeFrameFilter intervals |
| `references/chart-types.md` | When adding a chart — all 17 types + legendPosition rules |
| `references/filter-operations.md` | When building filters — complete operator reference |
| `references/verification-checklist.md` | Step 6 — pre-deploy validation |
| `references/errors-and-troubleshooting.md` | When fields are missing or deployment fails |
| `examples/TabularOpportunitiesReport.report-meta.xml` | Tabular report template |
| `examples/OpportunitiesByStageReport.report-meta.xml` | Summary report with chart |
| `examples/OpportunitiesByStageAndQuarter.report-meta.xml` | Matrix report template |
| `examples/AccountsCreatedThisYear.report-meta.xml` | Filtered report with time frame |
