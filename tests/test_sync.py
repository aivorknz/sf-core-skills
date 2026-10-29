import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mirror_lib as lib
import sync
import install


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root, self.source = self.base / "mirror", self.base / "source"
        self.root.mkdir()
        self.source.mkdir()
        (self.root / "adapters/notes").mkdir(parents=True)
        (self.root / "adapters/copilot.md").write_text("> Maintained Copilot adaptation\n")
        (self.root / "adapters/replacements.json").write_text("[]\n")
        (self.root / "LICENSE").write_text("fixture license")
        (self.root / "NOTICE").write_text("fixture attribution")
        (self.root / "upstream.json").write_text(json.dumps({"repository": sync.OFFICIAL, "ref": "main", "skills": ["alpha"]}))
        (self.root / "upstream.lock.json").write_text(json.dumps({"schema": 1, "upstream": {"commit": None}, "files": {}}))
        folder = self.source / "skills/alpha"
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text("---\nname: alpha\ndescription: Test skill\nallowed-tools: Bash\nmetadata:\n  mcpTools:\n    example-service:\n      tools: [test_tool]\n---\n\nOriginal body.\n")
        (folder / "helper.sh").write_text("#!/bin/sh\nexit 0\n")
        (folder / "helper.sh").chmod(0o755)
        (self.source / "LICENSE.txt").write_text("fixture license")
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.test")
        self.git("remote", "add", "origin", sync.OFFICIAL)
        self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args], stderr=subprocess.STDOUT, text=True).strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")

    def run_sync(self, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return sync.main(["--root", str(self.root), "--source", str(self.source), *args])

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_initial_update_preserves_resources_modes_and_mcp(self):
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual(self.run_sync("--locked", "--check"), 0)
        self.assertEqual(self.run_sync("--verify"), 0)
        text = (self.root / "alpha/SKILL.md").read_text()
        self.assertIn("Maintained Copilot adaptation", text)
        self.assertTrue(text.endswith("Original body.\n"))
        self.assertNotIn("allowed-tools:", text)
        self.assertTrue((self.root / "alpha/helper.sh").stat().st_mode & 0o111)
        self.assertEqual(json.loads((self.root / "dependency-audit.json").read_text())["skills_with_declared_mcp"], 1)

    def test_check_detects_new_commit_without_writes_then_preserves_adapter(self):
        self.run_sync()
        before = self.snapshot()
        p = self.source / "skills/alpha/SKILL.md"
        p.write_text(p.read_text().replace("Original body.", "New upstream body."))
        self.commit()
        self.assertEqual(self.run_sync("--check-upstream"), 2)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.run_sync(), 0)
        self.assertIn("Maintained Copilot adaptation", (self.root / "alpha/SKILL.md").read_text())
        self.assertIn("New upstream body.", (self.root / "alpha/SKILL.md").read_text())

    def test_local_edit_blocks_update_before_any_write(self):
        self.run_sync()
        (self.root / "alpha/helper.sh").write_text("local modification")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "changed or missing"):
            self.run_sync()
        self.assertEqual(self.snapshot(), before)

    def test_exact_replacement_and_conflict_protection(self):
        rules = [{"skill": "alpha", "path": "SKILL.md", "old": "Original body.", "new": "Reviewed local wording."}]
        (self.root / "adapters/replacements.json").write_text(json.dumps(rules))
        self.run_sync()
        self.assertIn("Reviewed local wording", (self.root / "alpha/SKILL.md").read_text())
        p = self.source / "skills/alpha/SKILL.md"
        p.write_text(p.read_text().replace("Original body.", "Changed upstream wording."))
        self.commit()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Adapter conflict"):
            self.run_sync()
        self.assertEqual(self.snapshot(), before)

    def test_source_resource_add_remove_and_unrelated_file_preservation(self):
        self.run_sync()
        (self.root / "alpha/local-notes.md").write_text("keep this")
        (self.source / "skills/alpha/helper.sh").unlink()
        (self.source / "skills/alpha/new.txt").write_text("new resource")
        self.commit()
        self.run_sync()
        self.assertFalse((self.root / "alpha/helper.sh").exists())
        self.assertEqual((self.root / "alpha/new.txt").read_text(), "new resource")
        self.assertEqual((self.root / "alpha/local-notes.md").read_text(), "keep this")

    def test_unrelated_upstream_commit_is_quiet(self):
        self.run_sync()
        before = self.snapshot()
        (self.source / "unselected.txt").write_text("unrelated change")
        self.commit()
        self.assertEqual(self.run_sync("--check-upstream"), 0)
        self.assertEqual(self.run_sync("--update-if-needed"), 0)
        self.assertEqual(self.snapshot(), before)

    def test_changed_adapter_is_regenerated(self):
        self.run_sync()
        (self.root / "adapters/copilot.md").write_text("> New reviewed adaptation\n")
        with self.assertRaisesRegex(ValueError, "adapters changed"):
            self.run_sync("--verify")
        self.assertEqual(self.run_sync("--update-if-needed"), 0)
        self.assertIn("New reviewed adaptation", (self.root / "alpha/SKILL.md").read_text())

    def test_missing_skill_and_symlink_fail_without_writes(self):
        self.run_sync()
        before = self.snapshot()
        p = self.source / "skills/alpha/SKILL.md"
        original = p.read_text()
        p.unlink()
        self.commit()
        with self.assertRaisesRegex(ValueError, "removed/renamed"):
            self.run_sync()
        p.write_text(original)
        (self.source / "skills/alpha/link").symlink_to(self.source / "LICENSE.txt")
        self.commit()
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.run_sync()
        self.assertEqual(self.snapshot(), before)

    def test_origin_dirty_checkout_and_path_checks(self):
        self.git("remote", "set-url", "origin", "https://example.test/fork.git")
        with self.assertRaisesRegex(ValueError, "origin"):
            self.run_sync()
        self.git("remote", "set-url", "origin", sync.OFFICIAL)
        (self.source / "dirty.txt").write_text("not committed")
        with self.assertRaisesRegex(ValueError, "clean"):
            self.run_sync()
        (self.source / "dirty.txt").unlink()
        data = json.loads((self.root / "upstream.json").read_text())
        data["skills"] = ["../escape"]
        (self.root / "upstream.json").write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            self.run_sync()

    def test_executable_edits_and_unmanaged_collisions_are_protected(self):
        self.run_sync()
        p = self.root / "alpha/helper.sh"
        p.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "mode changed"):
            self.run_sync()
        p.chmod(0o755)
        (self.root / "alpha/new.txt").write_text("local")
        (self.source / "skills/alpha/new.txt").write_text("upstream")
        self.commit()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "collision"):
            self.run_sync()
        self.assertEqual(self.snapshot(), before)

    def test_install_updates_preserves_other_skills_and_protects_edits(self):
        self.run_sync()
        target = self.base / "consumer"
        (target / ".github/skills/other").mkdir(parents=True)
        (target / ".github/skills/other/SKILL.md").write_text("keep")
        install.install(self.root, target)
        install.install(self.root, target, check=True)
        self.assertEqual((target / ".github/skills/other/SKILL.md").read_text(), "keep")
        (target / ".github/skills/alpha/SKILL.md").write_text("project edit")
        with self.assertRaisesRegex(ValueError, "Local modification"):
            install.install(self.root, target)

    def test_report_cannot_overwrite_repository_source(self):
        with self.assertRaisesRegex(ValueError, "Reports"):
            self.run_sync("--check-upstream", "--report", str(self.root / "README.md"))
        self.assertFalse((self.root / "README.md").exists())

    def test_temporary_parent_symlink_is_canonicalized(self):
        canonical = self.base / "canonical-temp"
        canonical.mkdir()
        alias = self.base / "temp-alias"
        alias.symlink_to(canonical, target_is_directory=True)
        checkout = lib.checkout({"url": str(self.source), "ref": "HEAD"}, alias / "upstream")
        self.assertEqual(checkout, canonical / "upstream")
        self.assertTrue(lib.safe_path(checkout, "skills/alpha/SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
