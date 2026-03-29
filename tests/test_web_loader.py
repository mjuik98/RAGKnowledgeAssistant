from __future__ import annotations

import tempfile
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

from app.services.web_loader import WebDocumentFetcher


SAMPLE_HTML = """
<html>
  <head>
    <title>테스트 공지</title>
    <script>var hidden = true;</script>
  </head>
  <body>
    <nav>홈 검색 메뉴</nav>
    <main>
      <h1>2026 청년 지원 공고</h1>
      <p>신청기간은 2026년 5월 1일부터 6월 19일까지입니다.</p>
      <p>지원금은 월 최대 10만 원입니다.</p>
      <p>문의처는 청년정책과입니다.</p>
    </main>
    <footer>개인정보처리방침</footer>
  </body>
</html>
"""


class WebLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fetcher = WebDocumentFetcher(timeout_seconds=5)

    def test_extract_text_prefers_main_content(self) -> None:
        title, text = self.fetcher.extract_text(SAMPLE_HTML)
        self.assertEqual(title, "2026 청년 지원 공고")
        self.assertIn("신청기간은 2026년 5월 1일부터 6월 19일까지입니다.", text)
        self.assertIn("지원금은 월 최대 10만 원입니다.", text)
        self.assertNotIn("var hidden", text)
        self.assertNotIn("개인정보처리방침", text)

    @patch("app.services.web_loader.requests.get")
    def test_snapshot_url_to_text_saves_txt(self, mock_get: Mock) -> None:
        response = Mock()
        response.text = SAMPLE_HTML
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        with tempfile.TemporaryDirectory() as tmpdir:
            output = self.fetcher.snapshot_url_to_text(
                url="https://example.org/policy/123",
                title_hint="테스트 공지",
                filename_hint="test_notice",
                output_dir=Path(tmpdir),
            )
            saved_text = output.read_text(encoding="utf-8")

        self.assertTrue(output.name.endswith(".txt"))
        self.assertIn("[source_url] https://example.org/policy/123", saved_text)
        self.assertIn("[source_title] 테스트 공지", saved_text)
        self.assertIn("지원금은 월 최대 10만 원입니다.", saved_text)


if __name__ == "__main__":
    unittest.main()
