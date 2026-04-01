from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCS_PY = REPO_ROOT / "scripts" / "docs.py"
DEFAULT_TARGET_ROOT = REPO_ROOT / "docs-quickapp"
DEFAULT_DOCS_PYTHON = Path(sys.executable)

INTERNAL_ABSOLUTE_PREFIX = "https://iot.mi.com/vela/quickapp/zh/"

RENAME_MAP = {
    Path("guide/framework/template/Props.md"): Path("guide/framework/template/props.md"),
    Path("tools/project/creat-project.md"): Path("tools/project/create-project.md"),
}

CONTENT_REWRITES = {
    "features/network/interconnect.md": [
        ("### connect.diagnosis(OBJECT)", "### connect.diagnosis(OBJECT) {#connect-diagnosis-object}"),
    ],
    "guide/framework/style/page-style-and-layout.md": [
        ("## 引入 less/scss 预编译", "## 引入 less/scss 预编译 {#引入-less-scss-预编译}"),
    ],
    "guide/framework/script/global-data-method.md": [
        ("### this.$watch", "### this.$watch {#thiswatch}"),
    ],
    "guide/framework/template/props.md": [
        ("../script/global-data-method.md#this.$watch", "../script/global-data-method.md#thiswatch"),
    ],
}


def normalize_fragment(fragment: str) -> str:
    normalized = fragment
    if normalized.endswith(".html"):
        normalized = normalized[:-5]
    if normalized.startswith("_"):
        normalized = normalized[1:]
    return normalized


def strip_source_comment(content: str) -> str:
    return re.sub(r"^<!--\s*(?:Source|源地址):[^>]+-->\s*\n*", "", content, count=1)


def rewrite_open_window_links(content: str) -> str:
    return re.sub(
        r"<(https?://[^>]+)>\[\s*\(opens new window\)\]\(([^)]+)\)",
        lambda match: f"[{match.group(1)}]({match.group(2)})",
        content,
    )


def normalize_fence_boundaries(content: str) -> str:
    content = re.sub(r"([^\n`])```([A-Za-z0-9_-]+)", r"\1\n```\2", content)
    content = re.sub(r"([^\n`])\s+```([A-Za-z0-9_-]+)", r"\1\n```\2", content)
    content = re.sub(r"```\s+```([A-Za-z0-9_-]+)", r"```\n\n```\1", content)
    return content


def infer_raw_block_language(line: str) -> str:
    lowered = line.lower()
    if lowered.startswith("<script"):
        return "javascript"
    if lowered.startswith("<style"):
        return "css"
    return "html"


def fence_raw_tag_blocks(segment: str) -> str:
    lines = segment.splitlines()
    output: list[str] = []
    index = 0

    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("<") and not stripped.startswith(("<http", "<https")):
            language = infer_raw_block_language(stripped)
            block_lines = [lines[index]]
            index += 1

            while index < len(lines):
                current = lines[index]
                current_stripped = current.strip()
                if current_stripped == "":
                    break
                block_lines.append(current)
                index += 1
                if current_stripped.startswith(("</script", "</style", "</template")):
                    break

            output.append(f"```{language}\n" + "\n".join(block_lines) + "\n```")
            continue

        output.append(lines[index])
        index += 1

    return "\n".join(output)


def escape_special_chars_outside_fences(content: str) -> str:
    parts = re.split(r"(```[\s\S]*?```)", content)
    escaped_parts: list[str] = []
    for index, part in enumerate(parts):
        if index % 2 == 1:
            escaped_parts.append(part)
            continue

        trailing_newlines = re.search(r"\n+$", part)
        suffix = trailing_newlines.group(0) if trailing_newlines else ""
        core = part[:-len(suffix)] if suffix else part

        fenced = fence_raw_tag_blocks(core)
        
        # 保护单反引号和它内部自动生成的三反引号，避免行内代码的 < 和 > 以及 {} 被转义
        fenced_parts = re.split(r"(```[\s\S]*?```|`[^`]*`)", fenced)
        escaped_fenced_parts: list[str] = []
        for j, fpart in enumerate(fenced_parts):
            if j % 2 == 1:
                escaped_fenced_parts.append(fpart)
            else:
                fpart = fpart.replace("{", "&#123;").replace("}", "&#125;")
                fpart = fpart.replace("<", "&lt;").replace(">", "&gt;")
                escaped_fenced_parts.append(fpart)
        fenced = "".join(escaped_fenced_parts)
        
        escaped_parts.append(fenced + suffix)

    return "".join(escaped_parts)


