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

@app.route('/mainpage/<username>')
def home2(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False

        user_info = db.users.find_one({"username": username}, {"_id": False})
        name = user_info['nickname']


        return render_template('index.html', user_info=name, status=status)

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):

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

        dbnickname = db.users.find_one({'username':payload["id"]},{'nickname':1,'_id':0})
        nickname = dbnickname['nickname']
        print(nickname)
        # 확장자 저장 리스트의 마지막에 접근
        extension = filename.split(".")[-1]

        # 파일 경로 저장(왜 f가붙지 앞에?)
        file_path = f"static/{filename}"

        time = datetime.now()
        temp = {'date': time.strftime(('%Y년 %m월 %d일 %H시'))}
        savedate = temp['date']

        #포스트 개수만 받아오기
        count = db.users.find_one({'username':payload["id"]},{'numofpost':1,'_id':0})

        print(count)
        numberofpost = count['numofpost']
        numberofpost = numberofpost + 1

        # 리뷰등록시 그 유저의 포스트 개수를 1증가
        db.users.update_one({'username': payload["id"]}, {'$set': {'numofpost': numberofpost}})
        print(numberofpost)

        file.save(file_path)
        doc ={
            "address": address,
            "store": store,
            "comment": comment,
            "file_path": file_path,
            "file_name": filename,
            "savedate": savedate,
            "nickname":nickname,
            "numofpost":numberofpost
        }
        db.review.insert_one(doc)

        print('success2')
        return jsonify({'msg':'성공했습니다.','username':payload['id']})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        print('fail2')
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

    # 삭제를 위한 그 유저의 포스트 개수 추가 20220512
    numberofpost = 0

    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,     # 비밀번호
        "nickname": nickname_receive,  # 닉네임
        "numofpost": numberofpost      # 포스트개수
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

@app.route('/delete_post',methods=['POST'])
def delete_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        postnum_receive = request.form['postnum_give']

        # 토탈 포스트개수를 받아와서 -1시켜줄 예정
        temp = db.users.find_one({'username':payload["id"]},{'numofpost':1 ,'_id':0})

        totalpostnum = temp['numofpost']

        print(totalpostnum,postnum_receive)

        # 포스트 번호와 일치하는 포스트를 DB클라우드로부터 삭제
        dbnickname = db.users.find_one({'username': payload["id"]}, {'nickname': 1, '_id': 0})
        nickname = dbnickname['nickname']

        db.review.delete_one({'$and': [{'nickname': nickname}, {'numofpost': int(postnum_receive)}]})
        # 아래 문법이 잘못된 거 였어서 삭제햇을때 이상한 포스팅이 삭제되었다. 위가 올바른 문법
        # db.review.delete_one({'nickname': nickname} and {'numofpost': int(postnum_receive)})
        # db.review.delete_one({'nickname':nickname,'numofpost':postnum_receive})

        totalpostnum = totalpostnum - 1
        # 여기 처음써보는거라 확인할 필요 있음 그 유저의 토탈 포스트개수 -1 일단 여기 되는거 확인
        db.users.update_one({'username':payload['id']},{'$set':{'numofpost': totalpostnum}})

        #포스트 넘버 를 바꿔주는 위치의 잘못?
        doc = list(db.review.find({'nickname': nickname}, {'numofpost': 1, '_id': False}))

        # 결론적으로 db 의 update나 delete문법안에 조건식을 넣는다던지 다룰줄 몰라서 포스트 번호 업데이트하는데 시간을 써버렷다.
        for i in range(totalpostnum):
            if doc[i]['numofpost'] > int(postnum_receive):
                num = (doc[i]['numofpost'])
                print(num)
                db.review.update_one({'nickname': nickname} and {'numofpost':num}, {'$set': {'numofpost': num-1}})

        doc = list(db.review.find({'nickname': nickname}, {'numofpost': 1, '_id': False}))
        print(doc)
        return jsonify({'result':'success'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template('index.html')

    return jsonify('msg','삭제했습니다.')

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)