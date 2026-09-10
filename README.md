# Weekly SWEA Picker

매주 월요일 오전 7시(KST)에 SWEA D1~D3 난이도 문제 3개를 선정해 Mattermost 알고리즘 스터디 채널에 공지하는 자동화입니다.

## 기능

- SWEA D1, D2, D3 문제를 각각 1개씩 추천
- Mattermost 비공개 채널에 Markdown 형식으로 자동 공지
- GitHub Actions를 이용한 매주 월요일 정기 실행 예정

## 프로젝트 구조

```text
weekly-swea-picker/
├── swea_problems.json    # 문제 후보 목록
├── send_weekly.py        # 문제 선정 및 Mattermost 발송 코드
├── .gitignore            # 민감한 설정 파일 제외
└── README.md
```

## 메시지 예시

```text
📚 이번 주 IM 대비 SWEA 3문제

1. [D1] 연월일 달력
2. [D2] 최빈수 구하기
3. [D3] Flatten

이번 주 안에 풀어보고, 막힌 부분은 채널에서 같이 이야기해요!
```

## 보안

Mattermost Incoming Webhook URL은 절대 GitHub에 직접 올리지 않습니다.  
나중에 GitHub 저장소의 `Settings → Secrets and variables → Actions`에서 `MATTERMOST_WEBHOOK_URL`이라는 비밀 값으로 등록해 사용합니다.