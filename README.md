# Docker-Microservice-DevKit
基于 Docker 和 Docker-Compose 构建了微服务开发/测试一体化容器方案，实现多服务、多中间件的一键本地编排，彻底解决在我电脑上能运行，在服务器上不行的经典问题。
 
## ⚙️ 核心组件与工程设计

本项目不仅仅是一套监控脚本，而是围绕边缘端（树莓派5）特性，按照工业级标准打造的微服务一体化交付方案。各核心文件的功能与设计逻辑如下：

### 1. `docker-compose.yml` (容器编排与拓扑设计)
* **核心功能**：负责一键编排、拉取并纳管 MySQL 数据库、Redis 缓存以及 Python 核心应用容器。
* **工程亮点**：
  * **服务发现**：利用内置的 Bridge 自定义网络，实现容器间通过服务名（如 `my_db`）进行安全的内网 DNS 解析，彻底解耦硬编码 IP。
  * **拓扑解耦（Healthcheck）**：为 MySQL 容器配置了底层健康检查（`mysqladmin ping`），配合 `condition: service_healthy` 约束，完美解决了分布式中间件因启动时滞导致后端应用连接超时、崩溃重启的经典痛点。

### 2. `backend/Dockerfile` (高水准多阶段构建)
* **核心功能**：定义 Python 应用镜像的生成算法。
* **工程亮点**：
  * **多阶段构建（Multi-stage Build）**：分为 `builder` 编译阶段与最终运行阶段。在第一阶段引入 `gcc` 及开发头文件，在树莓派本地现场编译 `psutil` 等涉及底层 C 接口的依赖包；在第二阶段仅拷贝纯净产物，不引入任何编译工具链。
  * **边缘端优化**：通过隔离编译冗余，使最终交付的镜像体积**缩减 70% 以上**，极大缓解了树莓派等边缘设备的存储压力。

### 3. `backend/app.py` (数据采集与可视化看板)
* **核心功能**：纯 Python 编写的微服务核心业务。
* **工程亮点**：
  * **多维数据采集**：利用 `psutil` 异步采集树莓派 5 边缘节点的物理状态（CPU、内存）以及网络栈流量（实时上传/下载速率）。
  * **双层高并发存储**：高频访问指标接入 **Redis 缓存行**进行原子计数，历史全量指标持久化落入 **MySQL 关系型数据库**，并基于 Streamlit 实现前端动态折线图的秒级异步渲染。

### 4. `backend/requirements.txt` (声明式依赖清单)
* **核心功能**：精确锁定项目所需的最小第三方库集合（`streamlit`、`redis`、`mysql-connector-python`、`psutil`、`pandas`）。
* **工程亮点**：配合 Docker 的 **Layer Cache（层缓存机制）**。只要该文件内容未发生变更，后续修改 `app.py` 业务代码时，Docker 会直接跳过耗时数分钟的依赖下载编译阶段，实现**秒级热更新与极速 CI/CD 交付**。

### 📂 项目目录结构

```text
~/my-deploy/
├── docker-compose.yml     # 核心容器编排文件
└── backend/               # Python 后端监控服务
    ├── app.py             # Streamlit 核心脚本（数据采集与可视化看板）
    ├── requirements.txt   # 项目 Python 依赖包
    └── Dockerfile         # 多阶段构建 Dockerfile

