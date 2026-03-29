from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.core.config import get_settings


@dataclass
class WebSnapshotResult:
    url: str
    title: str
    text: str
    output_path: Path


class WebDocumentFetcher:
    USER_AGENT = (
        "Mozilla/5.0 (compatible; PortfolioRAGBot/1.0; +https://example.local) "
        "Python requests"
    )
    BLOCK_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "form",
        "button",
        "input",
        "select",
        "textarea",
        "iframe",
        "footer",
    }
    NOISE_PATTERNS = [
        re.compile(pattern)
        for pattern in [
            r"^홈$",
            r"^메뉴$",
            r"^검색$",
            r"^닫기$",
            r"^공유하기$",
            r"^프린트하기$",
            r"^목록$",
            r"^이전$",
            r"^다음$",
            r"^맨위로$",
            r"^바로가기$",
            r"^sns 공유$",
            r"^만족도 조사$",
            r"^개인정보처리방침$",
        ]
    ]

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def snapshot_url_to_text(
        self,
        url: str,
        title_hint: str | None = None,
        filename_hint: str | None = None,
        output_dir: Path | None = None,
    ) -> Path:
        snapshot = self.fetch(url=url, title_hint=title_hint, filename_hint=filename_hint, output_dir=output_dir)
        return snapshot.output_path

    def fetch(
        self,
        url: str,
        title_hint: str | None = None,
        filename_hint: str | None = None,
        output_dir: Path | None = None,
    ) -> WebSnapshotResult:
        response = requests.get(
            url,
            timeout=self.timeout_seconds,
            headers={"User-Agent": self.USER_AGENT},
        )
        response.raise_for_status()

        title, text = self.extract_text(response.text)
        if title_hint:
            title = title_hint.strip()
        if not text.strip():
            raise ValueError("URL에서 적재할 본문 텍스트를 추출하지 못했습니다.")

        target_dir = output_dir or (Path(get_settings().raw_dir) / "web_imports")
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = self._build_filename(url=url, title=title, filename_hint=filename_hint)
        target_path = target_dir / filename

        fetched_at = datetime.now(timezone.utc).isoformat()
        snapshot_text = (
            f"[source_url] {url}\n"
            f"[fetched_at_utc] {fetched_at}\n"
            f"[source_title] {title}\n\n"
            f"{text.strip()}\n"
        )
        target_path.write_text(snapshot_text, encoding="utf-8")
        return WebSnapshotResult(url=url, title=title, text=text, output_path=target_path)

    def extract_text(self, html: str) -> tuple[str, str]:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup.find_all(self.BLOCK_TAGS):
            tag.decompose()

        title = self._extract_title(soup)
        content_root = soup.find("main") or soup.find("article") or soup.body or soup
        raw_lines = content_root.get_text("\n").splitlines()
        cleaned_lines = self._clean_lines(raw_lines)

        if len(cleaned_lines) < 3:
            fallback_lines = self._clean_lines(soup.get_text("\n").splitlines())
            if len(fallback_lines) > len(cleaned_lines):
                cleaned_lines = fallback_lines

        text = "\n".join(cleaned_lines)
        return title, text

    def _extract_title(self, soup: BeautifulSoup) -> str:
        for selector in ["h1", "h2", "title"]:
            node = soup.find(selector)
            if node:
                text = self._normalize_line(node.get_text(" "))
                if text:
                    return text
        return "web_document"

    def _clean_lines(self, lines: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw_line in lines:
            line = self._normalize_line(raw_line)
            if not line:
                continue
            if self._is_noise_line(line):
                continue
            if line in seen:
                continue
            seen.add(line)
            cleaned.append(line)
        return cleaned

    def _normalize_line(self, text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _is_noise_line(self, line: str) -> bool:
        if len(line) <= 1:
            return True
        for pattern in self.NOISE_PATTERNS:
            if pattern.match(line):
                return True
        if line.startswith("Image:"):
            return True
        if line.startswith("http") and len(line) < 80:
            return True
        return False

    def _build_filename(self, url: str, title: str, filename_hint: str | None = None) -> str:
        if filename_hint:
            base = filename_hint.strip()
        else:
            parsed = urlparse(url)
            seed = title or parsed.path.rsplit("/", 1)[-1] or parsed.netloc
            base = self._slugify(seed)
        if not base:
            base = "web_document"
        if not base.endswith(".txt"):
            base += ".txt"
        return base

    def _slugify(self, value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^0-9a-zA-Z가-힣]+", "_", value)
        value = re.sub(r"_+", "_", value)
        return value.strip("_")
