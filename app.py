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

client = MongoClient('mongodb+srv://test:sparta@cluster0.bvp5m.mongodb.net/Cluster0?retryWrites=true&w=majority',
                     tlsCAFile=ca)
db = client.dbsparta


@app.route('/')
def home():
    return render_template('SignUp.html')

@app.route('/mainpage')
def home2():
    return render_template('mainpage.html')

@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']

    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "nickname": nickname_receive  # 닉네임
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

    # ID의 중복확인


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))

    return jsonify({'result': 'success', 'exists': exists})


@app.route('/sign_up/check_dup_nick', methods=['POST'])
def check_dup_nick():
    nickname_receive = request.form['nickname_give']
    exists = bool(db.users.find_one({'nickname': nickname_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/sign_in', methods=['POST'])
def sign_in():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    result = db.users.find_one({'username':username_receive,'password':pw_hash })
    # db로부터 일치하는 ID와 PW가 있다고 응답이 있었을 시
    print(result)

    if result is not None:
        payload = {
            'id': username_receive,
            # datetime에 내장되어 있는 timedelta클래스는 기간을 표현하기 위해 사용된다.
            # 24시간 유지되는 토큰을 표현
            'exp': datetime.utcnow() + timedelta(seconds= 60*60*24)
        }
        token = jwt.encode(payload,SECRET_KEY,algorithm='HS256').decode('utf-8')

        return jsonify({'result':'success','token': token})
        #응답이 없었을때
    else:
        return jsonify({'result': 'fail', 'msg': "아이디 또는 비밀번호가 일치하지 않습니다."})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)