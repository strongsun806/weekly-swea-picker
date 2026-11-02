# 🤖 Weekly SWEA & Programmers Picker !!

매주 월요일 오전 7시(KST)에 **SWEA(D2~D4) 2문제와 프로그래머스(Python Lv.0~1) 3문제, 총 5개를 랜덤으로 선정**하여 Mattermost 알고리즘 스터디 채널에 자동으로 공지하는 봇입니다.

알고리즘 스터디에서 매주 문제를 직접 선정하는 번거로움을 줄이고, 꾸준히 문제를 풀 수 있도록 제작했습니다.

---

## 🎯 스터디 목적

* SWEA IM 대비 및 Python 기초/구현 역량 강화
* 알고리즘 문제 풀이 습관 형성
* 다양한 문제 유형 경험
* 문제를 직접 읽고 풀이 방법을 생각하는 능력 향상
* **5일 동안 최소 1문제 이상 무조건 풀이** 및 꾸준한 참여

---

## 🤖 주요 기능

* **SWEA D2~D4** (186문제) 중 **2문제** + **프로그래머스 Python3 Lv.0~1** (328문제) 중 **3문제**, 매주 **총 5문제 랜덤 추천**
* Mattermost 알고리즘 스터디 채널에 Markdown 형식으로 자동 공지
* GitHub Actions를 이용해 **매주 월요일 오전 7시(KST)** 자동 실행
* 이미 봇이 추천한 문제는 다시 추천하지 않도록 **중복 제거**
* 추천한 문제의 이력을 `history.json`에 저장
* GitHub Actions 실행 후 변경된 추천 이력을 자동으로 GitHub에 커밋 및 Push

---

## 📌 문제 추천 방식

매주 SWEA와 프로그래머스 문제 후보 중 아직 추천되지 않은 문제를 기준으로 **총 5문제(SWEA 2 + 프로그래머스 3)**를 랜덤 선정합니다.

```text
SWEA 후보 (186개) + 프로그래머스 후보 (328개)
      ↓
이미 추천된 문제 제외
      ↓
남은 문제 중 랜덤 선정 (SWEA 2개 + 프로그래머스 3개)
      ↓
총 5문제 추천
      ↓
Mattermost 자동 공지
      ↓
history.json에 추천 이력 저장
```

### 🔄 중복 추천 방지

**봇이 이전에 추천했던 문제는 다시 추천하지 않습니다.**

추천된 문제의 ID는 `history.json`에 기록되며, 다음 주 문제를 선정할 때 이미 추천된 문제를 자동으로 제외합니다. 특정 플랫폼의 문제를 모두 소진한 경우 해당 플랫폼의 이력만 초기화되어 다시 추천됩니다.

---

## 🔥 스터디 규칙

* 매주 추천되는 5문제 중 **5일 동안 최소 한 개는 무조건 풀기!**
* 본인의 실력과 일정에 맞춰 Lv.0~Lv.1, D2~D4 문제를 자율적으로 도전합니다.

---

## 📁 프로젝트 구조

```text
weekly-swea-picker/
│
├── swea_problems.json          # SWEA 문제 후보 목록 (D2~D4)
├── programmers_problems.json   # 프로그래머스 문제 후보 목록 (Python3 Lv.0~1)
├── history.json                # 봇이 추천한 문제 이력
├── send_weekly.py              # 문제 선정 및 Mattermost 발송 코드
├── requirements.txt            # Python 패키지 목록
│
├── .github/
│   └── workflows/
│       └── weekly.yml          # GitHub Actions 자동 실행 설정
│
├── .gitignore                  # 민감한 설정 파일 및 불필요한 파일 제외
└── README.md                   # 프로젝트 설명
```

---

## 💬 Mattermost 공지 예시

```text
## 📚 이번 주 SWEA & 프로그래머스 랜덤 5문제

1. **[SWEA / D4] [문제 제목](링크)**
2. **[SWEA / D3] [문제 제목](링크)**
3. **[Programmers / Lv.0] [문제 제목](링크)**
4. **[Programmers / Lv.1] [문제 제목](링크)**
5. **[Programmers / Lv.0] [문제 제목](링크)**

SWEA(D2~D4) 2문제와 프로그래머스(Python Lv.0~1) 3문제를 골랐어요!
🔥 **5일 동안 최소 한 개는 무조건 풀기!** 이번 주도 화이팅해봅시다! 💪
```

---

## 📦 Python 패키지

현재 프로젝트에서 사용하는 외부 Python 패키지는 `requests`입니다.

`requirements.txt`:

```text
requests
```

---

## 🔐 보안

Mattermost Incoming Webhook URL과 같은 민감한 정보는 **절대 GitHub 저장소에 직접 업로드하지 않습니다.**

GitHub Repository의 `Settings → Secrets and variables → Actions`에 `MATTERMOST_WEBHOOK_URL`로 등록하여 사용합니다.
