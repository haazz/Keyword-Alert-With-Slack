from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException

from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import re
import requests
import os
import logging
import traceback

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Stateless 설정: 크롤 간격과 알림 윈도우를 동일하게 두어
# 이력 저장 없이 "현재 시간 - WINDOW" 이후 post만 신규로 판단 (중복/누락 최소화)
# 키워드는 .env의 KEYWORD_LIST(콤마 구분)에서 로드 → 재배포 없이 수정 가능
ALERT_WINDOW_MINUTES = 10
CRAWL_INTERVAL_SECONDS = ALERT_WINDOW_MINUTES * 60

def postMessage(url, text):
    try:
        header = {'Content-type': 'application/json'}
        icon_emoji = ":slack:"
        username = "keyword-bot"
        attachments = [{"color": "good", "text": text}]
        data = {"username": username, "attachments": attachments, "icon_emoji": icon_emoji}
        print(data)

        # 메세지 전송
        return requests.post(url, headers=header, json=data)
    except Exception as e:
        logging.error("Slack-Bot postMessage fail!")
        exit(0)

def getPostTimeText(post):
    # 추정 셀렉터: post(.pjax 링크)가 속한 카드 컨테이너 내부의 작성시간 element.
    # 실제 DOM 구조 확인 후 ancestor 경로 및 CSS 셀렉터(.time/.date/.regdate/time)를 맞춰야 함.
    try:
        card = post.find_element(By.XPATH, "./ancestor::*[contains(@class,'card_content')][1]")
        timeEl = card.find_element(By.CSS_SELECTOR, ".time, .date, .regdate, time")
        return driver.execute_script("return arguments[0].textContent;", timeEl).strip()
    except Exception:
        return None

def parsePostTime(timeText):
    # 작성시간 텍스트를 datetime으로 파싱. 상대시간/절대시간 모두 추정 포맷 대응.
    # 실제 사이트 표기 포맷 확인 후 케이스 보강 필요.
    if not timeText:
        return None
    now = datetime.now()
    text = timeText.strip()

    if "방금" in text:
        return now

    # 상대시간: "3분 전", "1시간 전", "2일 전" 등
    m = re.search(r"(\d+)\s*(초|분|시간|일|주|개월|달|년)\s*전", text)
    if m:
        value = int(m.group(1))
        unit = m.group(2)
        deltas = {
            "초": timedelta(seconds=value),
            "분": timedelta(minutes=value),
            "시간": timedelta(hours=value),
            "일": timedelta(days=value),
            "주": timedelta(weeks=value),
            "개월": timedelta(days=value * 30),
            "달": timedelta(days=value * 30),
            "년": timedelta(days=value * 365),
        }
        return now - deltas[unit]

    # 절대시간 추정 포맷
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y.%m.%d %H:%M",
                "%Y-%m-%d", "%Y.%m.%d", "%m-%d %H:%M", "%m.%d %H:%M"):
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.year == 1900:  # 연도 없는 포맷은 올해로 보정
                parsed = parsed.replace(year=now.year)
            return parsed
        except ValueError:
            continue

    # "HH:MM"만 있으면 오늘 날짜로 간주
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
    if m:
        return now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)

    logging.warning(f"Unparsable post time text: {timeText}")
    return None

def alertNewPost(cutoff):
    # 이력 저장 없이 cutoff(현재시간 - WINDOW) 이후 작성된 post만 알림 → stateless
    try:
        searchButton = WebDriverWait(driver, 100).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".trigger-search"))
        )
        searchButton.click()
        time.sleep(3)
        for keyword in KEYWORDS:
            searchInput = WebDriverWait(driver, 100).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "._search .keyword"))
            )
            searchInput.clear()
            searchInput.send_keys(keyword)
            searchInput.send_keys(Keys.RETURN)
            time.sleep(2)
            posts = WebDriverWait(driver, 100).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".card_content .pjax"))
            )
            for post in posts:
                try:
                    postTime = parsePostTime(getPostTimeText(post))
                    if postTime is not None and postTime >= cutoff:
                        postTitle = driver.execute_script("return arguments[0].textContent;", post)
                        postUrl = post.get_attribute("href")
                        response = postMessage(slackUrl, f"{postTitle}\n{postUrl}")
                        logging.info(f"New post found: {postTitle} ({postTime})")
                        logging.info(f"Slack response: {response}")
                except StaleElementReferenceException:
                    logging.warning(f"Stale element encountered for keyword: {keyword}")
                    continue
    except TimeoutException:
        logging.error("Timeout occurred while alerting new posts")

if __name__ == "__main__":
    # .env 파일 가져오기
    load_dotenv()

    # slack bot request url
    slackUrl = os.environ.get("SLACK_URL")

    # 키워드 목록: .env KEYWORD_LIST(콤마 구분)에서 로드 → 재배포 없이 수정
    KEYWORDS = [k.strip() for k in os.environ.get("KEYWORD_LIST", "").split(",") if k.strip()]
    if not KEYWORDS:
        logging.error("KEYWORD_LIST is empty. Set it in .env (e.g. KEYWORD_LIST=아워레가시,ourlegacy)")
        exit(1)

    # chrome --headless를 위한 userAgent 정보
    userAgent = os.environ.get("USER_AGENT")
    
    # chrome driver 가져오기
    # ubuntu 환경에서 window-size를 설정하지 않으면 클릭이 안되는 문제 해결
    options = Options()
    options.add_argument('--window-size=1920,1080')  
    options.add_argument('--headless=new')
    options.add_argument(userAgent)
    CHROME_DRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH")
    # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    service = Service(executable_path=CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    crawlUrlList = [os.environ.get('CRAWL_URL_1'), os.environ.get('CRAWL_URL_2')]

    logging.info(f"Keywords: {KEYWORDS}, window: {ALERT_WINDOW_MINUTES}min (stateless)")
    try:
        while True:
            # 이번 통신 시간 기준 cutoff 계산 → 이력 DB 없이 시간만으로 신규 판단
            cutoff = datetime.now() - timedelta(minutes=ALERT_WINDOW_MINUTES)
            for crawlUrl in crawlUrlList:
                driver.get(crawlUrl)
                time.sleep(2)
                driver.implicitly_wait(5)
                alertNewPost(cutoff)
                driver.quit()
                time.sleep(2)
                driver = webdriver.Chrome(service=service, options=options)

            time.sleep(CRAWL_INTERVAL_SECONDS)


    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt: Server shutting down")
    except Exception as e:
        traceback.print_exc()
        logging.error(f"Unexpected error in main: {e}")
    finally:
        postMessage(slackUrl, "Server Down!")
        driver.quit()
