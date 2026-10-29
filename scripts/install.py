#!/usr/bin/env python3
"""Install verified skills into a consumer project without overwriting local edits."""
import argparse
import json
from pathlib import Path

import mirror_lib as lib
import sync


def install(root, target, check=False):
    lock = sync.verify(root)
    names = sync.config(root)["skills"]
    output = {}
    for name, record in lock["files"].items():
        if name.split("/", 1)[0] in names:
            output["skills/" + name] = (lib.safe_path(root, name).read_bytes(), record["mode"])
    for name in ("LICENSE", "NOTICE"):
        output["sf-core-skills-licenses/" + name] = (lib.safe_path(root, name).read_bytes(), 0o644)
    state = {"schema": 1, "upstream": lock["upstream"], "files": {
        n: {"sha256": lib.sha(data), "mode": mode} for n, (data, mode) in sorted(output.items())}}
    output["sf-core-skills.lock.json"] = (lib.json_bytes(state), 0o644)
    lib.apply(target / ".github", output, check=check, lock_name="sf-core-skills.lock.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = args.target.resolve()
    if not target.is_dir() or target == sync.ROOT:
        raise ValueError("Choose a different existing consumer-project directory")
    install(sync.ROOT, target, args.check)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from error
