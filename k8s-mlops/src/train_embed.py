import pandas as pd
import numpy as np
# import torch
# from transformers import BertModel, BertTokenizer
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from joblib import dump

BASE_PATH = os.environ["BASE_PATH"]

def vectorize_comments(comments_file_path, output_path):
    """
    使用TF-IDF方法将评论文本转换为向量形式，并进行降维处理。

    Args:
        comments_file_path (str): 包含评论文本的CSV文件路径。
        output_path (str): 向量化结果将被保存的路径。
    """
    # 读取评论数据
    df = pd.read_csv(comments_file_path)
    # 初始化TF-IDF向量化器
    tfidf_vectorizer = TfidfVectorizer(max_features=500)
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['reply'])
    
    # 保存TF-IDF向量化器
    dump(tfidf_vectorizer, f'/root/data/model/tfidf_vectorizer.joblib')
    
    # 确定SVD的组件数
    # n_components = min(50, tfidf_matrix.shape[1] - 1)
    n_components = 86
    
    # 使用SVD进行降维处理
    svd = TruncatedSVD(n_components=n_components)
    char_embeds = svd.fit_transform(tfidf_matrix)
    
    # 保存SVD模型
    dump(svd, f'/root/data/model/svd.joblib')
    
    # 保存向量化结果到CSV文件
    np.savetxt(output_path, char_embeds, delimiter=",")

    print(f"Vectorized data saved to {output_path}")

def weight_and_save(char_embeds_path, scores_path, output_path):
    """
    根据情感分数加权字符嵌入，并将加权结果保存到文件。

    Args:
        char_embeds_path (str): 字符嵌入向量文件路径。
        scores_path (str): 包含情感分数的文件路径。
        output_path (str): 加权字符嵌入将被保存的路径。
    """
    # 加载字符嵌入向量和情感分数
    char_embeds = np.loadtxt(char_embeds_path, delimiter=",")
    normalized_scores = pd.read_csv(scores_path, usecols=["senti-z-score"]).to_numpy()
    
    # 根据情感分数加权字符嵌入
    senti_embed = char_embeds * normalized_scores
    
    # 保存结果到CSV文件
    np.savetxt(output_path, senti_embed, delimiter=",")

    print("Completed weighted character embeddings generation!")


def main(): 

    output_dir = f'{BASE_PATH}/char'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 初始化路径
    comments_path = f"{BASE_PATH}/comment_output/comments_cleaned.csv"
    vectorized_path = f"{BASE_PATH}/char/embedding_char.csv"
    output_path = f"{BASE_PATH}/char/weighted_embeddings.csv" 

    # 将评论文本向量化
    vectorize_comments(comments_path, vectorized_path)
    
    # 使用情感分数加权向量化结果，并保存
    weight_and_save(vectorized_path, comments_path, output_path)


if __name__ == "__main__":
    main()
