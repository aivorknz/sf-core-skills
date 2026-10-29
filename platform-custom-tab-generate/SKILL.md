---
name: platform-custom-tab-generate
description: Use this skill when users need to create or configure Salesforce Custom
  Tabs. Trigger when users mention tabs, navigation tabs, object tabs, web tabs, Visualforce
  tabs, Lightning component tabs, app page tabs, or tab configuration. Also use when
  users want to add navigation to custom objects, create tabs for external content,
  or set up Lightning page tabs. Always use this skill for any custom tab work.
metadata:
  version: '1.0'
  domains:
  - Platform
  minApiVersion: '60.0'
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


## When to Use This Skill

Use this skill when you need to:
- Create tabs for objects, web pages, or Visualforce pages
- Add navigation tabs to applications
- Configure tab visibility and access
- Troubleshoot deployment errors related to custom tabs

## Specification

# CustomTab Metadata Specification

## Overview
Custom tabs for navigating to objects, web content, or Visualforce pages within Salesforce applications.

## Purpose
- Provide navigation to custom objects
- Link to external web content
- Access Visualforce pages
- Organize application navigation

## Required Properties

### Core Tab Properties
- **customObject**: `true` for custom object tabs, `false` for all others.
- **motif**: Tab icon style — choose a motif that semantically matches the object's purpose. Do NOT reuse the same motif for every tab.
- **label**: Display name (required for non-object tabs ONLY; object tabs inherit label from the object)
- **url**: Web URL (for web tabs)
- **page**: Visualforce page name (for Visualforce tabs)


### STRICT ELEMENT ALLOWLIST — READ THIS FIRST

**The root element MUST always be `<CustomTab>` (NOT `<Tab>`).** The XML namespace must be `xmlns="http://soap.sforce.com/2006/04/metadata"`.

Only the elements listed below are valid. **Any element not on this list WILL cause a deployment error.**

| Tab Type | ONLY these elements are allowed (nothing else) |
|---|---|
| **Object tabs** | `<customObject>` (required, set to `true`), `<motif>` (required), `<description>` (optional) |
| **Web tabs** | `<customObject>` (required, set to `false`), `<label>` (required), `<motif>` (required), `<url>` (required), `<urlEncodingKey>` (required, set to `UTF-8`), `<description>` (optional), `<frameHeight>` (optional) |
| **Visualforce tabs** | `<customObject>` (required, set to `false`), `<label>` (required), `<motif>` (required), `<page>` (required), `<description>` (optional) |

### FORBIDDEN ELEMENTS (every one of these causes a deployment error)
`<sobjectName>`, `<name>`, `<fullName>`, `<apiVersion>`, `<isHidden>`, `<tabVisibility>`, `<type>`, `<mobileReady>`, `<urlFrameHeight>`, `<urlType>`, `<urlRedirect>`, `<encodingKey>`, `<height>`, `<auraComponent>`

Also forbidden:
- `<label>` on object tabs (object tabs inherit their label from the custom object)
- `<page>` on web tabs (only for Visualforce tabs)
- Empty elements like `<page></page>` or `<description></description>`
- Any element not in the allowlist table above

## Tab Types

### Object Tabs
- **Purpose**: Navigate to custom or standard objects
- **File name** determines the object: `{ObjectApiName}.tab-meta.xml` (e.g., `Space_Station__c.tab-meta.xml`)
- **Required elements**: `<customObject>true</customObject>` and `<motif>`
- **Correct example** (for a Space_Station__c.tab-meta.xml):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <customObject>true</customObject>
    <motif>Custom39: Telescope</motif>
</CustomTab>
```
- **Correct example** (for a Supply__c.tab-meta.xml — note different motif):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <customObject>true</customObject>
    <motif>Custom98: Truck</motif>
</CustomTab>
```
- **WRONG** — do NOT add `<sobjectName>`, `<name>`, `<fullName>`, or `<label>`:
```xml
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <sobjectName>Space_Station__c</sobjectName>  <!-- DEPLOYMENT ERROR -->
    <label>Space Station</label>                  <!-- DEPLOYMENT ERROR on object tabs -->
    <customObject>true</customObject>
    <motif>Custom57: Desert</motif>
</CustomTab>
```

### Web Tabs
- **Purpose**: Link to external websites or web applications
- **File name**: Use a descriptive name: `{TabName}.tab-meta.xml` (e.g., `Knowledge_Base.tab-meta.xml`)
- **COPY THIS EXACT TEMPLATE** — only replace the placeholder values. Do NOT add, remove, or rename any XML elements:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <customObject>false</customObject>
    <description>REPLACE_WITH_DESCRIPTION</description>
    <frameHeight>600</frameHeight>
    <label>REPLACE_WITH_LABEL</label>
    <motif>REPLACE_WITH_MOTIF</motif>
    <url>REPLACE_WITH_URL</url>
    <urlEncodingKey>UTF-8</urlEncodingKey>
</CustomTab>
```
- **These 7 elements above are the ONLY elements allowed in a web tab file.** Do not add ANY other elements.
- The `<description>` element is optional — you may remove it if not needed, but do not add anything else.

### Visualforce Tabs
- **Purpose**: Access custom Visualforce pages
- **File name**: `{TabName}.tab-meta.xml` (e.g., `Custom_Page_Tab.tab-meta.xml`)
- **Required elements**: `<customObject>false</customObject>`, `<label>`, `<motif>`, `<page>`
- **Correct example**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <customObject>false</customObject>
    <label>Custom Page</label>
    <motif>Custom46: Computer</motif>
    <page>CustomPage</page>
</CustomTab>
```

## Tab Configuration

### Tab Style
- **Default**: Use standard tab styling
- **Custom**: Can specify custom tab styles if needed

### Tab Visibility
- **Default**: Visible to all users with access
- **Custom**: Can be configured for specific user profiles

## Supported Applications
- **Standard Apps**: Available in standard Salesforce applications
- **Custom Apps**: Can be included in custom applications
- **Community Apps**: Available in community applications

## Integration Points
- **Object Relationships**: Links to related object records
- **Web Content**: External website integration
- **Visualforce Pages**: Custom page functionality
- **Lightning Components**: Modern component integration
## Best Practices
- Use clear, descriptive tab labels
- Choose appropriate tab types for functionality
- **Select a unique, contextually relevant motif for each tab** — do not default every tab to the same icon
- Consider user experience and navigation flow
- Test tab functionality across different applications
- Ensure proper permissions and visibility settings
- Follow consistent naming conventions
- Object tab files MUST only contain `<customObject>true</customObject>` and `<motif>` — nothing else
- Web tab files MUST only contain: `<customObject>false</customObject>`, `<label>`, `<motif>`, `<url>`, `<urlEncodingKey>`, and optionally `<description>`, `<frameHeight>` — nothing else
- Never include `<isHidden>`, `<tabVisibility>`, `<type>`, `<mobileReady>`, or empty elements
