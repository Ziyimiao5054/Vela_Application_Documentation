from __future__ import annotations

import argparse
import hashlib
import os
import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    from markdownify import markdownify as to_markdown
except ImportError as exc:
    raise SystemExit(
        "缺少 markdownify 依赖，请先执行: python -m pip install -r scripts/requirements-docs.txt"
    ) from exc


DEFAULT_BASE_URL = "https://iot.mi.com/vela/quickapp/zh/"
INTERNAL_LANGS = {"zh", "en"}
REMOVE_SELECTORS = (
    "header.navbar",
    "aside.sidebar",
    "aside.theme-doc-sidebar-container",
    "div.page-nav",
    "div.toc",
    "div.theme-doc-breadcrumbs",
    "div.theme-doc-version-badge",
    "nav.pagination-nav",
    "footer",
)


def normalize_fragment(fragment: str) -> str:
    normalized = fragment
    if normalized.endswith(".html"):
        normalized = normalized[:-5]
    if normalized.startswith("_"):
        normalized = normalized[1:]
    return normalized


def resolve_language(base_url: str) -> str | None:
    parts = [part for part in urlparse(base_url).path.strip("/").split("/") if part]
    if parts and parts[-1] in INTERNAL_LANGS:
        return parts[-1]
    return None


class MarkdownScraper:
    def __init__(self, base_url: str, output_dir: Path) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.language = resolve_language(self.base_url)
        self.output_dir = Path(output_dir).resolve()
        if self.language:
            self.output_dir = self.output_dir / self.language
        self.output_root = self.output_dir.parent if self.language else self.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache",
            }
        )

    def split_internal_doc_path(self, path: str) -> tuple[str | None, str | None, bool, bool]:
        clean_path = urlparse(path).path if "://" in path else path
        stripped = clean_path.strip("/")
        parts = stripped.split("/") if stripped else []

        if len(parts) >= 3 and parts[:2] == ["vela", "quickapp"] and parts[2] in INTERNAL_LANGS:
            return parts[2], "/".join(parts[3:]), clean_path.endswith("/"), False

        if parts and parts[0] in INTERNAL_LANGS:
            return parts[0], "/".join(parts[1:]), clean_path.endswith("/"), True

        return None, None, False, False

    def get_output_md_path_for_url(self, url: str) -> Path | None:
        parsed = urlparse(url)
        language, relative_path, ends_with_slash, is_short_path = self.split_internal_doc_path(parsed.path)
        if not language:
            return None

        target_root = self.output_root / language
        relative_path = re.sub(r"\.(html|htm|php|aspx)$", "", relative_path or "").strip("/")

        if not relative_path:
            return target_root / "index.md"

        file_candidate = target_root / f"{relative_path}.md"
        index_candidate = target_root / relative_path / "index.md"

        if ends_with_slash:
            return index_candidate

        if parsed.path.endswith((".html", ".htm", ".php", ".aspx")):
            return file_candidate

        if is_short_path and "/" not in relative_path:
            return index_candidate

        if index_candidate.exists() and not file_candidate.exists():
            return index_candidate

        return file_candidate

    def convert_internal_link(self, href: str, page_url: str) -> str:
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            return href

        full_url = urljoin(page_url, href)
        parsed_full = urlparse(full_url)
        parsed_base = urlparse(self.base_url)

        if parsed_full.netloc != parsed_base.netloc:
            return href

        current_md_path = self.get_output_md_path_for_url(page_url)
        target_md_path = self.get_output_md_path_for_url(full_url)
        if not current_md_path or not target_md_path:
            return href

        relative_path = os.path.relpath(target_md_path, start=current_md_path.parent).replace("\\", "/")
        fragment = normalize_fragment(parsed_full.fragment)
        if fragment:
            relative_path = f"{relative_path}#{fragment}"
        return relative_path

    def extract_code_language(self, pre_tag) -> str:
        classes: list[str] = []
        if pre_tag.get("class"):
            classes.extend(pre_tag.get("class"))

        parent = pre_tag.find_parent("div")
        if parent and parent.get("class"):
            classes.extend(parent.get("class"))

        for class_name in classes:
            match = re.match(r"language-([A-Za-z0-9_-]+)", class_name)
            if match:
                return match.group(1)
        return ""

    def extract_code_blocks(self, root: BeautifulSoup) -> dict[str, str]:
        placeholders: dict[str, str] = {}
        for index, pre_tag in enumerate(root.find_all("pre")):
            language = self.extract_code_language(pre_tag)
            code = pre_tag.get_text("\n").strip("\n")
            fence = f"```{language}" if language else "```"
            placeholder = f"VELA_CODE_BLOCK_{index:04d}"
            placeholders[placeholder] = f"\n{fence}\n{code}\n```\n"

            wrapper = pre_tag
            parent = pre_tag.parent
            if parent and parent.name == "div" and any(
                class_name.startswith("language-") for class_name in parent.get("class", [])
            ):
                wrapper = parent
            wrapper.replace_with(f"\n\n{placeholder}\n\n")

        return placeholders

    def download_asset(self, url: str, asset_type: str = "images") -> str:
        asset_dir = self.output_dir / asset_type
        asset_dir.mkdir(parents=True, exist_ok=True)

        parsed = urlparse(url)
        raw_name = Path(unquote(parsed.path)).name
        suffix = Path(raw_name).suffix or ".bin"
        stem = Path(raw_name).stem or "asset"
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-.") or "asset"
        digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
        filename = f"{safe_stem}-{digest}{suffix}"
        save_path = asset_dir / filename

        if not save_path.exists():
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            save_path.write_bytes(response.content)

        return f"{asset_type}/{filename}"

    def clean_markdown(self, markdown: str) -> str:
        cleaned = markdown.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
        return cleaned.strip() + "\n"

    def convert_html_to_markdown(self, html: str, page_url: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        root = soup.select_one("main article") or soup.select_one("article") or soup.select_one("main") or soup

        for element in root.find_all(["script", "style", "iframe", "svg", "noscript"]):
            element.decompose()

        for selector in REMOVE_SELECTORS:
            for element in root.select(selector):
                element.decompose()

        for header in root.find_all(re.compile(r"^h[1-6]$")):
            for anchor in header.select("a.header-anchor"):
                anchor.decompose()

        placeholders = self.extract_code_blocks(root)

        for anchor in root.find_all("a", href=True):
            anchor["href"] = self.convert_internal_link(anchor["href"], page_url)

        for image in root.find_all("img", src=True):
            image_url = urljoin(page_url, image["src"])
            try:
                image["src"] = self.download_asset(image_url)
            except requests.RequestException:
                image["src"] = image_url

        markdown = to_markdown(str(root), heading_style="ATX")
        for placeholder, code_block in placeholders.items():
            markdown = markdown.replace(placeholder, code_block)

        return self.clean_markdown(markdown)

    def save_markdown_file(self, content: str, url: str) -> Path:
        output_path = self.get_output_md_path_for_url(url)
        if output_path is None:
            raise ValueError(f"无法根据 URL 推导输出路径: {url}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_content = f"<!-- Source: {url} -->\n\n{content}"

        def adjust_image_path(match: re.Match[str]) -> str:
            alt_text = match.group(1)
            target = match.group(2).strip()
            if urlparse(target).scheme:
                return match.group(0)

            absolute_image_path = self.output_dir / target
            if not absolute_image_path.exists():
                return match.group(0)

            relative_image_path = os.path.relpath(absolute_image_path, start=output_path.parent).replace("\\", "/")
            return f"![{alt_text}]({relative_image_path})"

        final_content = re.sub(r"!\[(.*?)\]\((.*?)\)", adjust_image_path, final_content)
        output_path.write_text(final_content, encoding="utf-8")
        return output_path

    def scrape_page(self, url: str) -> Path:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        final_url = response.url
        markdown = self.convert_html_to_markdown(response.text, final_url)
        return self.save_markdown_file(markdown, final_url)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="定向抓取并转换单个 QuickApp 文档页面。")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="文档站基础 URL。")
    parser.add_argument("--output-dir", type=Path, default=Path("docs"), help="输出目录。")
    parser.add_argument("--start-url", help="兼容旧调用，等同于 --single-url。")
    parser.add_argument("--single-url", help="只抓取一个指定 URL。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    page_url = args.single_url or args.start_url
    if not page_url:
        raise SystemExit("请通过 --single-url 指定要抓取的页面。")

    scraper = MarkdownScraper(base_url=args.base_url, output_dir=args.output_dir)
    saved_path = scraper.scrape_page(page_url)
    print(f"Saved: {saved_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