def restore_external_targets(content: str) -> str:
    return re.sub(
        r"\(&lt;(https?://[^&]+?)&gt;(\s+\"[^\"]*\")?\)",
        lambda match: f"({match.group(1)}{match.group(2) or ''})",
        content,
    )


def apply_rename_map(
    current_file: Path,
    target_path: str,
    old_to_new: dict[Path, Path],
) -> str:
    resolved_target = (current_file.parent / target_path).resolve()
    for old_path, new_path in old_to_new.items():
        if resolved_target == old_path.resolve():
            return Path(os.path.relpath(new_path, start=current_file.parent)).as_posix()
    return target_path


def normalize_target(
    raw_target: str,
    current_file: Path,
    target_root: Path,
    old_to_new: dict[Path, Path],
) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]

    if not target or target.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return target

    if target.startswith(INTERNAL_ABSOLUTE_PREFIX):
        target = target[len(INTERNAL_ABSOLUTE_PREFIX):]

    parsed = urlparse(target)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return target
    if parsed.scheme in {"http", "https"}:
        return target

    path = parsed.path.replace("\\", "/")
    fragment = normalize_fragment(parsed.fragment)

    if path.startswith("/vela/quickapp/zh/"):
        path = path[len("/vela/quickapp/zh/"):]
    elif path == "/vela/quickapp/zh":
        path = "index.md"
    elif path.startswith("/"):
        path = path.lstrip("/")

    if path.endswith("/"):
        path = f"{path}index.md"
    elif path.endswith(".html"):
        path = f"{path[:-5]}.md"

    current_rel = current_file.relative_to(target_root).as_posix()
    if current_rel == "guide/index.md" and path == "multi-screens/simulator.md":
        path = "../tools/debug/multi-screens.md"

    if path:
        path = apply_rename_map(current_file, path, old_to_new)

    if fragment:
        return f"{path}#{fragment}"
    return path


def normalize_markdown_file(file_path: Path, target_root: Path, old_to_new: dict[Path, Path]) -> None:
    content = file_path.read_text(encoding="utf-8")
    content = strip_source_comment(content)
    content = rewrite_open_window_links(content)
    content = normalize_fence_boundaries(content)

    def replace_target(match: re.Match[str]) -> str:
        prefix = match.group(1)
        raw_target = match.group(2)
        suffix = match.group(3)
        normalized_target = normalize_target(raw_target, file_path, target_root, old_to_new)
        return f"{prefix}{normalized_target}{suffix}"

    content = re.sub(r"(!?\[[^\]]*\]\()([^)]+)(\))", replace_target, content)
    content = escape_special_chars_outside_fences(content)
    content = restore_external_targets(content)
    relative_path = file_path.relative_to(target_root).as_posix()
    for old_value, new_value in CONTENT_REWRITES.get(relative_path, []):
        content = content.replace(old_value, new_value)
    file_path.write_text(content, encoding="utf-8")


def merge_directory(source: Path, destination: Path) -> None:
    if not source.exists():
        return

    destination.mkdir(parents=True, exist_ok=True)
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        target = destination / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def find_invalid_image_references(target_root: Path) -> set[str]:
    invalid_refs: set[str] = set()
    for image_path in (target_root / "images").glob("*"):
        raw = image_path.read_bytes()[:32]
        if raw.startswith((b"<!DOCTYPE html", b"<html", b"\r\n<html", b"\n<html")):
            invalid_refs.add(image_path.name)
    return invalid_refs


def remove_invalid_image_references(target_root: Path) -> None:
    invalid_names = find_invalid_image_references(target_root)
    if not invalid_names:
        return

    image_pattern = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

    for markdown_file in target_root.rglob("*.md"):
        content = markdown_file.read_text(encoding="utf-8")

        def replace_invalid_image(match: re.Match[str]) -> str:
            target = match.group(1).strip("<>")
            if Path(target).name in invalid_names:
                return ""
            return match.group(0)

        updated = image_pattern.sub(replace_invalid_image, content)
        markdown_file.write_text(updated, encoding="utf-8")

    for image_name in invalid_names:
        (target_root / "images" / image_name).unlink(missing_ok=True)


