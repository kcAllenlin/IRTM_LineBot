import requests
import time
import json
import urllib3
from datetime import datetime,timedelta
from lxml import etree
import csv

import sys #Adding parameter
#from pathlib import Path #Get the file path

#參數
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18362',
    }
#stat = sys.argv[1]
token = 'vXptaR4F72ehsf7lcuiRo9UdCvurQJUWVeabWZYxafR' #Line Notify Token
    
#將資料儲存成CSV檔案
def savefile(beginday,stopday,news):
    filename='cnyes-'+ beginday +'.csv'
    with open(filename, 'a', newline='',encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(news)

#分析網頁資訊
def parse(headers,newsID,k,total,beginday,stopday):    
    fnews_url = 'https://news.cnyes.com/news/id/{}?exp=a'.format(newsID) #原始新聞網址    
    response = requests.get(fnews_url, headers)
    html=etree.HTML(response.content)   
    try: 
        title=html.xpath('//*[@id="content"]/div/div/div[2]/main/div[2]/h1/text()')[0] #新聞標題
        print('第 {} / {} 篇新聞: '.format(k,total),title)     
        posttime=html.xpath('//*[@id="content"]/div/div/div[2]/main/div[2]/div[2]/time/text()')[0] 
        posttime=posttime.split(' ')
        date=posttime[0]#新聞發佈日期
        time=posttime[1]#新聞發佈時間
        content=html.xpath('//*[@id="content"]/div/div/div[2]/main/div[3]/article/section[1]//p/text()')
        content=''.join(content).strip() #新聞內文
        content=content.replace('\n','')
        url=fnews_url.replace('?exp=a','')#原始新聞來源網址
        tag=html.xpath('//*[@id="content"]/div/div/div[2]/main/div[3]/article/section[1]/nav/a//text()')
        tag=','.join(tag).strip() #Tag
        news=[date,time,title,tag,content,url]
        print("news:",news)
        
        # TODO: save to csv
        # #將資訊儲存成檔案(或寫入資料庫)
        # savefile(beginday,stopday,news)
        
    except IndexError as IE:
        print('抓值範圍錯誤')
        print('html:' ,response.text)
        news={"title":None,"date":None,"content":None,"url":None,"tag":None }
    except OSError as OSErr:
        print('OSError:{}'.format(OSErr))
    except requests.exceptions.ConnectionError as REC:
        print('連線錯誤')
    except urllib3.exceptions.ProtocolError as UEP:
        print('連線錯誤')
    return news

#分析文章數量
def crawler(beginday,stopday):   
    #搜尋新聞開始日,格式為 'Y-M-D'
    be_day=beginday
    #搜尋新聞結束日
    st_day=stopday
    #日期格式轉換成時間戳型式
    startday = int(datetime.timestamp(datetime.strptime(be_day, "%Y-%m-%d")))
    endday = int(datetime.timestamp(datetime.strptime(st_day, "%Y-%m-%d"))-1)
    url ='https://news.cnyes.com/api/v3/news/category/tw_stock?startAt={}&endAt={}&limit=30'.format(startday,endday)
    res = requests.get(url, headers)

    newsID_lt=[]
    #獲取搜尋總頁數
    last_page = json.loads(res.text)['items']['last_page']
    #print('總共 {} 頁'.format(last_page))
    # 篩選 newsId 值
    newsIDlist=json.loads(res.text)['items']['data']

    #獲取第一頁各個新聞的 newsId
    for i in newsIDlist:
        newsID=i['newsId']
        newsID_lt.append(newsID)
    #print('正在獲取第 1 頁 newsId')
    time.sleep(1)

    #進行翻頁並獲取各頁面的 newsId
    for p in range(2,last_page+1):
        oth_url ='https://news.cnyes.com/api/v3/news/category/tw_stock?startAt={}&endAt={}&limit=30&page={}'.format(startday,endday,p)
        res=requests.get(oth_url, headers)
        #print('正在獲取第 {} 頁 newsId'.format(p))
        # 獲取新聞的newsId
        newsIDlist=json.loads(res.text)['items']['data']
        for j in newsIDlist:        
            newsID=j['newsId']
            newsID_lt.append(newsID)
        #抓取每頁newsId的延遲時間
        time.sleep(1)
    
    # 由 newsId 獲取詳細新聞內容
    for k,n in enumerate(newsID_lt):    
        data=parse(headers,n,k+1,len(newsID_lt),beginday,stopday)
        #抓取每篇完整新聞的延遲時間
        time.sleep(0.5)
    
    return data # TODO: return要改

def line_notify(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type" : "application/x-www-form-urlencoded" 
    }
    
    payload = {'message': msg}
    r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
    return r.status_code

if __name__ == '__main__':
    current_time = datetime.now()
    currentyear = current_time.year  # 爬取新聞年分
    currentmonth = current_time.month    #爬取新聞月份
    currentday = current_time.day-1    # 爬取新聞日期 #TODO:日期要加回來

    if currentmonth < 10:
        beginday = '{}-0{}-{}'.format(currentyear, currentmonth, currentday)
    else:
        beginday = '{}-{}-{}'.format(currentyear, currentmonth, currentday)
    begindate = datetime.strptime(beginday, '%Y-%m-%d')
    stopdate = begindate + timedelta(days=1)
    stopday = stopdate.strftime('%Y-%m-%d')

    msg = crawler(beginday, stopday)
    if msg != None:
      line_notify(token, msg)
      print('line notify success')
    else:
      print('line notify fail')
