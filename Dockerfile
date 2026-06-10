# --- 阶段一：构建依赖阶段 ---
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev
COPY requirements.txt .
# --user 可以把依赖包装在当前用户目录下，方便后面拷贝
RUN pip install --user -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# --- 阶段二：最终运行阶段 ---
FROM python:3.11-slim
WORKDIR /app
# 从构建阶段把安装好的 Python 包拷贝过来，不引入编译工具链，保持镜像极度轻量
COPY --from=builder /root/.local /root/.local
COPY app.py .

ENV PATH=/root/.local/bin:$PATH
EXPOSE 8501

# 启动 Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
