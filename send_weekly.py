import json
import os
import random
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("MATTERMOST_WEBHOOK_URL")
HISTORY_FILE = Path(__file__).with_name("history.json")
BASE_URL = "https://swexpertacademy.com"
LEVELS = ("D2", "D3", "D4")
MAX_PAGES_PER_LEVEL = 100

HEADERS = {
    "User-Agent": "weekly-swea-picker/1.0 (study reminder bot)"
}


def find_problem_in_link(link, level):
    node = link

    for _ in range(5):
        text = " ".join(node.stripped_strings)
        match = re.search(r"(\d+)\.\s*(.+)", text)

        if match:
            problem_id = match.group(1)
            title = re.sub(r"\s*\[\d+\]\s*$", "", match.group(2)).strip()

            if title:
                return {
                    "id": problem_id,
                    "title": title,
                    "level": level,
                    "url": urljoin(BASE_URL, link.get("href")),
                }

        node = node.parent

        if node is None:
            break

    return None


def collect_problems():
    problems_by_id = {}

    for level in LEVELS:
        level_number = level[1:]

        for page_index in range(1, MAX_PAGES_PER_LEVEL + 1):
            response = requests.get(
                f"{BASE_URL}/main/code/problem/problemList.do",
                params={
                    "pageSize": 100,
                    "pageIndex": page_index,
                    "problemLevel": level_number,
                },
                headers=HEADERS,
                timeout=20,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            page_problems = []

            for link in soup.select('a[href*="problemDetail.do"]'):
                problem = find_problem_in_link(link, level)

                if problem and problem["id"] not in problems_by_id:
                    problems_by_id[problem["id"]] = problem
                    page_problems.append(problem)

            # 다음 페이지에서 새 문제가 없으면 해당 난이도의 끝입니다.
            if not page_problems:
                break

    problems = list(problems_by_id.values())

    if len(problems) < 3:
        raise ValueError("SWEA에서 D2~D4 문제를 충분히 가져오지 못했습니다.")

    return problems


def load_history():
    if not HISTORY_FILE.exists():
        return {"sent_ids": []}

    with HISTORY_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def save_history(history):
    with HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)


def select_problems(problems, history):
    sent_ids = set(history["sent_ids"])
    available = [problem for problem in problems if problem["id"] not in sent_ids]

    # D2~D4 후보를 모두 한 번씩 보냈다면 새 순환을 시작합니다.
    if len(available) < 3:
        history["sent_ids"] = []
        available = problems

    selected = random.sample(available, 3)
    history["sent_ids"].extend(problem["id"] for problem in selected)

    return selected


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

    lines.extend([
        "",
        "D2~D4 중에서 골랐어요. 이번 주 안에 도전해봅시다! 💪",
    ])

    return "\n".join(lines)


def send_to_mattermost(message):
    if not WEBHOOK_URL:
        raise ValueError("MATTERMOST_WEBHOOK_URL이 설정되지 않았습니다.")

    response = requests.post(
        WEBHOOK_URL,
        json={"text": message},
        timeout=20,
    )
    response.raise_for_status()


def main():
    try:
        problems = collect_problems()
        history = load_history()
        selected = select_problems(problems, history)

        send_to_mattermost(make_message(selected))
        save_history(history)

        print(f"SWEA 후보 {len(problems)}개에서 3개를 전송했습니다.")
    except (ValueError, OSError, requests.RequestException) as error:
        print(f"오류: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()