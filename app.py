from flask import Flask, request, abort, session
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, TextSendMessage, MessageEvent, MemberJoinedEvent
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # 設定 Flask 會話的 secret key
app.config['SESSION_TYPE'] = 'filesystem'  # 設定儲存類型


line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if msg == "我的公司":
        if "company" in session:
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=31)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(f'您目前欲查詢的公司為：{session["company"]}'))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="您目前尚未設定欲查詢的公司"))
    else:
        session['company'] = msg
        line_bot_api.reply_message(event.reply_token, TextSendMessage(f'您輸入的公司為：{session["company"]}'))

# 歡迎事件
@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)

# 設定 Flask 應用程式的端點
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
