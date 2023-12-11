import requests
import time
import json
import urllib3
from datetime import datetime,timedelta
from lxml import etree
import csv
import pandas as pd

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edge/18.18362',
    }


stockname_dict={}
with open ("./data/stockname.csv","r")as stocknamefile:
    rows=csv.reader(stocknamefile)
    for row in rows:
        stocknum=row[0]
        stockname=row[1]
        stockname_dict[stocknum]=stockname
        
stock_dict={}        
for num,name in stockname_dict.items():
    stock_dict[name] = stockname_dict[num]
        
#將爬蟲資料儲存成CSV檔案
def savefile(beginday,stopday,news):
    #filename='cnyes-'+ beginday +'.csv'
    file='./data/raw.csv'
    with open(file, 'a', newline='',encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(news)
    
#分析網頁資訊
def parse(headers,newsID,k,total,beginday,stopday):    
    fnews_url = 'https://news.cnyes.com/news/id/{}?exp=a'.format(newsID) #原始新聞網址    
    response = requests.get(fnews_url, headers)
    html=etree.HTML(response.content)
    news=[]
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
        tags=html.xpath('//*[@id="content"]/div/div/div[2]/main/div[3]/article/section[1]/nav/a//text()')
        # Check if any tag in the list is in the stockname_dict
        stock_related_tags = [tag for tag in tags if tag in stock_dict]
        if len(stock_related_tags)==1:
            news = [date, time, title, stock_related_tags[0], content, url]
            print("news:", news)
            #將資訊儲存成檔案(或寫入資料庫)
            savefile(beginday, stopday, news)  
    except IndexError as IE:
        print('抓值範圍錯誤')
        print('html:' ,response.text)
        news={"title":None,"date":None,"content":None,"url":None,"tags":None }
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
    print('總共 {} 頁'.format(last_page))
    # 篩選 newsId 值
    newsIDlist=json.loads(res.text)['items']['data']

    #獲取第一頁各個新聞的 newsId
    for i in newsIDlist:
        newsID=i['newsId']
        newsID_lt.append(newsID)
    print('正在獲取第 1 頁 newsId')
    time.sleep(1)

    #進行翻頁並獲取各頁面的 newsId
    for p in range(2,last_page+1):
        oth_url ='https://news.cnyes.com/api/v3/news/category/tw_stock?startAt={}&endAt={}&limit=30&page={}'.format(startday,endday,p)
        res=requests.get(oth_url, headers)
        print('正在獲取第 {} 頁 newsId'.format(p))
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

if __name__ == '__main__':
    current_time = datetime.now()
    # 爬取前一天到今天的新聞(每日8:30am執行)
    yesterday = current_time - timedelta(days=1)
    yesterday_year = yesterday.year  # 爬取新聞年分
    yesterday_month = yesterday.month    #爬取新聞月份
    yesterday_day = yesterday.day    # 爬取新聞日期

    if yesterday_month < 10:
        beginday = '{}-0{}-{}'.format(yesterday_year, yesterday_month, yesterday_day)
    else:
        beginday = '{}-{}-{}'.format(yesterday_year, yesterday_month, yesterday_day)
    begindate = datetime.strptime(beginday, '%Y-%m-%d') 
    stopdate = current_time + timedelta(days=1) 
    stopday = stopdate.strftime('%Y-%m-%d')

    crawler(beginday, stopday) #昨日到今日