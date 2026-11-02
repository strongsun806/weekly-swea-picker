import json
import os
import random
import sys
from pathlib import Path

import requests


# ============================================================
# 기본 설정
# ============================================================

WEBHOOK_URL = os.environ.get("MATTERMOST_WEBHOOK_URL")

BASE_DIR = Path(__file__).resolve().parent
SWEA_PROBLEMS_FILE = BASE_DIR / "swea_problems.json"
PROGRAMMERS_PROBLEMS_FILE = BASE_DIR / "programmers_problems.json"
HISTORY_FILE = BASE_DIR / "history.json"

SWEA_PER_WEEK = 2
PROGRAMMERS_PER_WEEK = 3
PROBLEMS_PER_WEEK = SWEA_PER_WEEK + PROGRAMMERS_PER_WEEK


# ============================================================
# 문제 목록 불러오기
# ============================================================

def _load_problem_file(file_path, default_source, min_count):
    if not file_path.exists():
        raise FileNotFoundError(
            f"문제 목록 파일을 찾을 수 없습니다: {file_path}"
        )

    with file_path.open("r", encoding="utf-8") as file:
        problems = json.load(file)

    if not isinstance(problems, list):
        raise ValueError(f"{file_path.name}의 최상위 구조는 리스트([])여야 합니다.")

    valid_problems = []

    for problem in problems:
        if not isinstance(problem, dict):
            continue

        required_keys = {"id", "title", "level", "url"}

        if not required_keys.issubset(problem.keys()):
            continue

        item = dict(problem)
        item.setdefault("source", default_source)
        valid_problems.append(item)

    if len(valid_problems) < min_count:
        raise ValueError(
            f"{file_path.name}에서 사용 가능한 문제가 {min_count}개보다 적습니다."
        )

    return valid_problems


def load_problems():
    swea_problems = _load_problem_file(
        SWEA_PROBLEMS_FILE,
        default_source="SWEA",
        min_count=SWEA_PER_WEEK,
    )
    programmers_problems = _load_problem_file(
        PROGRAMMERS_PROBLEMS_FILE,
        default_source="Programmers",
        min_count=PROGRAMMERS_PER_WEEK,
    )
    return swea_problems, programmers_problems


# ============================================================
# 추천 이력 불러오기
# ============================================================

def load_history():
    if not HISTORY_FILE.exists():
        return {"sent_ids": []}

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            history = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError("history.json의 JSON 형식이 올바르지 않습니다.") from error

    if not isinstance(history, dict):
        raise ValueError("history.json의 형식이 올바르지 않습니다.")

    sent_ids = history.get("sent_ids", [])

    if not isinstance(sent_ids, list):
        raise ValueError("history.json의 sent_ids는 리스트여야 합니다.")

    return {
        "sent_ids": [str(problem_id) for problem_id in sent_ids]
    }


# ============================================================
# 추천 이력 저장
# ============================================================

def save_history(history):
    with HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")


# ============================================================
# 이번 주 문제 5개 선택 (SWEA 2개 + Programmers 3개)
# ============================================================

def _select_from_pool(problems, count, history, source_label):
    sent_ids = set(history["sent_ids"])

    available = [
        problem
        for problem in problems
        if str(problem["id"]) not in sent_ids
    ]

    # 아직 보내지 않은 문제가 count개 이상 있으면
    # 기존에 보낸 문제를 제외하고 랜덤 선택
    if len(available) >= count:
        return random.sample(available, count)

    # 남은 문제가 count개 미만이면 해당 플랫폼의 추천 이력을 초기화하고 전체에서 선택
    print(f"{source_label} 문제를 모두 한 번씩 사용했습니다. {source_label} 추천 이력을 초기화합니다.")
    pool_ids = {str(problem["id"]) for problem in problems}
    history["sent_ids"] = [
        pid for pid in history["sent_ids"] if pid not in pool_ids
    ]

    return random.sample(problems, count)


def select_problems(swea_problems, programmers_problems, history):
    selected_swea = _select_from_pool(
        swea_problems,
        SWEA_PER_WEEK,
        history,
        "SWEA",
    )
    selected_programmers = _select_from_pool(
        programmers_problems,
        PROGRAMMERS_PER_WEEK,
        history,
        "Programmers",
    )
    return selected_swea + selected_programmers


# ============================================================
# Mattermost 메시지 생성
# ============================================================

def make_message(problems):
    lines = [
        "## 📚 이번 주 SWEA & 프로그래머스 랜덤 5문제",
        "",
    ]

    for index, problem in enumerate(problems, start=1):
        source = problem.get("source", "SWEA")
        lines.append(
            f'{index}. **[{source} / {problem["level"]}] '
            f'[{problem["title"]}]({problem["url"]})**'
        )

    lines.extend(
        [
            "",
            "SWEA(D2~D4) 2문제와 프로그래머스(Python Lv.0~1) 3문제를 골랐어요!",
            "🔥 **5일 동안 최소 한 개는 무조건 풀기!** 이번 주도 화이팅해봅시다! 💪",
        ]
    )

    return "\n".join(lines)


# ============================================================
# Mattermost 전송
# ============================================================

def send_to_mattermost(message):
    if not WEBHOOK_URL:
        raise ValueError(
            "MATTERMOST_WEBHOOK_URL이 설정되지 않았습니다."
        )

    response = requests.post(
        WEBHOOK_URL,
        json={"text": message},
        timeout=20,
    )

    response.raise_for_status()


# ============================================================
# 메인 실행
# ============================================================

def main():
    try:
        swea_problems, programmers_problems = load_problems()
        history = load_history()

        selected = select_problems(
            swea_problems,
            programmers_problems,
            history,
        )

        # Mattermost 전송이 성공한 경우에만
        # 선택된 문제를 history에 기록
        send_to_mattermost(
            make_message(selected)
        )

        history["sent_ids"].extend(
            str(problem["id"])
            for problem in selected
        )

        save_history(history)

        total_count = len(swea_problems) + len(programmers_problems)
        print(
            f"전체 {total_count}개 문제(SWEA {len(swea_problems)}개, "
            f"Programmers {len(programmers_problems)}개) 중 "
            f"{len(selected)}개를 Mattermost에 전송했습니다."
        )

        print("이번 주 추천 문제:")

        for problem in selected:
            source = problem.get("source", "SWEA")
            print(
                f'- [{source} / {problem["level"]}] '
                f'{problem["id"]}: {problem["title"]}'
            )

    except (
        ValueError,
        OSError,
        requests.RequestException,
    ) as error:
        print(
            f"오류: {error}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
