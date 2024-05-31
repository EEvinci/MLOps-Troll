import pandas as pd
import jieba
from scipy.stats import zscore
import numpy as np
import os

import mlflow
from sqlalchemy import create_engine


BASE_PATH = os.environ["BASE_PATH"]
DB_URI = os.environ["DATABASE_URL"]
mlflow.tracking.set_tracking_uri(os.environ["TRACKING_URL"])


def get_clean_comments(output_file_path):
    try:
        engine = create_engine(DB_URI)
        # 从数据库中读取数据
        df = pd.read_sql("SELECT * FROM dataset limit 100", engine)
        engine.dispose()

        # 重命名列以符合后续处理
        df.rename(columns={"text": "reply", "label": "is_troll"}, inplace=True)

        # 筛选出长度在3到40字符之间的评论
        df = df[df['reply'].apply(lambda x: 3 <= len(x) <= 40)]

        # 保存处理后的数据到CSV文件
        df.to_csv(output_file_path, index=False)
        print(f"Cleaned data saved to {output_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")



def seg_rmStpw(input_output_csv_path, stopwords_txt_path):
    """
    使用jieba进行中文分词并去除停用词。

    Args:
        input_output_csv_path (str): 输入和输出使用同一个CSV文件的路径，该文件包含需要处理的评论。
        stopwords_txt_path (str): 停用词列表的文本文件路径。
    """
    # 读取CSV文件
    df = pd.read_csv(input_output_csv_path)

    # 加载停用词
    with open(stopwords_txt_path, "r", encoding="utf-8") as f:
        stopwords = set([line.strip() for line in f.readlines()])

    # 分词并移除停用词
    def tokenize_and_remove_stopwords(text):
        tokens = jieba.cut(text)
        filtered_tokens = [
            token for token in tokens if token not in stopwords and token.strip() != ""
        ]
        cleaned_text = " ".join(filtered_tokens)
        # 清理前后以及中间的多余空格
        return " ".join(cleaned_text.split())

    # 应用到每一行的中文文本列
    df["word_seg"] = df["reply"].apply(tokenize_and_remove_stopwords)

    # 保存到新的CSV文件
    df.to_csv(input_output_csv_path, index=False)


def calculate_sentiment_score_and_normalize(
    input_output_csv_path, sen_dict_path, neg_dict_path, adv_dict_path
):
    """
    计算评论的情感分数，并根据提供的情感、否定词和副词词典进行加权。

    Args:
        input_output_csv_path (str): 输入和输出使用同一个CSV文件的路径，该文件包含已分词的评论。
        sen_dict_path (str): 情感词典的文件路径。
        neg_dict_path (str): 否定词词典的文件路径。
        adv_dict_path (str): 副词词典的文件路径。
    """

    def load_dictionary(dict_path, separator=","):
        """根据词典文件的格式加载词典，返回一个字典"""
        try:
            with open(dict_path, "r", encoding="utf-8") as file:
                if separator == " ":
                    return {
                        line.split(separator)[0]: float(
                            line.split(separator)[1].strip()
                        )
                        for line in file
                        if line.strip()
                    }
                else:
                    return {
                        line.strip().split(separator)[0]: float(
                            line.strip().split(separator)[1]
                        )
                        for line in file
                        if separator in line
                    }
        except Exception as e:
            print(f"Error loading dictionary from {dict_path}: {e}")
            return {}

    # 加载词典，情感词典使用空格分隔（根据词典的实际格式加载词典）
    sen_dict = load_dictionary(sen_dict_path, separator=" ")
    neg_dict = load_dictionary(neg_dict_path)
    adv_dict = load_dictionary(adv_dict_path)

    # 读取评论数据
    comments_df = pd.read_csv(input_output_csv_path)

    # 确保word_seg列是字符串类型，并处理NaN值
    comments_df["word_seg"] = comments_df["word_seg"].fillna("").astype(str)

    def sentiment_analysis(row):
        words = row.split()
        score = 0.0
        adv_modifier = 1.0
        negation = False
        pending_score = 0.0

        for word in words:
            if word in sen_dict:
                emotion_score = sen_dict[word] * (-1 if negation else 1) * adv_modifier
                pending_score += emotion_score
                adv_modifier, negation = 1.0, False
            elif word in adv_dict:
                adv_modifier = adv_dict[word]
            elif word in neg_dict:
                negation = not negation

        score += pending_score
        return score

    comments_df["t-score"] = comments_df["word_seg"].apply(sentiment_analysis)

    # 保存到新的CSV文件
    comments_df.to_csv(input_output_csv_path, index=False)


def t_normalize_sentiment_scores(file_path):
    """
    对评论的情感分数进行Z-score标准化处理。

    Args:
        file_path (str): 包含情感分数的CSV文件路径。
    """
    # 读取评论数据
    comments_df = pd.read_csv(file_path)

    # 计算情感分数的Z-score
    comments_df["t-z-score"] = zscore(comments_df["t-score"])

    # 保存更新后的DataFrame到原文件
    comments_df.to_csv(file_path, index=False)


