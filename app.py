from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

import certifi
ca = certifi.where()

client = MongoClient('mongodb+srv://test:sparta@cluster0.bvp5m.mongodb.net/Cluster0?retryWrites=true&w=majority',tlsCAFile=ca)
db = client.dbsparta

@app.route('/')
def home():
        return render_template('SignUp.html')

@app.route('/sign_up/save', methods =['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_receive']

    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,   # 아이디
        "password": password_hash,      # 비밀번호
        "nickname": nickname_receive    # 닉네임
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

    #ID의 중복확인
@app.route('/sign_up/check_dup',methods = ['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result':'success' , 'exists': exists})

@app.route('/sign_up/check_dup_nick')
def check_dup_nick():
    nickname_receive = request.form['nickname_give']
    exsist = bool(db.users.find_one({'nickname': nickname_receive}))
    return jsonify({'result':'success' , 'exsist':exsist})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)