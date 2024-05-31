import pandas as pd
import numpy as np
import torch
from transformers import BertModel, BertTokenizer

def initialize_bert_model(bert_path):
    """
    初始化BERT模型和分词器。
    
    Args:
        bert_path (str): 预训练BERT模型的路径。
        
    Returns:
        BertModel: 加载的BERT模型。
        BertTokenizer: 相应的分词器。
        device: 模型和数据将运行在的设备（CPU或GPU）。
    """
    # 检查CUDA是否可用，优先使用GPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # 加载BERT模型
    bert_model = BertModel.from_pretrained(bert_path).to(device)
    # 加载BERT分词器
    tokenizer = BertTokenizer.from_pretrained(bert_path)
    return bert_model, tokenizer, device



def vectorize_comments(comments_file, tokenizer, bert_model, device):
    """
    使用BERT模型将评论文本转换为向量形式。
    
    Args:
        comments_file (pd.Series): 评论文本的pandas序列。
        tokenizer (BertTokenizer): BERT分词器。
        bert_model (BertModel): BERT模型。
        device (torch.device): 运算设备。
        
    Returns:
        np.ndarray: 评论的向量化表示。
    """
    char_embeds = []
    # 对每条评论进行处理
    for reply in comments_file:
        # 使用BERT分词器处理文本
        inputs = tokenizer(reply, padding="max_length", truncation=True, max_length=512, return_tensors="pt").to(device)
        # 使用BERT模型进行预测，无需梯度
        with torch.no_grad():
            outputs = bert_model(**inputs)
        # 提取[CLS]标记的嵌入，作为句子的向量表示
        cls_embed = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        char_embeds.append(cls_embed.squeeze())
    return np.array(char_embeds)



def weight_and_save(char_embeds, scores_path, output_path):
    """
    根据情感分数加权字符嵌入，并将加权结果保存到文件。
    
    Args:
        char_embeds (np.ndarray): 字符嵌入向量。
        scores_path (str): 包含情感分数的文件路径。
        output_path (str): 加权字符嵌入将被保存的路径。
    """
    # 加载情感分数
    normalized_scores = pd.read_csv(scores_path, usecols=['senti-z-score']).to_numpy()
    # 根据情感分数加权字符嵌入
    senti_embed = char_embeds * normalized_scores
    # 保存结果到CSV文件
    np.savetxt(output_path, senti_embed, delimiter=',')
    print("完成情感加权的字符嵌入生成！")




def main():
    # BERT模型路径
    bert_path = '/home/lc/lc/Test/BERT_zh_L12_PyTorch_'
    # 处理后的评论数据文件路径
    comments_path = '/home/lc/lc/Test/data/gen_data/comments_cleaned.csv'
    # 保存向量化结果的文件路径
    output_path = '/home/lc/lc/Test/data/gen_data/embedding_char.csv'

    # 初始化BERT模型和分词器
    bert_model, tokenizer, device = initialize_bert_model(bert_path)
    # 加载评论数据
    comments_df = pd.read_csv(comments_path)
    # 将评论文本向量化
    char_embeds = vectorize_comments(comments_df['reply'], tokenizer, bert_model, device)
    # 使用情感分数加权向量化结果，并保存
    weight_and_save(char_embeds, comments_path, output_path)



if __name__ == "__main__":
    main()
