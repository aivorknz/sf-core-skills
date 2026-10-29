#!/usr/bin/env python3
"""Check/update selected Salesforce skills while preserving maintained Copilot adapters."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

import yaml
import mirror_lib as lib

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = "https://github.com/forcedotcom/sf-skills.git"


def inputs(root):
    paths = [lib.safe_path(root, "upstream.json")]
    for path in sorted((root / "adapters").rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Adapter symlink: {path}")
        if path.is_file():
            paths.append(path)
    return {p.relative_to(root).as_posix(): lib.sha(p.read_bytes()) for p in paths}


def config(root):
    data = json.loads(lib.safe_path(root, "upstream.json").read_text())
    if data["repository"].removesuffix(".git") != OFFICIAL.removesuffix(".git"):
        raise ValueError("Only the official Salesforce upstream is accepted")
    names = data["skills"]
    if not names or len(set(names)) != len(names):
        raise ValueError("Selection must contain unique skill names")
    if any(not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", n) for n in names):
        raise ValueError("Unsafe skill name")
    if not isinstance(data["ref"], str) or data["ref"].startswith("-"):
        raise ValueError("Invalid upstream ref")
    return data


def verify(root, check_inputs=True):
    lib.verify(root)
    lock = json.loads(lib.safe_path(root, lib.LOCK).read_text())
    if check_inputs and lock.get("inputs") != inputs(root):
        raise ValueError("Selection/adapters changed; regenerate before claiming verification")
    return lock


def collect(root, source, settings, commit):
    names = settings["skills"]
    output, originals, audit = {}, {}, []
    common = lib.safe_path(root, "adapters/copilot.md").read_text()
    replacements = json.loads(lib.safe_path(root, "adapters/replacements.json").read_text())
    for rule in replacements:
        if rule["skill"] not in names:
            raise ValueError(f"Replacement targets an unselected skill: {rule['skill']}")
        lib.safe_path(Path("/validation"), rule["path"])
    for name in names:
        folder = lib.safe_path(source, "skills/" + name)
        skill = folder / "SKILL.md"
        if not skill.is_file():
            raise ValueError(f"Selected skill removed/renamed upstream: {name}; review the selection")
        adapted, header = lib.adapt_skill(skill.read_text(), name)
        note_path = lib.safe_path(root, f"adapters/notes/{name}.md")
        note = note_path.read_text() if note_path.is_file() else ""
        adapted = adapted.replace(lib.BRIDGE + "\n", lib.BRIDGE + "\n" + common + "\n" + note + "\n", 1)
        metadata = header.get("metadata") or {}
        audit.append({"name": name, "description": header["description"],
                      "version": metadata.get("version"), "declared_mcp": metadata.get("mcpTools") or {},
                      "cli_tools": metadata.get("cliTools") or [],
                      "related_outside_selection": [n for n in metadata.get("relatedSkills", []) if n not in names]})
        paths = set()
        for file in sorted(folder.rglob("*")):
            if file.is_symlink():
                raise ValueError(f"Upstream symlink: {file}")
            if not file.is_file():
                continue
            relative = file.relative_to(folder).as_posix()
            paths.add(relative)
            key = f"{name}/{relative}"
            raw = file.read_bytes()
            mode = 0o755 if file.stat().st_mode & 0o111 else 0o644
            originals[key] = {"sha256": lib.sha(raw), "mode": mode}
            data = adapted.encode() if relative == "SKILL.md" else raw
            for rule in replacements:
                if rule["skill"] != name or rule["path"] != relative:
                    continue
                old, new = rule["old"].encode(), rule["new"].encode()
                if not old or data.count(old) != 1:
                    raise ValueError(f"Adapter conflict: {key}; exact replacement no longer matches once")
                data = data.replace(old, new, 1)
            output[key] = (data, mode)
        if any(r["skill"] == name and r["path"] not in paths for r in replacements):
            raise ValueError(f"Adapter conflict: replacement file disappeared in {name}")
    license_path = lib.safe_path(source, "LICENSE.txt")
    license_bytes = license_path.read_bytes()
    output["upstream/LICENSE.txt"] = (license_bytes, 0o644)
    originals["upstream/LICENSE.txt"] = {"sha256": lib.sha(license_bytes), "mode": 0o644}
    provenance = {"repository": settings["repository"], "ref": settings["ref"], "commit": commit}
    output["dependency-audit.json"] = (lib.json_bytes({"upstream": provenance,
        "classification": "Declared requirements, not proof of tool availability or end-to-end execution.",
        "skills_with_declared_mcp": sum(bool(r["declared_mcp"]) for r in audit), "skills": audit}), 0o644)
    lines = ["# Skill catalog", "", f"{len(names)} Copilot-adapted skills from Salesforce commit `{commit}`.", "",
             "| Skill | Description |", "|---|---|"]
    for row in audit:
        description = row["description"].split("TRIGGER")[0].split("Use this skill")[0].strip().replace("|", "\\|")
        lines.append(f"| `{row['name']}` | {' '.join(description.split())[:300]} |")
    output["CATALOG.md"] = (("\n".join(lines) + "\n").encode(), 0o644)
    lines = ["# Dependencies", "", f"Reviewed source: `{commit}`. {len(names)} selected skills.", "",
             "MCP declarations may apply to specific operations; read the skill before use. No service is installed by copying skills.",
             "Optional plugin hooks, language servers, licenses and API entitlements are not supplied. Related skills outside this list are not installed.", "",
             "| Skill | Declared MCP services | Declared CLI tools | Related skills outside selection |", "|---|---|---|---|"]
    for row in audit:
        tools = sorted({t for item in row["cli_tools"] for t in item.get("tool", [])})
        lines.append(f"| `{row['name']}` | {', '.join(row['declared_mcp']) or 'None declared'} | {', '.join(tools) or 'See skill'} | {', '.join(row['related_outside_selection']) or 'None declared'} |")
    output["DEPENDENCIES.md"] = (("\n".join(lines) + "\n").encode(), 0o644)
    lock = {"schema": 1, "upstream": provenance, "inputs": inputs(root), "source_files": originals,
            "files": {n: {"sha256": lib.sha(data), "mode": mode} for n, (data, mode) in sorted(output.items())}}
    output[lib.LOCK] = (lib.json_bytes(lock), 0o644)
    return output, lock


def changes(old, new):
    before, after = old.get("source_files", {}), new["source_files"]
    return {"added": sorted(after.keys() - before.keys()), "removed": sorted(before.keys() - after.keys()),
            "modified": sorted(k for k in before.keys() & after.keys() if before[k] != after[k])}


def save_report(path, report, root):
    if path:
        path = path.resolve()
        if path.is_relative_to(root) and not path.is_relative_to(root / ".sync"):
            raise ValueError("Reports inside this repository must go under ignored .sync/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(lib.json_bytes(report))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source", type=Path, help="Clean official upstream checkout; otherwise fetch into a temporary directory")
    parser.add_argument("--locked", action="store_true", help="Use the accepted upstream commit")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify", action="store_true", help="Verify locally without network")
    modes.add_argument("--check", action="store_true", help="Read-only regeneration comparison; exit 2 on drift")
    modes.add_argument("--check-upstream", action="store_true", help="Read-only selected-source comparison; exit 2 on upstream changes")
    modes.add_argument("--update-if-needed", action="store_true", help="Ignore upstream commits that do not change selected content or adapters")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    settings = config(root)
    old = verify(root, check_inputs=args.verify)
    if args.verify:
        return 0
    revision = old["upstream"]["commit"] if args.locked else None
    if args.locked and not revision:
        raise ValueError("Bootstrap has no single accepted upstream commit yet; run the first update")
    with tempfile.TemporaryDirectory(prefix="sf-core-upstream-") as temp:
        source = args.source.resolve() if args.source else lib.checkout(
            {"url": settings["repository"], "ref": settings["ref"]}, Path(temp) / "upstream", revision)
        if lib.git(source, "remote", "get-url", "origin").removesuffix(".git") != OFFICIAL.removesuffix(".git"):
            raise ValueError("Unexpected upstream origin")
        if lib.git(source, "status", "--porcelain", "--untracked-files=all"):
            raise ValueError("Upstream checkout must be clean")
        commit = lib.git(source, "rev-parse", "HEAD")
        if not re.fullmatch(r"[0-9a-f]{40}", commit) or (revision and revision != commit):
            raise ValueError("Source does not match the accepted commit")
        output, new = collect(root, source, settings, commit)
        delta = changes(old, new)
        selected_changed = any(delta.values())
        adapters_changed = old.get("inputs") != new["inputs"]
        report = {"previous_commit": old["upstream"]["commit"], "candidate_commit": commit,
                  "selected_changed": selected_changed, "adapters_changed": adapters_changed,
                  "source_changes": delta, "selected_skill_count": len(settings["skills"])}
        save_report(args.report, report, root)
        print(f"Official upstream {commit}; selected skills: {len(settings['skills'])}.")
        print(f"Selected source: {len(delta['added'])} added, {len(delta['modified'])} modified, {len(delta['removed'])} removed files.")
        if args.check_upstream:
            return 2 if selected_changed else 0
        if args.update_if_needed and not selected_changed and not adapters_changed:
            print("No selected content or adapter changes; accepted pin unchanged.")
            return 0
        if args.check:
            try:
                lib.apply(root, output, check=True)
            except ValueError as error:
                if str(error).startswith("Mirror out of date:"):
                    print(error)
                    return 2
                raise
        else:
            lib.apply(root, output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError, yaml.YAMLError) as error:
        raise SystemExit(str(error)) from error
