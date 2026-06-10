# Docker-Microservice-DevKit
基于 Docker 和 Docker-Compose 构建了微服务开发/测试一体化容器方案，实现多服务、多中间件的一键本地编排，彻底解决在我电脑上能运行，在服务器上不行的经典问题。

<img width="1276" height="668" alt="image" src="https://github.com/user-attachments/assets/43f2f278-d5cb-4759-a70f-19f7f1ed772c" />

## ⚙️ 核心组件与工程设计

本项目不仅仅是一套监控脚本，而是围绕边缘端（树莓派5）特性，按照工业级标准打造的微服务一体化交付方案。各核心文件的功能与设计逻辑如下：

### 1. `docker-compose.yml` (容器网络安全平面与拓扑设计)
* **核心功能**：一键编排并纳管整个网管系统的微服务拓扑。
* **网络工程亮点**：
  * **DMZ 双网络平面隔离**：显式划分了 `frontend_net`（前端外网段）和 `backend_net`（后端内网安全段）两个独立的虚拟 Bridge 网卡。
  * **零暴露安全收敛**：下线了 MySQL（3306）和 Redis（6379）的物理端口映射，将其完全隐蔽在私有内网段中，隔绝局域网内的恶意扫描与端口攻击。
  * **堡垒机拓扑路由**：仅允许同时跨双网络平面的 Python 网管容器（`rpi_python_app`）扮演网关角色进行数据桥接，完美落地微服务“最小化权限暴露”的安全纳管规范。
  * **拓扑联动（Healthcheck）**：配置 `mysqladmin ping` 底层健康检查，配合 `condition: service_healthy` 约束，彻底解决分布式中间件因启动时滞导致的后端连接超时崩溃问题。

### 2. `backend/Dockerfile` (高水准多阶段构建)
* **核心功能**：定义 Python 应用镜像的生成算法。
* **工程亮点**：
  * **多阶段构建（Multi-stage Build）**：分为 `builder` 编译阶段与最终运行阶段。在第一阶段引入 `gcc` 及开发头文件，在树莓派本地现场编译 `psutil` 等涉及底层 C 接口的依赖包；在第二阶段仅拷贝纯净产物，不引入任何编译工具链。
  * **边缘端优化**：通过隔离编译冗余，使最终交付的镜像体积**缩减 70% 以上**，极大缓解了树莓派等边缘设备的存储压力。

### 3. `backend/app.py` (网络多维指标采集与 ICMP SLA 探测中心)
* **核心功能**：基于 Python 构建的边缘网络数通监控中心业务核心。
* **数通运维亮点**：
  * **链路层吞吐与健康度捕获**：利用底层系统接口，自动锚定树莓派当前的活跃物理网卡（如 `wlan0` 或 `eth0`），高频计算实时上行/下行网络吞吐速率；并实时捕获**入网错包率（Errors）与入网丢包率（Drops）**，为链路层排错提供核心 CRC 校验依据。
  * **传输层 TCP 有限状态机追踪**：实时分析宿主机套接字，对传输层 **TCP ESTABLISHED**（已建立连接数）和 **TCP TIME_WAIT**（等待回收状态数）进行动态计数，监控边缘节点的并发网络连接负载。
  * **ICMP SLA 链路质量探测**：内嵌轻量级 ICMP 拨测机制，定时向公网骨干 DNS（`223.5.5.5`）发送探测包，实现毫秒级链路响应延时（Latency）的实时监测与全量数据持久化。
 
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

