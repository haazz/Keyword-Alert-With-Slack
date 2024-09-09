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
import time
import requests
import pymysql
import os
import logging
import traceback

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def checkKeywordExistDB(mysqlCursor, keyword):
    selectKeywordSqlQuery = "SELECT keyword FROM keywordtable WHERE keyword like \'" + keyword + "\'"
    result = mysqlCursor.execute(selectKeywordSqlQuery)
    return result != 0

def insertKeywordDB(mysqlCursor, mysqlConnect, keyword):
    insertSqlQuery = "insert into keywordtable values(%s)"
    if not checkKeywordExist(mysqlCursor, keyword):
        mysqlCursor.execute(insertSqlQuery, keyword)
        mysqlConnect.commit()

def deleteKeywordDB(mysqlCursor, mysqlConnect, keyword):
    deleteKeywordSqlQuery = "DELETE FROM keywordtable WHERE keyword=\'" + keyword + "\'"
    if checkKeywordExist(mysqlCursor, keyword):
        mysqlCursor.execute(deleteKeywordSqlQuery)
        mysqlConnect.commit()

def selectKeywordListDB(mysqlCursor):
    selectSqlQuery = "SELECT keyword FROM keywordtable"
    mysqlCursor.execute(selectSqlQuery)
    return mysqlCursor.fetchall()

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

def findPost():
    try:
        searchButton = WebDriverWait(driver, 100).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".trigger-search"))
        )
        searchButton.click()
        time.sleep(1)
        for keyword in findPostDict:
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
                    postTitle = driver.execute_script("return arguments[0].textContent;", post)
                    print(postTitle)
                    if postTitle not in findPostDict[keyword]:
                        findPostDict[keyword].append(postTitle)
                    
                except StaleElementReferenceException:
                    logging.warning(f"Stale element encountered for keyword: {keyword}")
                    continue
            

    except TimeoutException:
        logging.error("Timeout occurred while finding posts")


def alertNewPost():
    try:
        searchButton = WebDriverWait(driver, 100).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".trigger-search"))
        )
        searchButton.click()
        time.sleep(3)
        for keyword in findPostDict:
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
                    postTitle = driver.execute_script("return arguments[0].textContent;", post)
                    if postTitle not in findPostDict[keyword]:
                        postUrl = post.get_attribute("href")
                        response = postMessage(slackUrl, f"{postTitle}\n{postUrl}")
                        findPostDict[keyword].append(postTitle)
                        logging.info(f"New post found: {postTitle}")
                        logging.info(f"Slack response: {response}")
                except StaleElementReferenceException:
                    logging.warning(f"Stale element encountered for keyword: {keyword}")
                    continue
            while len(findPostDict[keyword]) > 100:
                findPostDict[keyword].pop(0)
    except TimeoutException:
        logging.error("Timeout occurred while alerting new posts")

if __name__ == "__main__":
    # .env 파일 가져오기
    load_dotenv()

    # mysql 연결
    # mysqlConnect = pymysql.connect(host=os.environ.get('MYSQL_HOST'), user=os.environ.get('MYSQL_USER'), password=os.environ.get('MYSQL_PASSWORD'), db=os.environ.get('MYSQL_DB_NAME'), charset='utf8')
    # mysqlCursor = mysqlConnect.cursor()
    
    # slack bot request url
    slackUrl = os.environ.get("SLACK_URL")

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

    # findPostDict = {keyword[0]: [] for keyword in selectKeywordListDB(mysqlCursor)}
    findPostDict = {"아워레가시": [], "ourlegacy": [] }
    logging.info(f"Initial findPostDict: {findPostDict}")
    try:
        for crawlUrl in crawlUrlList:
            driver.get(crawlUrl)
            time.sleep(2)
            driver.implicitly_wait(5)    
            findPost()
            driver.quit()
            time.sleep(2)
            # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            driver = webdriver.Chrome(service=service, options=options)

        logging.info(f"Updated findPostDict: {findPostDict}")
        
        while True:
            for crawlUrl in crawlUrlList:
                driver.get(crawlUrl)
                time.sleep(2)
                driver.implicitly_wait(5)
                alertNewPost()
                driver.quit()
                time.sleep(2)
                # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
                driver = webdriver.Chrome(service=service, options=options)

            time.sleep(9 * 60)


    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt: Server shutting down")
    except Exception as e:
        traceback.print_exc()
        logging.error(f"Unexpected error in main: {e}")
    finally:
        postMessage(slackUrl, "Server Down!")
        # mysqlConnect.close()
        driver.quit()