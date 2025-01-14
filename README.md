# ✨프로젝트 소개
- Keyword-Alert-With-Slack
- 설정해둔 키워드에 맞는 post가 업데이트 될 때마다 slack bot을 통해 알림을 주는 서비스
- 개인 프로젝트로 진행 하였습니다.

## 🎞 Duration

2024.01 ~ 2024.03

## 🛠️ Skills & Tools
<img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white"> <img src="https://img.shields.io/badge/amazonaws-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white">

<img src="https://img.shields.io/badge/Google_chrome-4285F4?style=for-the-badge&logo=Google-chrome&logoColor=white"> <img src="https://img.shields.io/badge/Selenium-43B02A?logo=Selenium&logoColor=white"> <img src="https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=slack&logoColor=white">

## 🧩 아키텍처 (Stateless)
- 초기에는 RDS(MySQL)에 키워드 리스트와 조회 완료한 할인 이력을 저장하고 주기적으로 벌크 삭제하는 구조로 운영
- 이력 DB 조회/관리로 인한 인프라 오버헤드가 누적되어, 전체 이력 보관 대신 **현재 통신 시간을 기준으로 신규 post 여부를 즉각 판단하는 무상태(Stateless) 로직**으로 전면 리팩토링
- 각 post의 작성 시간을 파싱하여 `현재 시간 - 10분` 이후에 올라온 post만 신규로 판단해 알림 전송 → 이력 저장 없이 시간 기준으로만 판단
- 서버 비정상 종료 시 `finally` 블록에서 Slack-Webhook으로 `Server Down!` 알림을 전송하여 가용성 확보

## 👟 실행
- ubuntu 환경에서 chrome 설치
```bash
wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_128.0.6613.119_amd64.deb

sudo dpkg -i google-chrome-stable_current_amd64.deb

sudo apt-get install -f

google-chrome --version
```

- .env 생성 (src directory 밑에 생성)
```python
SLACK_URL = "SLACK_BOT_BASE_URL"

USER_AGENT = "TEMPORARY_USER_AGENT"

CRAWL_URL_1 = "CRAWL_URL"
CRAWL_URL_2 = "CRAWL_URL"
CHROME_DRIVER_PATH = "CHROME_DRIVER_PATH"

# 알림받을 키워드 (콤마 구분, 재배포 없이 수정 가능)
KEYWORD_LIST = "아워레가시,ourlegacy"
```

- venv 생성 및 pip 설치
```bash
python3 -m venv ./keyword_alert_venv

source ./keyword_alert_venv/bin/activate

pip install -r requirements.txt
```

- python 실행
```python
nohup python3 src/eomKeywordAlert.py &
```

