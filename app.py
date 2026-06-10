import streamlit as st
import mysql.connector
import redis
import psutil
import time
import os
import pandas as pd

# 从环境变量获取容器服务名
DB_HOST = os.getenv("SPRING_DATASOURCE_URL", "my_db")
REDIS_HOST = os.getenv("SPRING_REDIS_HOST", "my_redis")

st.set_page_config(page_title="树莓派5监控", layout="wide")
st.title("树莓派 5 边缘端容器化监控看板 ")

# 1. Redis 访问计数
try:
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    r.incr("page_views")
    views = r.get("page_views")
    st.markdown(f"###  看板总访问次数（Redis 缓存计数）: `{views}`")
except Exception as e:
    st.error(f"Redis 连接失败: {e}")

# 计算网络速率的函数
def get_net_speed():
    net_old = psutil.net_io_counters()
    time.sleep(0.5)
    net_new = psutil.net_io_counters()
    # 转换为 KB/s
    download_speed = (net_new.bytes_recv - net_old.bytes_recv) / 1024 / 0.5
    upload_speed = (net_new.bytes_sent - net_old.bytes_sent) / 1024 / 0.5
    return round(download_speed, 2), round(upload_speed, 2)

# 2. 采集数据
cpu = psutil.cpu_percent(interval=None)
mem = psutil.virtual_memory().percent
download, upload = get_net_speed()

# 3. MySQL 读写与图表渲染
try:
    conn = mysql.connector.connect(
        host=DB_HOST, user="root", password="root_password", database="test_db"
    )
    cursor = conn.cursor()
    
    # 确保表结构完整（增加了网络流量字段）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_status_v2 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cpu_usage FLOAT,
            memory_usage FLOAT,
            download_speed FLOAT,
            upload_speed FLOAT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 写入最新数据
    cursor.execute(
        "INSERT INTO system_status_v2 (cpu_usage, memory_usage, download_speed, upload_speed) VALUES (%s, %s, %s, %s)",
        (cpu, mem, download, upload)
    )
    conn.commit()
    
    # 顶层状态卡片展示
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(" CPU 使用率", f"{cpu} %")
    col2.metric("内存使用率", f"{mem} %")
    col3.metric("网络下载速率", f"{download} KB/s")
    col4.metric("网络上传速率", f"{upload} KB/s")
    
    # 读取最后 30 条数据用于画图
    cursor.execute("SELECT timestamp, cpu_usage, memory_usage FROM system_status_v2 ORDER BY id DESC LIMIT 30")
    rows = cursor.fetchall()
    
    if rows:
        # 转换为 Pandas DataFrame 方便 Streamlit 画图
        df = pd.DataFrame(rows, columns=['时间', 'CPU 使用率', '内存使用率'])
        df = df.iloc[::-1] # 反转顺序让时间轴从左到右
        
        st.subheader("性能走势图（实时读取 MySQL 历史数据）")
        st.line_chart(df.set_index('时间'))
        
    cursor.close()
    conn.close()
except Exception as e:
    st.error(f"MySQL 操作失败: {e}")

# 3秒自动刷新
time.sleep(3)
st.rerun()
