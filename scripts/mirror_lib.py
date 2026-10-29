#!/usr/bin/env python3
"""Shared conversion and file-ownership helpers for sf-core-skills."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
LOCK = "upstream.lock.json"
NOTICE = "<!-- Modified for GitHub Copilot by sf-core-skills; upstream copyright and license retained. -->"
BRIDGE = """> **Copilot compatibility:** Resolve resources relative to this skill's installed
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
"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def safe_path(root, relative):
    p = PurePosixPath(relative)
    if p.is_absolute() or not p.parts or any(x in ("..", ".git") for x in p.parts):
        raise ValueError(f"Unsafe managed path: {relative}")
    result = root.joinpath(*p.parts)
    if any(x.is_symlink() for x in (result, *result.parents)):
        raise ValueError(f"Symlink in managed path: {relative}")
    return result


def split_skill(text):
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)(.*)\Z", text, re.S)
    if not match:
        raise ValueError("Missing YAML frontmatter")
    header = yaml.safe_load(match[1])
    if not isinstance(header, dict):
        raise ValueError("Frontmatter must be a mapping")
    return header, match[2]


def adapt_skill(text, directory):
    header, body = split_skill(text)
    if header.get("name") != directory or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", directory):
        raise ValueError(f"Skill name/directory mismatch: {directory}")
    if not isinstance(header.get("description"), str) or not header["description"].strip():
        raise ValueError(f"Missing skill description: {directory}")
    # Claude tool allowlists are not portable Copilot permissions. Preserve dependency
    # metadata for discovery, but only emit common Agent Skills frontmatter fields.
    common = {k: v for k, v in header.items()
              if k in {"name", "description", "license", "compatibility", "metadata"}}
    rendered = "---\n" + yaml.safe_dump(common, sort_keys=False, allow_unicode=True) + "---\n\n"
    return rendered + NOTICE + "\n\n" + BRIDGE + "\n" + body.lstrip(), header


def verify(root):
    lock = json.loads((root / LOCK).read_text())
    for name, expected in lock["files"].items():
        path = safe_path(root, name)
        if not path.is_file() or sha(path.read_bytes()) != expected["sha256"]:
            raise ValueError(f"Managed file changed or missing: {name}")
        if os.name != "nt" and bool(path.stat().st_mode & 0o111) != bool(expected["mode"] & 0o111):
            raise ValueError(f"Executable mode changed: {name}")
    print(f"Verified {len(lock['files'])} managed files.")


def apply(root, output, check=False, lock_name=LOCK):
    lock_path = safe_path(root, lock_name)
    old = json.loads(lock_path.read_text())["files"] if lock_path.exists() else {}
    # Preflight every path before writing anything. Local skills outside the
    # managed inventory are preserved, and collisions require explicit resolution.
    for name in sorted(set(old) | set(output)):
        path = safe_path(root, name)
        if path.exists() and not path.is_file():
            raise ValueError(f"Managed path is not a file: {name}")
        if name in old:
            if not path.exists() or sha(path.read_bytes()) != old[name]["sha256"]:
                raise ValueError(f"Local modification to managed file: {name}; move changes to adapters first")
            if os.name != "nt" and bool(path.stat().st_mode & 0o111) != bool(old[name]["mode"] & 0o111):
                raise ValueError(f"Local executable mode modification: {name}")
        elif name != lock_name and path.exists():
            raise ValueError(f"Unmanaged file collision: {name}")
    changed = [name for name, (data, mode) in output.items()
               if not (root / name).is_file() or (root / name).read_bytes() != data
               or (os.name != "nt" and bool((root / name).stat().st_mode & 0o111) != bool(mode & 0o111))]
    removed = sorted(set(old) - set(output))
    if check and (changed or removed):
        raise ValueError(f"Mirror out of date: {len(changed)} changed, {len(removed)} removed files")
    if not check:
        for name in changed:
            data, mode = output[name]
            path = safe_path(root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
                temp.write(data)
                temp_name = temp.name
            os.chmod(temp_name, mode)
            os.replace(temp_name, path)
        for name in removed:
            safe_path(root, name).unlink()
    print(f"Mirror: {len(changed)} changed, {len(removed)} removed files.")


def checkout(config, destination, revision=None):
    # macOS exposes temporary folders through /var -> /private/var. Canonicalize
    # the checkout root while still rejecting symlinks inside managed content.
    destination = destination.resolve()
    subprocess.run(["git", "init", "-q", str(destination)], check=True)
    subprocess.run(["git", "-C", str(destination), "remote", "add", "origin", config["url"]], check=True)
    ref = revision or config["ref"]
    if ref.startswith("-"):
        raise ValueError("Invalid upstream ref")
    subprocess.run(["git", "-C", str(destination), "fetch", "--depth=1", "origin", ref], check=True)
    subprocess.run(["git", "-C", str(destination), "checkout", "--detach", "-q", "FETCH_HEAD"], check=True)
    return destination
