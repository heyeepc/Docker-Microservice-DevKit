import streamlit as st
import mysql.connector
import redis
import psutil
import time
import os
import pandas as pd
import subprocess

DB_HOST = os.getenv("SPRING_DATASOURCE_URL", "my_db")
REDIS_HOST = os.getenv("SPRING_REDIS_HOST", "my_redis")

st.set_page_config(page_title="树莓派5边缘网管中心", layout="wide")
st.title("🛰️ 树莓派 5 边缘端网络数通监控中心")

# 1. Redis 访问计数
try:
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    r.incr("page_views")
    views = r.get("page_views")
    st.sidebar.markdown(f"### 📊 看板总访问次数: `{views}`")
except Exception as e:
    st.sidebar.error(f"Redis 异常: {e}")

# --- 数通指标采集函数 ---
def get_network_metrics():
    # 1. 计算网络速率
    net_old = psutil.net_io_counters(pernic=True)
    time.sleep(0.5)
    net_new = psutil.net_io_counters(pernic=True)
    
    # 自动获取当前活动的网卡（通常是 wlan0 或 eth0）
    active_iface = "lo"
    for iface in net_new.keys():
        if iface != "lo" and net_new[iface].bytes_recv > 0:
            active_iface = iface
            break
            
    old_if = net_old[active_iface]
    new_if = net_new[active_iface]
    
    download_speed = (new_if.bytes_recv - old_if.bytes_recv) / 1024 / 0.5
    upload_speed = (new_if.bytes_sent - old_if.bytes_sent) / 1024 / 0.5
    
    # 2. 采集网卡错误与丢包（网络排错核心指标）
    err_in = new_if.errin
    drop_in = new_if.dropin
    
    # 3. 统计底层 TCP 连接状态
    tcp_conns = psutil.net_connections(kind='tcp')
    established = sum(1 for c in tcp_conns if c.status == 'ESTABLISHED')
    time_wait = sum(1 for c in tcp_conns if c.status == 'TIME_WAIT')
    
    # 4. ICMP SLA：探测网关或公网 DNS 延时
    try:
        # Ping 阿里 DNS 1次，超时1秒
        output = subprocess.check_output(["ping", "-c", "1", "-W", "1", "223.5.5.5"], text=True)
        # 提取 time=xx ms
        ping_time = float(output.split("time=")[1].split(" ms")[0])
    except Exception:
        ping_time = -1.0 # Ping 不通显示 -1
        
    return active_iface, round(download_speed, 2), round(upload_speed, 2), err_in, drop_in, established, time_wait, ping_time

# 执行采集
iface, download, upload, err_in, drop_in, established, time_wait, ping_time = get_network_metrics()
cpu = psutil.cpu_percent(interval=None)
mem = psutil.virtual_memory().percent

# 2. MySQL 持久化写入
try:
    conn = mysql.connector.connect(host=DB_HOST, user="root", password="root_password", database="test_db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS net_advanced_status (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cpu FLOAT, memory FLOAT, download FLOAT, upload FLOAT,
            ping_latency FLOAT, tcp_established INT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT INTO net_advanced_status (cpu, memory, download, upload, ping_latency, tcp_established)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (cpu, mem, download, upload, ping_time, established))
    conn.commit()
    
    # --- 前端渲染 ---
    st.subheader(f"🌐 活跃网卡接口状态: `{iface}`")
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    r1_c1.metric(" 下载速率", f"{download} KB/s")
    r1_c2.metric(" 上传速率", f"{upload} KB/s")
    r1_c3.metric(" 接口入网错误包数", f"{err_in} Pkts")
    r1_c4.metric(" 接口入网丢包数", f"{drop_in} Pkts")
    
    st.subheader(" 链路层与传输层高级指标")
    r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
    r2_c1.metric(" ICMP SLA 延时 (至223.5.5.5)", f"{ping_time} ms" if ping_time > 0 else "超时/不通")
    r2_c2.metric(" TCP ESTABLISHED 状态数", f"{established} 个")
    r2_c3.metric(" TCP TIME_WAIT 状态数", f"{time_wait} 个")
    r2_c4.metric(" 宿主机 CPU / 内存", f"{cpu}% / {mem}%")
    
    # 读取历史画图
    cursor.execute("SELECT timestamp, download, upload, ping_latency FROM net_advanced_status ORDER BY id DESC LIMIT 30")
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=['时间', '下载速率', '上传速率', 'Ping延时(ms)'])
        df = df.iloc[::-1]
        st.subheader(" 网络链路吞吐与延时走势图")
        st.line_chart(df.set_index('时间'))
        
    cursor.close()
    conn.close()
except Exception as e:
    st.error(f"MySQL 交互失败: {e}")

time.sleep(3)
st.rerun()
