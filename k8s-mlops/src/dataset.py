import sys
sys.path.append("/root/train/src")

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, BigInteger
from threading import Thread

import mlflow

from datetime import datetime
import time
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from joblib import load
import train_embed
import train_pre_csv
import train_svm

from functools import wraps
from flask_httpauth import HTTPBasicAuth
from flask import g

from flask_cors import CORS, cross_origin

# 创建 Flask 应用
app = Flask(__name__)

CORS(app)  # 在app上启用全局跨域支持

# 设置HTTP基本认证
auth = HTTPBasicAuth()

# 设置MLflow跟踪URI，用于模型版本管理
mlflow.tracking.set_tracking_uri(os.environ["TRACKING_URL"])

# 配置数据库
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# 时间戳转化为“YYYY.MM.DD”
def format_unix_time(unix_time):
    return datetime.utcfromtimestamp(unix_time).strftime('%Y.%m.%d')

# 用户模型定义
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    
    def set_password(self, password):
        # 存储明文密码
        self.password = password
    def check_password(self, password):
        # 比较明文密码
        return self.password == password

# 根据用户名查询用户，并验证密码
@auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        g.user = user  # 存储用户信息到全局对象g
        return True
    return False

# 角色权限装饰器
def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if g.user.role not in roles:
                return jsonify({"error": "Unauthorized"}), 403
            return func(*args, **kwargs)
        return decorated_function
    return decorator

