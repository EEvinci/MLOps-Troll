import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

# import sys
# sys.path.append('/home/lc/lc/Test/thundersvm/python')



def load_data(label_csv_path, x_csv_path):
    """
    加载标签和BERT嵌入向量数据。
    :param label_csv_path: 标签数据文件的路径。
    :param x_csv_path: 嵌入向量数据文件的路径。
    :return: 嵌入向量X和标签y。
    """
    y = pd.read_csv(label_csv_path)['is_troll']  # 假设标签列名为'label'
    x = pd.read_csv(x_csv_path, header=None)
    return x, y


def evaluate_model(label_csv_path, x_csv_path, model_path):
    """
    加载数据和模型，评估模型性能。
    :param label_csv_path: 标签数据文件的路径。
    :param x_csv_path: 嵌入向量数据文件的路径。
    :param model_path: 训练好的模型文件的路径。
    """
    # 加载数据
    X, y = load_data(label_csv_path, x_csv_path)

    # 加载模型
    model = joblib.load(model_path)

    # 使用模型进行预测
    y_pred = model.predict(X)

    # 直接计算评估指标
    precision = precision_score(y, y_pred)
    recall = recall_score(y, y_pred)
    f1 = f1_score(y, y_pred)
    accuracy = accuracy_score(y, y_pred)

    # 打印评估指标
    print(f"精确率 (Precision): {precision:.4f}")
    print(f"召回率 (Recall): {recall:.4f}")
    print(f"F1得分 (F1 Score): {f1:.4f}")
    print(f"准确率 (Accuracy): {accuracy:.4f}")



# 调用函数
label_csv_path = '/home/lc/lc/Test/data/gen_data/comments_cleaned.csv'
x_csv_path = '/home/lc/lc/Test/data/gen_data/embedding_char.csv'
model_path = '/home/lc/lc/Test/model/model.joblib'
evaluate_model(label_csv_path, x_csv_path, model_path)



