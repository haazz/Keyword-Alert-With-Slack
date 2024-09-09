# ✨프로젝트 소개
- Keyword-Alert-With-Slack
- 설정해둔 키워드에 맞는 post가 업데이트 될 때마다 slack bot을 통해 알림을 주는 서비스
- 개인 프로젝트로 진행 하였습니다.

## 🎞 Duration

2024.01 ~ 2024.03

## 🛠️ Skills & Tools
<img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white"> <img src="https://img.shields.io/badge/mysql-4479A1?style=for-the-badge&logo=mysql&logoColor=white"> <img src="https://img.shields.io/badge/amazonaws-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white">

<img src="https://img.shields.io/badge/Google_chrome-4285F4?style=for-the-badge&logo=Google-chrome&logoColor=white"> <img src="https://img.shields.io/badge/Selenium-43B02A?logo=Selenium&logoColor=white"> <img src="https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=slack&logoColor=white">

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
MYSQL_HOST = "HOST"
MYSQL_USER = "USER"
MYSQL_PASSWORD = "PASSWORD"
MYSQL_DB_NAME = "DBNAME"

SLACK_URL = "SLACK_BOT_BASE_URL"

USER_AGENT = "TEMPORARY_USER_AGENT"

CRAWL_URL_1 = "CRAWL_URL"
CRAWL_URL_2 = "CRAWL_URL"
CHROME_DRIVER_PATH = "CHROME_DRIVER_PATH"

INSERT_KEYWORD_LIST = '[]'
DELETE_KEYWORD_LIST = '[]'
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

