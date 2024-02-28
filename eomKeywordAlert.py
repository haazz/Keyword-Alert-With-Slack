from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import time
import requests
import pymysql
import os


def checkKeywordExistDB(mysqlCursor, keyword):
    selectKeywordSqlQuery = "SELECT keyword FROM keywordtable WHERE keyword like \'" + keyword + "\'"
    result = mysqlCursor.execute(selectKeywordSqlQuery)
    if (result == 0):
        return False
    return True

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
        attachments = [{
            "color": "good",
            "text": text
        }]

        data = {"username": username, "attachments": attachments, "icon_emoji": icon_emoji}
        print(data)

        # 메세지 전송
        return requests.post(url, headers=header, json=data)
        
    except Exception as e:
        exit(0)

def findPost():
    searchButton = driver.find_element(By.CSS_SELECTOR, ".trigger-search")
    searchButton.click()
    time.sleep(1)
    for keyword in findPostDict:
        searchInput = driver.find_element(By.CSS_SELECTOR, "._search .keyword")
        searchInput.clear()
        searchInput.send_keys(keyword)
        searchInput.send_keys(Keys.RETURN)
        time.sleep(2)
        posts = driver.find_elements(By.CSS_SELECTOR, ".card_content .pjax")
        for post in posts:
            postTitle = post.get_attribute("text")
            if postTitle not in findPostDict[keyword]:
                findPostDict[keyword].append(postTitle)

def alertNewPost():
    searchButton = driver.find_element(By.CSS_SELECTOR, ".trigger-search")
    searchButton.click()
    time.sleep(1)
    for keyword in findPostDict:
        searchInput = driver.find_element(By.CSS_SELECTOR, "._search .keyword")
        searchInput.clear()
        searchInput.send_keys(keyword)
        searchInput.send_keys(Keys.RETURN)
        time.sleep(2)
        posts = driver.find_elements(By.CSS_SELECTOR, ".card_content .pjax")
        for post in posts:
            postTitle = post.get_attribute("text")
            if postTitle not in findPostDict[keyword]:
                response = postMessage(slackUrl, postTitle + "\n" + post.get_attribute("href"))
                findPostDict[keyword].append(postTitle)
                print(postTitle)
                print(response)
        while len(findPostDict[keyword]) > 100:
            findPostDict[keyword].pop(0)

if __name__ == "__main__":
    # .env 파일 가져오기
    load_dotenv()

    # mysql 연결
    mysqlConnect = pymysql.connect(host=os.environ.get('MYSQL_HOST'), user=os.environ.get('MYSQL_USER'), password=os.environ.get('MYSQL_PASSWORD'), db=os.environ.get('MYSQL_DB_NAME'), charset='utf8')
    mysqlCursor = mysqlConnect.cursor()

    # slack bot request url
    slackUrl = os.environ.get("SLACK_URL")

    # chrome --headless를 위한 userAgent 정보
    userAgent = os.environ.get("USER_AGENT")
    
    # chrome driver 가져오기
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument(userAgent)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    crawlUrlList = [os.environ.get('CRAWL_URL_1'), os.environ.get('CRAWL_URL_2')]

    findPostDict = {}
    try:
        for keyword in selectKeywordListDB(mysqlCursor):
            findPostDict[keyword[0]] = []
        print(findPostDict)

        for crawlUrl in crawlUrlList:
            driver.get(crawlUrl)
            time.sleep(2)
            driver.implicitly_wait(5)    
            findPost()
            driver.close()
            time.sleep(2)
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        print(findPostDict)
        
        while(True):
            for crawlUrl in crawlUrlList:
                driver.get(crawlUrl)
                time.sleep(2)
                driver.implicitly_wait(5)
                alertNewPost()
                driver.close()
                time.sleep(2)
                driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

            time.sleep(9 * 60)

    except KeyboardInterrupt:
        postMessage(slackUrl, "Server Down!")
        mysqlConnect.close()
        driver.close()
    
    driver.close()