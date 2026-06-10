# Docker-Microservice-DevKit
基于 Docker 和 Docker-Compose 构建了微服务开发/测试一体化容器方案，实现多服务、多中间件的一键本地编排，彻底解决在我电脑上能运行，在服务器上不行的经典问题。
 
~/my-deploy/
├── docker-compose.yml     # 编排文件
├── backend/               # 后端项目源码根目录
│   ├── app.py               # 代码
│   ├── requirements.txt
│   └── Dockerfile         # 后端Dockerfile
