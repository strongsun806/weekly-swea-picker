import json
import os
import random
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

WEBHOOK_URL = os.environ.get("MATTERMOST_WEBHOOK_URL")
HISTORY_FILE = Path(__file__).with_name("history.json")
BASE_URL = "https://swexpertacademy.com"
LEVELS = ("D2", "D3", "D4")
MAX_PAGES_PER_LEVEL = 100


def extract_problems_from_page(soup, expected_level):
    lines = [
        line.strip()
        for line in soup.get_text("\n").splitlines()
        if line.strip()
    ]

    problems = []

    for index, line in enumerate(lines):
        id_match = re.match(r"^(\d+)\.$", line)

        if not id_match or index + 1 >= len(lines):
            continue

        problem_id = id_match.group(1)
        title = re.sub(r"\s*\[\d+\]\s*$", "", lines[index + 1]).strip()
        nearby_text = " ".join(lines[index + 2:index + 6])

        if expected_level not in nearby_text:
            continue

        problems.append(
            {
                "id": problem_id,
                "title": title,
                "level": expected_level,
                "url": (
                    f"{BASE_URL}/main/code/problem/problemList.do"
                    f"?problemTitle={problem_id}"
                ),
            }
        )

    return problems


def collect_problems():
    problems_by_id = {}

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        for level in LEVELS:
            level_number = level[1:]

            for page_index in range(1, MAX_PAGES_PER_LEVEL + 1):
                url = (
                    f"{BASE_URL}/main/code/problem/problemList.do"
                    f"?pageSize=30&pageIndex={page_index}"
                    f"&problemLevel={level_number}"
                )

                driver.get(url)

                WebDriverWait(driver, 20).until(
                    lambda browser: len(
                        extract_problems_from_page(
                            BeautifulSoup(browser.page_source, "html.parser"),
                            level,
                        )
                    ) > 0
                )

                soup = BeautifulSoup(driver.page_source, "html.parser")
                page_problems = extract_problems_from_page(soup, level)

                new_problems = [
                    problem for problem in page_problems
                    if problem["id"] not in problems_by_id
                ]

                for problem in new_problems:
                    problems_by_id[problem["id"]] = problem

                if not new_problems:
                    break

    except TimeoutException as error:
        raise ValueError("SWEA 문제 목록을 불러오는 시간이 초과되었습니다.") from error
    except WebDriverException as error:
        raise ValueError("SWEA 목록을 읽을 브라우저를 실행하지 못했습니다.") from error
    finally:
        driver.quit()

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