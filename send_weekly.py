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
PROBLEMS_FILE = BASE_DIR / "swea_problems.json"
HISTORY_FILE = BASE_DIR / "history.json"

PROBLEMS_PER_WEEK = 3


# ============================================================
# 문제 목록 불러오기
# ============================================================

def load_problems():
    if not PROBLEMS_FILE.exists():
        raise FileNotFoundError(
            f"문제 목록 파일을 찾을 수 없습니다: {PROBLEMS_FILE}"
        )

    with PROBLEMS_FILE.open("r", encoding="utf-8") as file:
        problems = json.load(file)

    if not isinstance(problems, list):
        raise ValueError("swea_problems.json의 최상위 구조는 리스트([])여야 합니다.")

    valid_problems = []

    for problem in problems:
        if not isinstance(problem, dict):
            continue

        required_keys = {"id", "title", "level", "url"}

        if not required_keys.issubset(problem.keys()):
            continue

        valid_problems.append(problem)

    if len(valid_problems) < PROBLEMS_PER_WEEK:
        raise ValueError(
            f"사용 가능한 문제가 {PROBLEMS_PER_WEEK}개보다 적습니다."
        )

    return valid_problems


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
# 이번 주 문제 3개 선택
# ============================================================

def select_problems(problems, history):
    sent_ids = set(history["sent_ids"])

    available = [
        problem
        for problem in problems
        if str(problem["id"]) not in sent_ids
    ]

    # 아직 보내지 않은 문제가 3개 이상 있으면
    # 기존에 보낸 문제를 제외하고 랜덤 선택
    if len(available) >= PROBLEMS_PER_WEEK:
        selected = random.sample(
            available,
            PROBLEMS_PER_WEEK,
        )

        return selected

    # 남은 문제가 3개 미만이면 전체 목록을 다시 사용
    print("모든 문제를 한 번씩 사용했습니다. 추천 이력을 초기화합니다.")

    history["sent_ids"] = []

    selected = random.sample(
        problems,
        PROBLEMS_PER_WEEK,
    )

    return selected


# ============================================================
# Mattermost 메시지 생성
# ============================================================

def make_message(problems):
    lines = [
        "## 📚 이번 주 IM 대비 SWEA 랜덤 3문제",
        "",
    ]

    for index, problem in enumerate(problems, start=1):
        lines.append(
            f'{index}. **[{problem["level"]}] '
            f'[{problem["title"]}]({problem["url"]})**'
        )

    lines.extend(
        [
            "",
            "D2~D4 중에서 골랐어요. 이번 주 안에 도전해봅시다! 💪",
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
        problems = load_problems()
        history = load_history()

        selected = select_problems(
            problems,
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

        print(
            f"전체 {len(problems)}개 문제 중 "
            f"{len(selected)}개를 Mattermost에 전송했습니다."
        )

        print("이번 주 추천 문제:")

        for problem in selected:
            print(
                f'- [{problem["level"]}] '
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