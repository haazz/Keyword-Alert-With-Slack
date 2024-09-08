from dotenv import load_dotenv
import time
import requests
import pymysql
import json
import os

def checkKeywordExist(mysqlCursor, keyword):
    selectKeywordSqlQuery = "SELECT keyword FROM keywordtable WHERE keyword like \'" + keyword + "\'"
    result = mysqlCursor.execute(selectKeywordSqlQuery)
    if (result == 0):
        return False
    return True

def insertKeyword(mysqlCursor, mysqlConnect, keyword):
    insertSqlQuery = "insert into keywordtable values(%s)"
    if not checkKeywordExist(mysqlCursor, keyword):
        print("insert: " + keyword)
        mysqlCursor.execute(insertSqlQuery, keyword)
        mysqlConnect.commit()

def deleteKeyword(mysqlCursor, mysqlConnect, keyword):
    deleteKeywordSqlQuery = "DELETE FROM keywordtable WHERE keyword=\'" + keyword + "\'"
    if checkKeywordExist(mysqlCursor, keyword):
        print("delete: " + keyword)
        mysqlCursor.execute(deleteKeywordSqlQuery)
        mysqlConnect.commit()

def selectKeywordList(mysqlCursor):
    selectSqlQuery = "SELECT keyword FROM keywordtable"
    mysqlCursor.execute(selectSqlQuery)
    return mysqlCursor.fetchall()

if __name__ == "__main__":
    load_dotenv()
    mysqlConnect = pymysql.connect(host=os.environ.get('MYSQL_HOST'), user=os.environ.get('MYSQL_USER'), password=os.environ.get('MYSQL_PASSWORD'), db=os.environ.get('MYSQL_DB_NAME'), charset='utf8')
    mysqlCursor = mysqlConnect.cursor()
    
    insertKeywordList = json.loads(os.environ.get('INSERT_KEYWORD_LIST'))
    deleteKeywordList = json.loads(os.environ.get('DELETE_KEYWORD_LIST'))

    print("insert list: " + str(insertKeywordList))
    print("delete list: " + str(deleteKeywordList))

    print("\n----- insert -----")
    for keyword in insertKeywordList:
        insertKeyword(mysqlCursor, mysqlConnect, keyword.strip())
        
    print("\n----- delete -----")
    for keyword in deleteKeywordList:
        deleteKeyword(mysqlCursor, mysqlConnect, keyword.strip())

    print("\n----- result -----")
    print(selectKeywordList(mysqlCursor))
    mysqlConnect.close()