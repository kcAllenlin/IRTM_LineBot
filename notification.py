import psycopg2
import os
from linebot import LineBotApi
from linebot.models import TextSendMessage
import pandas as pd 

db_url = os.environ['DATABASE_URL']
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))

# data
df = pd.read_csv("./data/analysis.csv")

def get_all_user_ids():
    connection = psycopg2.connect(db_url)

    cursor = connection.cursor()
    cursor.execute("SELECT user_id FROM user_data")
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return [row[0] for row in result] if result else []

def get_company_name_from_database(user_id):
    connection = psycopg2.connect(db_url)

    cursor = connection.cursor()
    cursor.execute("SELECT company_name FROM user_data WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    if result:
        return result[0]
    else:
        return None

# send_alert_message()
def send_alert_message():    
    try:
        user_ids = get_all_user_ids()
        for user in user_ids:
            company_name = get_company_name_from_database(user)
            if company_name != None:
                for i in range(df.shape[0]):
                    row = df.iloc[i]
                    if row["name"] == company_name:
                        if row["type"] == "n":
                            message = "您的公司：{}，今天有一篇新聞的情緒為負 \n網址：{} \n文章概要：{}".format(company_name, row['url'], row['summary'])
                            #message = [TextSendMessage(f"您的公司：{company_name}，今天有一篇新聞的情緒為負"), TextSendMessage(f"網址：{row['url']}"), TextSendMessage(f"文章概要：{row['summary']}")]
                            line_bot_api.push_message(user, TextSendMessage(text = message))
    except:
        pass

send_alert_message()