def calculate_emoji_sentiment_scores(comments_file_path, emoji_data_path):
    """
    根据emoji情感得分数据文件计算含有emoji的评论的情感得分，并更新原数据文件。

    Args:
        comments_file_path (str): 包含评论数据的CSV文件路径。
        emoji_data_path (str): 包含emoji情感得分的数据文件路径。
    """
    # 加载emoji情感得分数据
    emoji_df = pd.read_csv(emoji_data_path)
    emoji_scores = {}
    for _, row in emoji_df.iterrows():
        total = row["Negative"] + row["Neutral"] + row["Positive"]
        # 计算综合情感得分
        score = (
            (1 * row["Positive"] / total)
            - (1.2 * row["Negative"] / total)
            + (0.5 * row["Neutral"] / total)
        )
        emoji_scores[row["Emoji"]] = score

    # 读取评论数据
    comments_df = pd.read_csv(comments_file_path)

    # 确保word_seg列中的所有项都是字符串，并处理NaN值
    comments_df["word_seg"] = comments_df["word_seg"].astype(str).fillna("")

    # 定义计算emoji情感得分的函数
    def emoji_sentiment_score(word_seg):
        score = 0.0
        words = word_seg.split()  # 现在word_seg已经保证是字符串类型
        for word in words:
            if word in emoji_scores:
                score += emoji_scores[word]
        return score

    # 应用函数计算每条评论的emoji情感得分
    comments_df["e-score"] = comments_df["word_seg"].apply(emoji_sentiment_score)

    # 将更新后的数据保存回原文件
    comments_df.to_csv(comments_file_path, index=False)


def normalize_emoji_scores(file_path):
    """
    对emoji情感得分进行Z-score标准化处理。

    Args:
        file_path (str): 包含emoji情感得分的CSV文件路径。
    """
    # 读取评论数据
    comments_df = pd.read_csv(file_path)

    # 确保e-score列存在
    if "e-score" in comments_df.columns:
        # 计算e-score的Z-score并添加为新列
        comments_df["e-z-score"] = zscore(comments_df["e-score"])

        # 将更新后的DataFrame保存回原文件
        comments_df.to_csv(file_path, index=False)
    else:
        print("The 'e-score' column does not exist in the DataFrame.")


def calculate_and_final_sentiment_score(file_path):
    """
    根据文本情感分数和emoji情感分数计算最终情感分数。

    Args:
        file_path (str): 包含已计算情感分数的CSV文件路径。
    """
    # 读取评论数据
    comments_df = pd.read_csv(file_path)

    # 定义计算最终情感分数的函数
    def calculate_final_score(row):
        t_z_score = row["t-z-score"]
        e_z_score = row["e-z-score"]
        # 当句子包含表情时，使用给定公式计算情感得分
        if t_z_score >= 0 and e_z_score >= 0:
            final_score = np.sqrt(0.7 * t_z_score + 0.3 * e_z_score)
        elif t_z_score < 0 and e_z_score < 0:
            final_score = 0.7 * t_z_score + 0.3 * e_z_score
        else:
            final_score = (t_z_score / e_z_score) * np.sqrt(
                np.abs(0.7 * t_z_score + 0.3 * e_z_score)
            )
        return final_score

    # 应用函数计算每条评论的最终情感得分
    comments_df["senti-score"] = comments_df.apply(calculate_final_score, axis=1)

    # 将更新后的数据保存回原文件
    comments_df.to_csv(file_path, index=False)


def normalize_senti_scores(file_path):
    """
    对最终情感得分进行Z-score标准化处理。

    Args:
        file_path (str): 包含最终情感得分的CSV文件路径。
    """
    # 读取评论数据
    comments_df = pd.read_csv(file_path)

    # 确保senti-score列存在
    if "senti-score" in comments_df.columns:
        # 计算senti-score的Z-score并添加为新列
        comments_df["senti-z-score"] = zscore(comments_df["senti-score"])

        # 将更新后的DataFrame保存回原文件
        comments_df.to_csv(file_path, index=False)
    else:
        print("The 'senti-score' column does not exist in the DataFrame.")

def main():
    # 确保输出目录存在
    output_dir = f'{BASE_PATH}/comment_output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 由原始数据文件经过长度清洗得到 并作为之后的主要数据处理文件
    comments_file_path = f"{BASE_PATH}/comment_output/comments_cleaned.csv"
    # 停用词词典的路径
    stopwords_txt_path = f"{BASE_PATH}/stopwords.txt"
    # 情感词典的路径
    sen_dict_path = f"{BASE_PATH}/BosonNLP_sentiment_score.txt"
    # 否定词词典的路径
    neg_dict_path = f"{BASE_PATH}/NOT.txt"
    # 副词词典的路径
    adv_dict_path = f"{BASE_PATH}/adv_chinese.txt"
    # Emoji数据的路径
    emoji_data_path = f"{BASE_PATH}/emoji_data.csv"

    # 清理评论数据，仅保留长度在特定范围内的评论
    get_clean_comments(comments_file_path)

 # 检查文件是否生成
    if os.path.exists(comments_file_path):
        print(f"{comments_file_path} has been created successfully.")
    else:
        print(f"Failed to create {comments_file_path}. Check the get_clean_comments function.")

    # 对评论进行分词处理并去除停用词
    seg_rmStpw(comments_file_path, stopwords_txt_path)

    # 计算评论的情感分数并对其进行初步标准化处理
    calculate_sentiment_score_and_normalize(
        comments_file_path, sen_dict_path, neg_dict_path, adv_dict_path
    )

    # 对文本情感分数进行Z-score标准化
    t_normalize_sentiment_scores(comments_file_path)

    # 计算包含Emoji的评论的情感分数
    calculate_emoji_sentiment_scores(comments_file_path, emoji_data_path)

    # 对Emoji情感分数进行Z-score标准化
    normalize_emoji_scores(comments_file_path)

    # 结合文本和Emoji情感分数，计算每条评论的最终情感得分
    calculate_and_final_sentiment_score(comments_file_path)

    # 对最终的情感得分进行Z-score标准化
    normalize_senti_scores(comments_file_path)


if __name__ == "__main__":
    main()