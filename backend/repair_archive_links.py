"""Repair obvious broken links in generated HTML archives."""
import re
from pathlib import Path


def repair_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    updated = text

    # Replace empty hrefs for HN links with inactive marker.
    updated = re.sub(
        r'<a[^>]*href=""[^>]*class="hn-link"[^>]*>\s*DISCUSS ON HN\s*</a>',
        '<span class="hn-link" aria-disabled="true">NO HN THREAD</span>',
        updated,
        flags=re.IGNORECASE,
    )
    updated = re.sub(
        r'<a[^>]*href=""[^>]*>\s*READ FULL DISCUSSION\s*→\s*</a>',
        '<span class="hn-link" aria-disabled="true">NO HN THREAD</span>',
        updated,
        flags=re.IGNORECASE,
    )
    updated = updated.replace(
        '<a href="" target="_blank">READ FULL DISCUSSION →</a>',
        '<span class="hn-link" aria-disabled="true">NO HN THREAD</span>',
    )

    # Strip accidental javascript: void pseudo-links in article metadata.
    updated = updated.replace('href="javascript:void(0)" target="_blank"', 'href="#"')

    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def repair_tree(root: Path):
    changed = 0
    for html_path in root.rglob("*.html"):
        if repair_file(html_path):
            changed += 1
    return changed


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    targets = [repo_root / "output", repo_root / "docs"]
    total = 0
    for t in targets:
        if t.exists():
            total += repair_tree(t)
    print(f"Repaired {total} html files")
