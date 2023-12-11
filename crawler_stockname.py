import pandas as pd
import requests
import csv
#先建立上市和上櫃公司代號及名稱的字典，以便篩選新聞
stock_dict = {}
stockname_dict={}
mode=[2,4]
for i in mode:
    stockname_url="https://isin.twse.com.tw/isin/C_public.jsp?strMode={}".format(i)
    res = requests.get(stockname_url)
    df = pd.read_html(res.text)[0]
    # 設定column名稱
    df.columns = df.iloc[0]
    # 刪除第一行
    df = df.iloc[1:]
    # 先移除row，再移除column，超過三個NaN則移除
    df = df.dropna(thresh=3, axis=0).dropna(thresh=3, axis=1)
    df = df[['有價證券代號及名稱']]
    df = df.reset_index(drop=True)
    for index, row in df.iterrows():
        # 使用 split 將 '有價證券代號及名稱' 列的數據分割成股票代號和股票名稱
        stock_info = row['有價證券代號及名稱'].split()    
        # 檢查列表的長度
        if len(stock_info) >= 2:
        # 提取股票代號和股票名稱
            stock_code = stock_info[0]
            stock_name = stock_info[1]
        
        # 將股票代號和股票名稱添加到字典中
            stock_dict[stock_code] = stock_name
        else:
            print(f"Skipping row {index + 1} due to insufficient data.")

for num,name in stock_dict.items():
    stockname_dict[name] = stock_dict[num]
    
#stockname="stockname.csv"
stockfile = "./data/stockname.csv"
with open(stockfile,"w",newline='') as stocknamecsv :
    writer = csv.writer(stocknamecsv)
    for stock_num, stock_name in stock_dict.items():
        writer.writerow([stock_num, stock_name])
    #for name,stock_name in stockname_dict.items():
       # writer.writerow([name, stock_name])
print("{}已經建立".format(stockfile))