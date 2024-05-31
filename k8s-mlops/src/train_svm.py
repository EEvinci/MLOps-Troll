import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.svm import SVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import confusion_matrix
from sklearn.utils.multiclass import unique_labels 
from joblib import dump
import time

import mlflow
import mlflow.sklearn


BASE_PATH = os.environ["BASE_PATH"]
MODEL_NAME = os.environ["MODEL_NAME"]
mlflow.tracking.set_tracking_uri(os.environ["TRACKING_URL"])

# 在 autolog 调用时添加 log_input_examples=False
mlflow.autolog()

def load_data(file_path):
    """
    从CSV文件中加载数据并进行预处理。

    Args:
        file_path (str): 文件路径。
    
    Returns:
        X (sparse matrix): TF-IDF 特征矩阵。
        y (array): 目标标签数组。
    """
    df = pd.read_csv(file_path)
    tfidf_vectorizer = TfidfVectorizer(max_features=5000)
    X = tfidf_vectorizer.fit_transform(df['reply'])
    y = df['is_troll'].values
    return X, y


def train_and_evaluate(X, y):
    """
    使用SVC训练模型并进行评估。

    Args:
        X: 特征数据。
        y: 标签数据。
    """
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    parameters = {'kernel': ['linear', 'rbf'], 'C': [1, 10], 'gamma': ['scale', 'auto']}
    svc = SVC(class_weight='balanced')
    clf = GridSearchCV(svc, parameters, cv=5, scoring='accuracy')

    start_time = time.time()
    with mlflow.start_run(run_name=f"train-{MODEL_NAME}-{int(time.time())}"):
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        precision = precision_score(y_test, y_pred, zero_division=1)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        accuracy = accuracy_score(y_test, y_pred)
        training_time = time.time() - start_time

        mlflow.log_params(clf.best_params_)
        mlflow.log_metrics({
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'accuracy': accuracy,
            'training_time': training_time
        })
        mlflow.sklearn.log_model(clf, "model")


def main():
    data_file_path = os.path.join(BASE_PATH, "comment_output/comments_cleaned.csv")
    X, y = load_data(data_file_path)
    train_and_evaluate(X, y)

if __name__ == "__main__":
    main()
