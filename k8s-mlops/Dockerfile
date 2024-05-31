# 使用官方 Python 运行时作为父镜像
FROM python:3.8.18-slim as builder

WORKDIR /app

# 将当前目录内容复制到位于 /app 的容器中
COPY . /app

# 安装 requirements.txt 中指定的所需包
# 使用 virtual environment 可帮助减小最终镜像大小
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 使用最终阶段构建
FROM python:3.8.18-slim
COPY --from=builder /opt/venv /opt/venv

# 设置工作目录
WORKDIR /app
COPY . /app

# 设置环境变量以确保 Python 输出直接打印到控制台，而不是先被缓冲
ENV PYTHONUNBUFFERED True

# 确保可以使用 venv
ENV PATH="/opt/venv/bin:$PATH"

# 定义运行时的命令
CMD ["python3", "-m", "src.dataset"]