def resolve_docs_python(docs_python: Path) -> Path:
    if docs_python.exists():
        return docs_python
    return Path(sys.executable)


def rescrape_single_page(docs_python: Path, docs_py: Path, target_root: Path) -> None:
    base_url = "https://iot.mi.com/vela/quickapp/zh/"
    single_url = "https://iot.mi.com/vela/quickapp/zh/guide/start.html"

    with tempfile.TemporaryDirectory(prefix="quickapp-rescrape-") as temp_dir:
        temp_root = Path(temp_dir)
        command = [
            str(resolve_docs_python(docs_python)),
            str(docs_py),
            "--base-url",
            base_url,
            "--output-dir",
            str(temp_root),
            "--single-url",
            single_url,
        ]
        subprocess.run(command, check=True)

        scraped_root = temp_root / "zh"
        scraped_page = scraped_root / "guide" / "start.md"
        if not scraped_page.exists():
            raise FileNotFoundError(f"定向补抓未产出目标页面: {scraped_page}")

        destination_page = target_root / "guide" / "start.md"
        destination_page.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(scraped_page, destination_page)
        merge_directory(scraped_root / "images", target_root / "images")


def rename_inconsistent_files(target_root: Path) -> dict[Path, Path]:
    old_to_new: dict[Path, Path] = {}
    for old_rel, new_rel in RENAME_MAP.items():
        old_path = target_root / old_rel
        new_path = target_root / new_rel
        if not old_path.exists():
            continue

        new_path.parent.mkdir(parents=True, exist_ok=True)
        if old_path.name.lower() == new_path.name.lower():
            temp_path = old_path.with_name(f"{old_path.stem}.__rename__.md")
            old_path.rename(temp_path)
            temp_path.rename(new_path)
        else:
            if new_path.exists():
                new_path.unlink()
            old_path.rename(new_path)
        old_to_new[old_path.resolve()] = new_path.resolve()

    return old_to_new


def remove_bad_duplicate_page(target_root: Path) -> None:
    duplicate_page = target_root / "guide" / "start" / "index.md"
    if duplicate_page.exists():
        duplicate_page.unlink()


def import_quickapp_docs(
    source_root: Path | None,
    docs_python: Path,
    docs_py: Path,
    target_root: Path,
) -> None:
    if source_root is None:
        if not target_root.exists():
            raise FileNotFoundError(f"未找到现有 QuickApp 文档目录: {target_root}")
    else:
        if not source_root.exists():
            raise FileNotFoundError(f"未找到 QuickApp 源文档目录: {source_root}")

        source_root = source_root.resolve()
        if source_root != target_root.resolve():
            if target_root.exists():
                shutil.rmtree(target_root)
            shutil.copytree(source_root, target_root)
        elif not target_root.exists():
            raise FileNotFoundError(f"目标文档目录不存在: {target_root}")

    rescrape_single_page(docs_python, docs_py, target_root)
    remove_bad_duplicate_page(target_root)
    old_to_new = rename_inconsistent_files(target_root)

    for markdown_file in target_root.rglob("*.md"):
        normalize_markdown_file(markdown_file, target_root, old_to_new)
    remove_invalid_image_references(target_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导入并清洗 VelaOS QuickApp 中文文档。")
    parser.add_argument(
        "--source-root",
        type=Path,
        help="可选：上游 QuickApp 中文 docs 根目录。未提供时直接清洗 target-root。",
    )
    parser.add_argument(
        "--docs-python",
        type=Path,
        default=DEFAULT_DOCS_PYTHON,
        help="运行本地 docs.py 的 Python 可执行文件，默认使用当前 Python。",
    )
    parser.add_argument(
        "--docs-py",
        type=Path,
        default=DEFAULT_DOCS_PY,
        help="本项目内的定向补抓脚本路径。",
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=DEFAULT_TARGET_ROOT,
        help="当前项目中的 QuickApp 文档目录。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.docs_py.exists():
        raise FileNotFoundError(f"未找到定向补抓脚本: {args.docs_py}")

    import_quickapp_docs(
        source_root=args.source_root.resolve() if args.source_root else None,
        docs_python=args.docs_python.resolve(),
        docs_py=args.docs_py.resolve(),
        target_root=args.target_root.resolve(),
    )
    print(f"QuickApp 文档已更新到: {args.target_root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
