from __future__ import annotations

import argparse
import shutil
from pathlib import Path


TARGET_PATHS = [
    Path('storage/app.db'),
    Path('storage/index'),
    Path('storage/evals'),
    Path('storage/parsed'),
    Path('storage/raw/web_imports'),
]

SAMPLE_FILES = {
    'sample_notice.txt',
    'youth_housing_support_2026.txt',
    'resident_certificate_fees_2026.txt',
    'university_scholarship_guide_2026.txt',
    'youth_transport_support_2025.txt',
    'youth_transport_support_2026.txt',
}


def main() -> None:
    parser = argparse.ArgumentParser(description='데모 실행 상태를 초기화합니다.')
    parser.add_argument('--remove-sample-raw', action='store_true', help='샘플 raw 문서까지 삭제합니다.')
    args = parser.parse_args()

    for target in TARGET_PATHS:
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
            print(f'삭제: {target}')
        elif target.exists():
            target.unlink()
            print(f'삭제: {target}')

    for path in [Path('storage/index'), Path('storage/evals'), Path('storage/parsed'), Path('storage/raw/web_imports')]:
        path.mkdir(parents=True, exist_ok=True)

    if args.remove_sample_raw:
        raw_dir = Path('storage/raw')
        for file_path in raw_dir.glob('*.txt'):
            if file_path.name in SAMPLE_FILES:
                file_path.unlink(missing_ok=True)
                print(f'샘플 raw 삭제: {file_path}')


if __name__ == '__main__':
    main()
