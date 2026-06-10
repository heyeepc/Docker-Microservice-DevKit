# Docker-Microservice-DevKit
基于 Docker 和 Docker-Compose 构建了微服务开发/测试一体化容器方案，实现多服务、多中间件的一键本地编排，彻底解决在我电脑上能运行，在服务器上不行的经典问题。
 
### 📂 项目目录结构

```text
~/my-deploy/
├── docker-compose.yml     # 核心容器编排文件
└── backend/               # Python 后端监控服务
    ├── app.py             # Streamlit 核心脚本（数据采集与可视化看板）
    ├── requirements.txt   # 项目 Python 依赖包
    └── Dockerfile         # 高水准多阶段构建 Dockerfile
