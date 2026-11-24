#!/usr/bin/env python3
"""Static checks on the skill package: frontmatter, size budget, links.

Run: python3 tests/test_static.py
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md must start with a --- frontmatter block"
    out = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out, text[m.end():]


class StaticChecks(unittest.TestCase):
    def setUp(self):
        self.text = read("SKILL.md")
        self.fm, self.body = frontmatter(self.text)

    def test_name_matches_folder_rules(self):
        self.assertEqual(self.fm.get("name"), "slop-to-gold")
        self.assertRegex(self.fm["name"], r"^[a-z0-9-]{1,64}$")

    def test_description_is_trigger_only(self):
        d = self.fm.get("description", "")
        self.assertTrue(d.startswith("Use when"), "description must start with 'Use when'")
        self.assertLessEqual(len(d), 1024)
        # A workflow summary in the description makes agents skip the body.
        for word in ("then", "step", "first,", "runs", "writes"):
            self.assertNotIn(f" {word} ", f" {d.lower()} ", f"description reads like a workflow: '{word}'")

    def test_body_under_500_words(self):
        self.assertLess(len(self.body.split()), 500)

    def test_referenced_files_exist(self):
        refs = set(re.findall(r"`((?:references|scripts)/[\w./-]+)`", self.text))
        self.assertTrue(refs, "SKILL.md should route to reference files")
        for rel in refs:
            self.assertTrue(os.path.isfile(os.path.join(ROOT, rel)), f"missing {rel}")

    def test_reference_files_cite_existing_scripts(self):
        for ref in os.listdir(os.path.join(ROOT, "references")):
            text = read(os.path.join("references", ref))
            for rel in re.findall(r"(scripts/[\w.-]+)", text):
                self.assertTrue(os.path.isfile(os.path.join(ROOT, rel)), f"{ref} cites missing {rel}")

    def test_no_personal_paths(self):
        for dp, dns, fns in os.walk(ROOT):
            dns[:] = [d for d in dns if d not in {".git", "results", "node_modules"}]
            for fn in fns:
                if fn.endswith((".md", ".py", ".sh", ".json")) and fn != "test_static.py":
                    with open(os.path.join(dp, fn), encoding="utf-8", errors="ignore") as f:
                        self.assertNotRegex(f.read(), r"/Users/[a-z]", f"personal path in {fn}")


if __name__ == "__main__":
    sys.exit(unittest.main(verbosity=2))
