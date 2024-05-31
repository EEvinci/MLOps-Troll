import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
import joblib
import logging

# import sys
# sys.path.append('/home/lc/lc/Test/thundersvm/python')

# from thundersvm import SVC
from sklearn.svm import SVC

# 定义日志配置
logging_file = '/home/lc/lc/Lecture_Design/model/model_training.log'
logging.basicConfig(filename=logging_file, level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')


def load_data(label_csv_path, x_csv_path):
    """
    从CSV文件中加载标签和特征数据。
    
    Args:
        label_csv_path (str): 标签数据文件路径。
        x_csv_path (str): 特征数据文件路径。
    
    Returns:
        tuple: 包含特征和标签的pandas DataFrame。
    """
    y = pd.read_csv(label_csv_path, delimiter=',')['is_troll']
    x = pd.read_csv(x_csv_path, delimiter=',', header=None)
    return x, y


def split_data(x, y, test_size=0.3, random_state=None):
    """
    将数据集分割为训练集和测试集。
    
    Args:
        x (DataFrame): 特征数据。
        y (DataFrame): 标签数据。
        test_size (float): 测试集所占比例。
        random_state (int): 随机种子，用于可复现的数据分割。
    
    Returns:
        tuple: 分割后的训练集和测试集。
    """
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=random_state)
    return x_train, x_test, y_train, y_test


def train_svm_model(x_train, y_train,n_flod):
    """
    使用SVM训练模型。
    
    Args:
        x_train (DataFrame): 训练集特征数据。
        y_train (DataFrame): 训练集标签数据。
        n_flod(int): 模型交叉训练折数
    
    Returns:
        GridSearchCV: 训练完成的模型，内部通过网格搜索确定最优参数。
    """
    # 不论是使用thunderSVM还是使用sklearnSVM，函数使用方式都相同，无需改变
    svc = SVC(max_iter=80000, verbose=True)
    parameters = {'kernel': ['rbf'], 'C': [1], 'gamma': [0.01]}
    cv = KFold(n_splits=n_flod, shuffle=True, random_state=68)
    clf = GridSearchCV(svc, parameters, cv=cv, scoring='accuracy', verbose=3, return_train_score=True)
    clf.fit(x_train, y_train)
    return clf

def save_model_and_results(clf, model_path, results_path, x_train, y_train, x_test, y_test):
    """
    保存训练好的模型和训练结果。
    
    Args:
        clf (GridSearchCV): 训练完成的模型。
        model_path (str): 模型保存路径。
        results_path (str): 训练结果保存路径。
        x_train (DataFrame): 训练集特征数据。
        y_train (DataFrame): 训练集标签数据。
        x_test (DataFrame): 测试集特征数据。
        y_test (DataFrame): 测试集标签数据。
    """
    # 检查模型保存路径，如果不存在则创建
    model_dir = os.path.dirname(model_path)
    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)  # 创建模型目录，exist_ok=True意味着如果目录已存在不会引发异常
    
    # 检查结果保存路径，如果不存在则创建
    results_dir = os.path.dirname(results_path)
    if not os.path.exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)  # 创建结果目录

    # 保存模型
    joblib.dump(clf, model_path)
    # 计算训练集和测试集的得分
    train_score = clf.score(x_train, y_train)
    test_score = clf.score(x_test, y_test)
    # 记录得分到日志
    logging.info(f"Train score: {train_score}, Test score: {test_score}")
    # 保存交叉验证的详细结果
    pd.DataFrame(clf.cv_results_).to_csv(results_path, index=False)


def main():
    # 经由数据预处理生成的目标数据
    label_csv_path = '/home/lc/lc/Test/data/gen_data/comments_cleaned.csv'
    # 经由bert模型生成的文本向量文件
    x_csv_path = '/home/lc/lc/Test/data/gen_data/embedding_char.csv'
    
    # 经由SVM训练即将得到的模型
    model_path = '/home/lc/lc/Test/model/model.joblib'
    # 模型训练信息记录文件
    results_path = '/home/lc/lc/Test/model/n_fold.csv'


   # 数据加载和分割
    x, y = load_data(label_csv_path, x_csv_path)
    x_train, x_test, y_train, y_test = split_data(x, y, test_size=0.3, random_state=42)
    # 模型训练
    clf = train_svm_model(x_train, y_train,5)
    # 保存模型和结果
    save_model_and_results(clf, model_path, results_path, x_train, y_train, x_test, y_test)

if __name__ == "__main__":
    main()