# 接口一
# 登录接口，只进行基本身份验证
@app.route('/login', methods=['POST'])
@auth.login_required
def login():
    user = g.user
    if user:
        return jsonify({"username": user.username, "role": user.role}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401

# 接口二
# 受保护的区域，需要管理员权限 管理员测试接口
@app.route('/secure', methods=['GET'])
@auth.login_required
@role_required("admin")
def secure_area():
    return f"Hello, {g.user.username}! You are viewing a secure area."

# 接口三
# 创建用户，只有管理员有权限
@app.route('/users_creation', methods=['POST'])
@auth.login_required
@role_required("admin")
def create_user():
    """
    JSON 字段输入:
    {
        "username": "user1", 
        "password": "pass1", 
        "role": "user"
    }
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default role is 'user'
    if username and password:
        if User.query.filter_by(username=username).first():
            return jsonify({"message": "Username already exists"}), 409
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "message": "User created"
        }), 201
    return jsonify({"message": "Missing username or password"}), 400

# 接口四
# 搜索指定用户
@app.route('/users/<username>', methods=['GET'])
@auth.login_required
@role_required("admin")
def get_user(username):
    """
    根据用户名检索用户的信息
    无论结果如何，都会返回状态代码 200 的 JSON 响应
    并在 JSON 正文中包含一个“代码”来指示成功或失败

    无需 JSON 输入 
    URL 中指定用户名
    """
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({
            "code": 1,
            "message": "User found",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }), 200
    else:
        return jsonify({
            "code": 0,
            "message": "User not found"
        }), 200

# 接口五
# 更新指定用户信息
@app.route('/users/<username>', methods=['PUT'])
@auth.login_required
@role_required("admin")
def update_user(username):
    """
    根据用户名更新用户的密码和角色
    无论结果如何，都会返回状态代码 200 的 JSON 响应
    并在 JSON 正文中包含一个“代码”来指示成功或失败

    需要 JSON 输入：
        {
            "password": "newpass", # 可选
            "role": "admin" # 可选
        }
    """
    user = User.query.filter_by(username=username).first()
    if user:
        data = request.json
        if 'password' in data:
            user.set_password(data['password'])
        if 'role' in data:
            user.role = data['role']
        
        db.session.commit()
        return jsonify({
            "code": 1,
            "message": "User updated",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }), 200
    else:
        return jsonify({
            "code": 0,
            "message": "User not found"
        }), 200

# 接口六
# 删除指定用户
@app.route('/users/<username>', methods=['DELETE'])
@auth.login_required
@role_required("admin")
def delete_user(username):
    """
    根据用户名删除用户，并返回已删除用户的 id、用户名和角色。
    
    无需 JSON 输入 
    URL 中指定用户名。
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        return jsonify({"code": 0, "message": "User not found"}), 200

    user_info = {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }
    db.session.delete(user)
    db.session.commit()
    return jsonify({
        "code": 1,
        "message": "User deleted successfully",
        "deletedUser": user_info
    }), 200

# 接口七
# 分页显示所有用户
@app.route('/users', methods=['GET'])
@auth.login_required
@role_required("admin")
def list_users():
    """
    支持在URL中使用查询参数“page”和“per_page”进行分页。
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items

    return jsonify({
        "list": [
            {
                "id": user.id,
                "username": user.username,
                "password": user.password,  # Assuming this is a hashed password
                "role": user.role
            } for user in users
        ],
        "total": pagination.total
    }), 200



### 定义数据模型，用于存储数据集的信息
class Dataset(db.Model):
    __tablename__ = "dataset"  # 数据表的名称
    # 定义表中的各个列
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=False)  # 数据文本
    label = db.Column(db.String, nullable=False)  # 数据标签
    source = db.Column(db.Integer)  # 数据来源
    create_time = db.Column(db.BigInteger)  # 创建时间

    # 将数据记录转换为字典形式，便于JSON序列化
    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "label": self.label,
            "source": self.source,
            "create_time": self.create_time,
        }

# 计算并返回数据库中的数据集数量
def count_datasets():
    count = Dataset.query.count()
    return jsonify({"count": count})

# 异步任务函数，用于处理数据预测和存储
def async_task(data, label):
    create_time = int(time.time())
    formatted_time = format_unix_time(create_time)
    # 创建一个新的Dataset对象，并保存到数据库
    predict_result = Dataset(
        text=data["text"], label=label, source=1, create_time=create_time
    )
    db.session.add(predict_result)
    db.session.commit()
    # 每100条数据后触发一次模型训练
    if Dataset.query.count() % 10 == 0:
        # 可以选择直接在这里调用训练脚本，或者通过Kubernetes API启动训练
        train_pre_csv.main()
        train_embed.main()
        train_svm.main()

# 存储已加载的模型，避免重复加载
MODEL_SET = {}

# 获取或加载指定的模型
def get_model(name, ver):
    if (name, ver) not in MODEL_SET:
        model = mlflow.pyfunc.load_model(model_uri=f"models:/{name}/{ver}")
        MODEL_SET[(name, ver)] = model
    return MODEL_SET[(name, ver)]

# 接口八
# 模型预测接口，接收数据并返回预测结果
@app.route("/predict", methods=["POST"])
@auth.login_required
@role_required('admin','user')
def predict_text():
    """
    JSON 输入示例：
    {
        "model_name": "my_model",
        "model_version": "v1",
        "text": "This is a sample text."
    }
    """
    data = request.json
    model = get_model(data["model_name"], data["model_version"])

    # 加载向量化器
    vectorizer = load('/root/data/model/tfidf_vectorizer.joblib')
    # svd = load('/root/data/model/svd.joblib')
    
    # 使用向量化器转换文本
    tfidf_matrix = vectorizer.transform([data["text"]])
    # reduced_matrix = svd.transform(tfidf_matrix)

    # 进行预测
    label = model.predict(tfidf_matrix)[0]

    # 创建新的数据集条目
    create_time = int(time.time())
    new_dataset = Dataset(
        text=data["text"], label=int(label), source=1, create_time=create_time
    )
    db.session.add(new_dataset)
    db.session.commit()

    dataset_info = new_dataset.to_dict()
    dataset_info['create_time'] = format_unix_time(create_time)

    return jsonify({"code": 1, "data": dataset_info}), 200

# 接口九
# 列出所有已注册的模型
@app.route("/models", methods=["GET"])
@auth.login_required
@role_required('admin','user')
def list_models():
    """
    不需要 JSON 输入
    返回所有模型列表
    """
    registered_models = mlflow.search_registered_models()
    models_list = []
    for model in registered_models:
        model_info = {"name": model.name, "versions": []}
        for version in model.latest_versions:
            version_info = {
                "version": version.version,
                "stage": version.current_stage,
                "description": version.description,
                "creation_time": version.creation_timestamp,
            }
            model_info["versions"].append(version_info)
        models_list.append(model_info)
    # try:
    #     model = get_model("mlops", "2")
    #     print("模型加载成功")
    # except Exception as e:
    #     print(f"模型加载失败: {e}")
    # try:
    #     test_input = ["这是一个测试文本。"]
    #     prediction = model.predict(test_input)
    #     print("预测结果:", prediction)
    # except Exception as e:
    #     print(f"预测过程中出错: {e}")
    return jsonify(models_list)

# 接口十
# 添加训练数据，只有admin可以操作
@app.route("/dataset", methods=["POST"])
@auth.login_required
@role_required("admin")
def create_dataset():
    """
    JSON 输入示例：
    {
        "text": "text",
        "label": "0/1",
        "source": "source"
    }
    """
    data = request.json
    create_time = int(time.time())
    formatted_create_time = datetime.utcfromtimestamp(create_time).strftime('%Y.%m.%d')

    new_dataset = Dataset(
        text=data["text"],
        label=data["label"],
        source=data["source"],
        create_time=create_time,
    )
    db.session.add(new_dataset)
    db.session.commit()

    dataset_info = new_dataset.to_dict()
    dataset_info['create_time'] = formatted_create_time

    return jsonify({"code": 1, "data": dataset_info}), 200

# 接口十一
# 根据id或label查找特定训练数据
@app.route("/datasets/search", methods=["GET"])
@auth.login_required
@role_required("admin")
def search_datasets():
    dataset_id = request.args.get('dataset_id', type=int)
    label = request.args.get('label', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if dataset_id is not None:
        dataset = Dataset.query.get(dataset_id)
        if dataset:
            if label is not None and dataset.label != label:
                return jsonify({"code": 0, "error": "No datasets found with the provided criteria, please check your label"}), 200
            else:
                return jsonify({
                    "data": [dataset.to_dict()],
                    "page": 1,
                    "pages": 1,
                    "per_page": 1,
                    "total": 1
                }), 200
        else:
            return jsonify({"code": 0, "error": "No dataset found with the provided ID"}), 200

    query = Dataset.query
    if label is not None:
        query = query.filter_by(label=label)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    datasets = pagination.items

    if not datasets:
        return jsonify({"code": 0, "error": "No datasets found with the provided label"}), 200

    return jsonify({
        "data": [dataset.to_dict() for dataset in datasets],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "total": pagination.total
    }), 200

# 接口十二
# 更新指定训练数据，只有admin可以操作
@app.route("/dataset/<int:dataset_id>", methods=["PUT"])
@auth.login_required
@role_required("admin")
def update_dataset(dataset_id):
    """
    根据 dataset_id 更新数据集条目
    需要 JSON 输入（所有字段可选）：
        {
            "text": "new text",
            "label": "new label",
            "source": "new source"
        }
    """
    dataset = Dataset.query.get(dataset_id)
    if dataset is None:
        return jsonify({"code": 0, "error": "Dataset not found"}), 200

    data = request.json
    dataset.text = data.get("text", dataset.text)
    dataset.label = data.get("label", dataset.label)
    dataset.source = data.get("source", dataset.source)
    dataset.create_time = int(time.time())

    db.session.commit()
    dataset_info = dataset.to_dict()
    dataset_info['create_time'] = format_unix_time(dataset.create_time)

    return jsonify({"code": 1, "data": dataset_info}), 200

# 接口十三
# 删除训练数据，只有admin可以操作
@app.route("/dataset/<int:dataset_id>", methods=["DELETE"])
@auth.login_required
@role_required("admin")
def delete_dataset(dataset_id):
    """
    不需要 JSON 输入
    """
    dataset = Dataset.query.get(dataset_id)
    if dataset is None:
        return jsonify({"code": 0, "message": "Dataset not found"}), 200
    
    # 将创建时间转换为可读格式
    formatted_time = format_unix_time(dataset.create_time)
    
    dataset_info = {
        "id": dataset.id,
        "text": dataset.text,
        "label": dataset.label,
        "source": dataset.source,
        "delete_time": formatted_time  # 使用格式化后的时间
    }
    db.session.delete(dataset)
    db.session.commit()
    return jsonify({
        "code": 1,
        "message": "Dataset deleted successfully",
        "deletedDataset": dataset_info
    }), 200



# 接口十四
# 查看所有训练数据
@app.route("/datasets", methods=["GET"])
@auth.login_required
@role_required("admin")
def list_datasets():
    """
    该端点支持分页 可以指定页码
    使用“page”和“per_page”查询参数的每页数据集数
    示例： GET /datasets?page=3&per_page=20
    """
    # 从查询参数中获取页码和每页记录数，设置默认值
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 使用 paginate 方法进行分页查询
    pagination = Dataset.query.paginate(page=page, per_page=per_page, error_out=False)
    datasets = pagination.items

    return jsonify({
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "data": [dataset.to_dict() for dataset in datasets],
        "total": pagination.total
    })

# 测试接口
@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "This is a test endpoint"})
    
# 创建默认用户
def create_default_users():
    admin_exists = User.query.filter_by(username='admin').first()
    if not admin_exists:
        admin_user = User(
            username='admin',
            password='123',  # 使用安全的方式存储密码
            role='admin'
        )
        db.session.add(admin_user)
    
    user_exists = User.query.filter_by(username='user').first()
    if not user_exists:
        regular_user = User(
            username='user',
            password='123',
            role='user'
        )
        db.session.add(regular_user)

    db.session.commit()  # 只有在添加了新用户时才需要提交


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # 确保所有数据表都已创建
        create_default_users()  # 创建默认用户

    app.run(host="0.0.0.0", port=8000,debug=True)