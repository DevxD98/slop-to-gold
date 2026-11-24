#!/usr/bin/env python3
"""First-pass slop scan: counts common anti-pattern signals per file.

Usage: python3 scan.py <repo-path> [--top N]
"""
import hashlib
import os
import re
import sys
from collections import Counter

SKIP = {".git", "node_modules", "dist", "build", ".next", "venv", ".venv", "__pycache__", "target"}
EXT = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java", ".swift"}

PATTERNS = {
    "timer-patch": re.compile(r"\b(setTimeout|requestAnimationFrame|requestIdleCallback)\s*\("),
    "useEffect": re.compile(r"\buseEffect\s*\("),
    "ts-escape": re.compile(r"@ts-ignore|@ts-expect-error|\bas any\b|: any\b"),
    "lint-disable": re.compile(r"eslint-disable|noqa|nolint|# type: ignore"),
    "todo-hack": re.compile(r"\b(TODO|FIXME|HACK|XXX|workaround)\b", re.I),
    "empty-catch": re.compile(r"catch\s*(\([^)]*\))?\s*\{\s*\}|except[^:\n]*:\s*pass"),
}
COMMENT = re.compile(r"^\s*(//|#|\*|/\*)")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    top = 10
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])
        args = [a for a in args if a != str(top)]
    if not args:
        sys.exit("usage: scan.py <repo-path> [--top N]")
    root = args[0]
    totals, per_file = Counter(), {}
    code_lines = comment_lines = 0
    seen, dupes = {}, []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP]
        for fn in fns:
            if os.path.splitext(fn)[1] not in EXT:
                continue
            path = os.path.join(dp, fn)
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            digest = hashlib.md5(text.encode("utf-8", "ignore")).hexdigest()
            if digest in seen:
                dupes.append((path, seen[digest]))
                continue
            seen[digest] = path
            counts = Counter()
            for name, rx in PATTERNS.items():
                n = len(rx.findall(text))
                if n:
                    counts[name] = n
                    totals[name] += n
            for line in text.splitlines():
                if line.strip():
                    code_lines += 1
                    if COMMENT.match(line):
                        comment_lines += 1
            if counts:
                per_file[path] = counts
    print(f"scanned: {root}")
    print(f"comment ratio: {comment_lines}/{code_lines} lines "
          f"({100 * comment_lines / max(code_lines, 1):.0f}%)")
    if dupes:
        print(f"skipped {len(dupes)} byte-identical duplicate files (copied dirs?), e.g.:")
        for d, orig in dupes[:3]:
            print(f"  {os.path.relpath(d, root)} == {os.path.relpath(orig, root)}")
    print("\npattern totals:")
    for name, n in totals.most_common():
        print(f"  {name:14} {n}")
    print(f"\ntop {top} files by signal count:")
    ranked = sorted(per_file.items(), key=lambda kv: -sum(kv[1].values()))[:top]
    for path, c in ranked:
        detail = ", ".join(f"{k}={v}" for k, v in c.most_common())
        print(f"  {sum(c.values()):4}  {os.path.relpath(path, root)}  ({detail})")


if __name__ == "__main__":
    main()
