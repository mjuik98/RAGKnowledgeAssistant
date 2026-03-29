from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GuardDecision:
    blocked: bool
    status: str = "ok"
    reason: str | None = None
    message: str | None = None


class QueryGuard:
    """문서 근거형 RAG 데모에서 다루기 어려운 요청을 선별합니다."""

    def __init__(self) -> None:
        self.block_patterns: list[tuple[re.Pattern[str], str]] = [
            (
                re.compile(r"(시스템\s*프롬프트|system\s*prompt|developer\s*message|내부\s*지침)", re.IGNORECASE),
                "prompt_injection",
            ),
            (
                re.compile(r"(ignore\s+(all|previous)|이전\s*지시.*무시|문서.*무시|규칙.*무시)", re.IGNORECASE),
                "instruction_override",
            ),
            (
                re.compile(r"(출처\s*없이|근거\s*없이|문서\s*말고|너의\s*지식으로|일반\s*상식으로)", re.IGNORECASE),
                "ungrounded_request",
            ),
            (
                re.compile(r"(비밀번호|password|api\s*key|secret|token|개인정보\s*유출)", re.IGNORECASE),
                "sensitive_exfiltration",
            ),
        ]

    def inspect(self, question: str) -> GuardDecision:
        normalized = re.sub(r"\s+", " ", question).strip()
        if not normalized:
            return GuardDecision(blocked=True, status="guard_blocked", reason="empty_question", message="질문을 입력해 주세요.")

        for pattern, reason in self.block_patterns:
            if pattern.search(normalized):
                return GuardDecision(
                    blocked=True,
                    status="guard_blocked",
                    reason=reason,
                    message=(
                        "이 도우미는 업로드된 문서에 근거한 질문만 답변합니다. "
                        "출처가 포함된 문서 질문으로 다시 요청해 주세요."
                    ),
                )

        return GuardDecision(blocked=False)
