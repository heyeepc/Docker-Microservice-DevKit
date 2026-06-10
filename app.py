import streamlit as st
import mysql.connector
import redis
import psutil
import time
import os

# 1. 联通测试：从环境变量获取 Docker 编排好的容器服务名
DB_HOST = os.getenv("SPRING_DATASOURCE_URL", "my_db") # 借用之前的环境变量名
REDIS_HOST = os.getenv("SPRING_REDIS_HOST", "my_redis")

st.title(" 树莓派 5 边缘端容器化监控看板")

# 2. 体验 Redis 缓存
try:
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    r.incr("page_views")
    views = r.get("page_views")
    st.metric(label=" 看板总访问次数（Redis 计数）", value=views)
except Exception as e:
    st.error(f"Redis 连接失败: {e}")

# 3. 体验 MySQL 持久化数据写入
try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user="root",
        password="root_password",
        database="test_db"
    )
    cursor = conn.cursor()
    # 创建测试表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_status (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cpu_usage FLOAT,
            memory_usage FLOAT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 采集当前树莓派的数据
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    
    # 写入数据库
    cursor.execute("INSERT INTO system_status (cpu_usage, memory_usage) VALUES (%s, %s)", (cpu, mem))
    conn.commit()
    
    # 读取最后 10 条数据显示在网页上
    cursor.execute("SELECT cpu_usage, memory_usage, timestamp FROM system_status ORDER BY id DESC LIMIT 10")
    data = cursor.fetchall()
    
    # 在前端渲染数据
    st.subheader("🖥️ 树莓派当前状态（实时写入 MySQL）")
    col1, col2 = st.columns(2)
    col1.metric("CPU 使用率", f"{cpu} %")
    col2.metric("内存使用率", f"{mem} %")
    
    # 简单展示一下数据历史
    st.write("历史采集数据（最近10条）：", data)
    
    cursor.close()
    conn.close()
except Exception as e:
    st.error(f"MySQL 连接或写入失败: {e}")

# 自动刷新页面
time.sleep(5)
st.rerun()
