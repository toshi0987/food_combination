from flask import Flask, request, abort, render_template, redirect

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from flask_sqlalchemy import SQLAlchemy
import os
import re
#import psycopg2


DATABASE_URL = os.environ['DATABASE_URL']
#conn = psycopg2.connect(DATABASE_URL, sslmode='require')

app = Flask(__name__)
#DATABASE_URL="postgresql-regular-33495"
#["DATABASE_URL"]はheroku側の環境変数
uri=os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri=uri.replace("postgres://","postgresql://",1)
app.config['SQLALCHEMY_DATABASE_URI'] =uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

###データベース用クラス####
class Post(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    mainname=db.Column(db.String(80),nullable=False)
    subname=db.Column(db.String(80),nullable=False)
    comb_state=db.Column(db.Integer,nullable=False)


YOUR_CHANNEL_ACCESS_TOKEN="f3fyc4UBKCodzjNjwRQLnAL93baaMABwZhn93AR0QGdbjiWpOJn5DzfKj8JWBr/pX6HoVLErj1lfY1azK2FFtFevxUgWj9YzSd+o2OzEwrTonIiK6GEfWRBCFKY62RzOidsKv3IDnNe3/VcKI/ZOdgdB04t89/1O/w1cDnyilFU="
YOUR_CHANNEL_SECRET="595fd3a35c45b776b49bb534ee654606"

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

###表記揺れ対策用辞書###
spell_dict={
    "ほうれんそう":"ホウレンソウ",
    "ほうれん草":"ホウレンソウ",
    "うなぎ":"ウナギ",
    "鰻":"ウナギ",
    "てんぷら":"天ぷら",
    "かに":"カニ",
    "蟹":"カニ",
    "にんじん":"ニンジン",
    "人参":"ニンジン",
    "わかめ":"ワカメ",
    "なす":"ナス",
    "茄子":"ナス",
    "しらす":"シラス",
    "ひじき":"ヒジキ",
    "とまと":"トマト",
    "ポーク":"豚肉",
    "れもん":"レモン",
    "ゆでたまご":"ゆで卵",
    "すいか":"スイカ",
    "西瓜":"スイカ",
    "大根":"ダイコン",
    "だいこん":"ダイコン",
    "ねぎ":"ネギ",
    "葱":"ネギ",
    "長ネギ":"ネギ",
    "ながねぎ":"ネギ",
    "長葱":"ネギ",
    "長ねぎ":"ネギ",
    "ナガネギ":"ネギ",
    "蕎麦":"そば",
    "ソバ":"そば",
    "漬け物":"漬物",
    "つけもの":"漬物",
    "漬けもの":"漬物",
    "茗荷":"ミョウガ",
    "みょうが":"ミョウガ",
    "きゅうり":"キュウリ",
    "胡瓜":"キュウリ",
    "タマネギ":"たまねぎ",
    "玉葱":"たまねぎ",
    "玉ねぎ":"たまねぎ",
    "玉ネギ":"たまねぎ",
    "オニオン":"たまねぎ",
    "にんにく":"ニンニク",
    "大蒜":"ニンニク",
    "葫":"ニンニク",
    "ごま":"ゴマ",
    "胡麻":"ゴマ"
}

##データベース探索##
def search(name):
    ##表記揺れ対策##
    if name in spell_dict.keys():
        name=spell_dict[name]
    result=Post.query.all()
    bad_res="悪い組み合わせ："+"\n"
    good_res="良い組み合わせ："+"\n"
    url_res="https://kurashiru.com/search?query="
    and_key="%E3%80%80"
    url_res+=name
    for r in result:
        if r.mainname==name:
            if r.comb_state==-1:
                if not(r.subname in bad_res):
                    bad_res+=r.subname+"\t"
            else:
                if not(r.subname in good_res):
                    good_res+=r.subname+"\t"
                    url_res+=and_key+r.subname
        if r.subname==name:
            if r.comb_state==-1:
                if not(r.mainname in bad_res):
                    bad_res+=r.mainname+"\t"
            else:
                if not(r.mainname in good_res):
                    good_res+=r.mainname+"\t"
                    url_res+=and_key+r.mainname
    res=[]
    res.append(bad_res)
    res.append(good_res)
    res.append(url_res)
    return res


        
    
    

@app.route("/")
def index():
    #return "hello world"
    posts=Post.query.all()
    return render_template("index.html",posts=posts)

@app.route("/register",methods=["POST","GET"])
def register():
    
    if request.method=="POST":
        if request.form["mainname"]!='' and request.form["subname"]!='':
            mainname=request.form["mainname"]
            subname=request.form["subname"]
            comb_state=request.form["goodorbad"]

            post=Post(mainname=mainname,subname=subname,comb_state=comb_state)
            db.session.add(post)
            db.session.commit()
        return redirect("/")
    return render_template("register.html")

@app.route("/<int:id>/delete",methods=["GET"])
def delete(id):
    post=Post.query.get(id)
    db.session.delete(post)
    db.session.commit()
    return redirect("/")


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    response=search(event.message.text)
    #res_mes="☆☆☆おすすめレシピ☆☆☆"
    res_mes="▼おすすめレシピ"
    """
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))
        """
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response[0]+"\n"+response[1]+"\n"+
                        res_mes+"\n"+response[2]))
     


if __name__ == "__main__":
    port=os.getenv("PORT")
    app.run(host="0.0.0.0",port=port)