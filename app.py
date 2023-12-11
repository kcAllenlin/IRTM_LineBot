from flask import Flask, request, abort, session
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, TextSendMessage, MessageEvent, MemberJoinedEvent
import os
import csv
import pandas as pd

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # 設定 Flask 會話的 secret key

line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

#建立字典{使用者id:公司}
user_company = {}
#記錄所有有效輸入的使用者id
user_id_lst = []

#讀取現有公司
df = pd.read_csv("./data/stockname.csv", header=None)
stock_name = df.iloc[:, 1].tolist()

#定義主動傳送警示訊息的函式
#def send_alert_message(user_id, user_company):
def send_alert_message():    
    try:
        for user in user_id_lst:
            if user_company[user] != None:
                with open("./data/analyisis.csv", "r") as csvfile:
                    data = csv.DictReader(csvfile)
                    for row in data:
                        if row["name"] == user_company[user]:
                            if row["type"] == "n":
                                message = [TextSendMessage(f"您的公司：{user_company[user]}，今天有一篇新聞的情緒為負"), TextSendMessage(f"網址：{row['url']}")]
                                line_bot_api.push_message(user, message)
        # with open("./data/analyisis.csv", "r") as csvfile:
        #     data = csv.DictReader(csvfile)
        #     for row in data:
        #         if row["name"] == user_company[user_id]:
        #             if row["type"] == "n":
        #                 message = [TextSendMessage(f"您的公司：{user_company[user_id]}，今天有一篇新聞的情緒為負"), TextSendMessage(f"網址：{row['url']}")]
        #                 line_bot_api.push_message(user_id, message)
    except:
        pass

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    msg = event.message.text

    if user_id not in user_company:
        user_company[user_id] = None

    if msg == "我的公司":
        if user_company[user_id] != None:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(f'您目前欲查詢的公司為：{user_company[user_id]}'))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="您目前尚未設定欲查詢的公司"))
    else:
        if msg in stock_name:
            user_company[user_id] = msg
            user_id_lst.append(user_id)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(f'您輸入的公司為：{user_company[user_id]}'))
        else:
            if user_company[user_id] != None:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(f'查無此公司，您目前欲查詢的公司仍為：{user_company[user_id]}'))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查無此公司，請重新輸入"))

# 歡迎事件
@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)


@app.route("/callback", methods=['POST', 'HEAD'])
def callback():
    #如果是HEAD請求，即UptimeRobot的監控
    if request.method == 'HEAD':
        return 'OK'

    #如為POST請求，處理LineBot Webhook
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

if __name__ == "__main__":
    send_alert_message()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
