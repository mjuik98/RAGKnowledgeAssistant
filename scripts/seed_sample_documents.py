from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SAMPLE_DOCUMENTS = {
    "sample_notice.txt": """
전입신고 안내
전입신고를 위해서는 신청인의 신분증이 필요합니다.
대리 신청 시에는 위임장과 대리인의 신분증을 추가로 제출해야 합니다.
세대주 확인이 필요한 경우 추가 확인 절차가 있을 수 있습니다.
자세한 내용은 주민센터 안내문을 확인하세요.
    """.strip(),
    "youth_housing_support_2026.txt": """
2026 청년 주거 지원 사업 안내
지원 대상은 만 19세 이상 34세 이하의 무주택 청년입니다.
월 소득이 기준중위소득 150퍼센트 이하인 1인 가구를 우선 지원합니다.
지원 금액은 월 최대 20만원이며 최대 12개월까지 지원합니다.
제외 대상은 주택을 보유한 신청자와 동일 사업 중복 수혜자입니다.
    """.strip(),
    "resident_certificate_fees_2026.txt": """
주민등록 등본 초본 발급 수수료 안내
주민센터 방문 발급 수수료는 통당 400원입니다.
정부24 온라인 발급 수수료는 무료입니다.
온라인 발급 가능 시간은 매일 06시부터 24시까지입니다.
수수료 감면 대상은 별도 규정에 따릅니다.
    """.strip(),
    "university_scholarship_guide_2026.txt": """
2026학년도 AI융합대학 장학금 안내
성적 우수 장학금은 직전 학기 15학점 이상 이수하고 평점평균 3.5 이상인 학생 중 선발합니다.
소득 연계 장학금은 한국장학재단 소득구간 5구간 이하 학생이 대상입니다.
공통 제출 서류는 성적증명서와 장학금 신청서입니다.
추가 서류가 필요한 경우 별도 공지합니다.
    """.strip(),
    "youth_transport_support_2025.txt": """
2025년 청년 교통비 지원 안내
지원 대상은 만 19세 이상 29세 이하 청년입니다.
지원 금액은 월 최대 5만원입니다.
신청 시 교통카드 이용 내역을 제출해야 합니다.
    """.strip(),
    "youth_transport_support_2026.txt": """
2026년 청년 교통비 지원 안내
지원 대상은 만 19세 이상 34세 이하 청년입니다.
지원 금액은 월 최대 7만원입니다.
신청 시 모바일 교통카드 이용 내역 확인서를 제출해야 합니다.
    """.strip(),
}


def main() -> None:
    raw_dir = Path("storage/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in SAMPLE_DOCUMENTS.items():
        target = raw_dir / filename
        target.write_text(content + "\n", encoding="utf-8")
        print(f"샘플 문서를 생성했습니다: {target}")

    print(f"총 {len(SAMPLE_DOCUMENTS)}개 샘플 문서를 생성했습니다.")


if __name__ == "__main__":
    main()
