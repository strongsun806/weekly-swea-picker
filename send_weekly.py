import json
import os
import random
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

WEBHOOK_URL = os.environ.get("MATTERMOST_WEBHOOK_URL")
PROBLEMS_FILE = Path(__file__).with_name("swea_problems.json")


def load_problems():
    with PROBLEMS_FILE.open(encoding="utf-8") as file:
        problems = json.load(file)

    selected = []

    for level in ("D1", "D2", "D3"):
        candidates = [
            problem for problem in problems
            if problem["level"] == level
        ]

        if not candidates:
            raise ValueError(f"{level} 문제 후보가 없습니다.")

        selected.append(random.choice(candidates))

    return selected


def make_message(problems):
    lines = [
        "## 📚 이번 주 IM 대비 SWEA 3문제",
        "",
    ]

    for index, problem in enumerate(problems, start=1):
        lines.append(
            f'{index}. **[{problem["level"]}] '
            f'[{problem["title"]}]({problem["url"]})**'
        )

    lines.extend([
        "",
        "이번 주 안에 풀어보고, 막힌 부분은 채널에서 같이 이야기해요! 💪",
    ])

    return "\n".join(lines)


def send_to_mattermost(message):
    if not WEBHOOK_URL:
        raise ValueError("MATTERMOST_WEBHOOK_URL이 설정되지 않았습니다.")

    data = json.dumps({"text": message}).encode("utf-8")
    request = Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"전송 실패: HTTP {response.status}")


def main():
    try:
        problems = load_problems()
        message = make_message(problems)
        send_to_mattermost(message)
        print("Mattermost 메시지를 전송했습니다.")
    except (ValueError, HTTPError, URLError, RuntimeError) as error:
        print(f"오류: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()