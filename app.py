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
    return render_template('index.html')

@app.route('/review-savepage')
def home3():
    return render_template('review-save.html')

@app.route('/review',methods=['POST'])
def save_review():
    # 토큰을 가지고 있는 유저만 작성할 수 있게한다.
    token_receive = request.cookies.get('mytoken')

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 리뷰하기 버튼 눌렀을 때 정보를 mongoDB클라우드에 저장한다.
        # 단 사진은 경로만 저장

        #form_data.append("file_give", file)
        #form_data.append("comment_give", comment)
        #form_data.append("store_give", store)
        #form_data.append("address_give", address)

        # payload에는 뭐가 들어있지?
        #유저 id 저장
        username = db.users.find_one({'username':payload["id"]})
        address = request.form['address_give']
        store = request.form['store_give']
        comment = request.form['comment_give']

        file = request.files["file_give"]
        filename = secure_filename(file.filename)
        print(filename)
        # 확장자 저장 리스트의 마지막에 접근
        extension = filename.split(".")[-1]
        print(extension)
        # 파일 경로 저장
        file_path = f"static/{filename}"
        print(file_path)
        file.save(file_path)
        doc ={
            "address": address,
            "store": store,
            "comment": comment,
            "file_path": file_path,
            "file_name": filename
        }
        db.review.insert_one(doc)

        return jsonify({'msg':'성공햇습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("/"))
@app.route('/review-save',methods=['GET'])
def get_data():
    data = list(db.review.find({},{'_id':False}))
    return jsonify({'save-review': data})

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
        token = jwt.encode(payload,SECRET_KEY,algorithm='HS256')

        return jsonify({'result':'success','token': token})
        #응답이 없었을때
    else:
        return jsonify({'result': 'fail', 'msg': "아이디 또는 비밀번호가 일치하지 않습니다."})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)