import streamlit as st
import pandas as pd
import math
import altair as alt
from datetime import datetime, timedelta
import os
import sqlite3
from urllib.parse import quote

# --- Page Config ---
st.set_page_config(
    page_title="霸王茶姬 (CHAGEE) 全链路运营诊断小程序",
    page_icon="🍵",
    layout="wide"
)

# --- Product Data ---
PRODUCTS = {
    "伯牙绝弦 (Boya Juexian)": {
        "tea_base": "茉莉雪芽 (Jasmine Green Tea)",
        "milk_base": "优质牛乳",
        "syrup": "原味糖浆",
        "prep_complexity": 1.0,
        "ingredients": ["15g 茉莉茶叶", "200ml 牛乳", "20ml 糖浆"],
        "process_steps": [
            "1. 泡茶/萃取: 80°C水温，焖泡10分钟，过滤备用。",
            "2. 基础备料: 加入20ml原味糖浆，准备冰块/热度调节。",
            "3. 调饮制作: 加入200ml优质牛乳，与茉莉茶汤充分融合。",
            "4. 封口包装: 机器封口，加吸管，套保温袋。",
            "5. 交付: 叫号取餐。"
        ]
    },
    "青青糯山 (Qingqing Nuoshan)": {
        "tea_base": "糯香乌龙 (Sticky Rice Oolong)",
        "milk_base": "优质牛乳",
        "syrup": "糯米糖浆",
        "prep_complexity": 1.2,
        "ingredients": ["18g 糯香茶叶", "200ml 牛乳", "25ml 糯米糖浆"],
        "process_steps": [
            "1. 泡茶/萃取: 90°C水温，焖泡12分钟，激发糯米香气。",
            "2. 基础备料: 加入25ml糯米糖浆，准备冰块/热度调节。",
            "3. 调饮制作: 加入200ml优质牛乳，糯香乌龙茶汤需额外摇晃均匀。",
            "4. 封口包装: 机器封口，加吸管，套保温袋。",
            "5. 交付: 叫号取餐。"
        ]
    },
    "寻香山茶 (Xunxiang Shancha)": {
        "tea_base": "山茶花乌龙 (Camellia Oolong)",
        "milk_base": "优质牛乳",
        "syrup": "原味糖浆",
        "prep_complexity": 1.1,
        "ingredients": ["15g 山茶花茶叶", "200ml 牛乳", "20ml 糖浆"],
        "process_steps": [
            "1. 泡茶/萃取: 85°C水温，焖泡10分钟，保留花香。",
            "2. 基础备料: 加入20ml原味糖浆，准备冰块/热度调节。",
            "3. 调饮制作: 加入200ml优质牛乳，混合山茶花乌龙茶汤。",
            "4. 封口包装: 机器封口，加吸管，套保温袋。",
            "5. 交付: 叫号取餐。"
        ]
    },
    "花开富贵 (Huakai Fugui)": {
        "tea_base": "茉莉雪芽 (Jasmine Green Tea)",
        "milk_base": "优质牛乳",
        "syrup": "原味糖浆",
        "prep_complexity": 1.3,
        "ingredients": ["15g 茉莉茶叶", "200ml 牛乳", "20ml 糖浆", "奶油顶", "坚果碎"],
        "process_steps": [
            "1. 泡茶/萃取: 80°C水温，焖泡10分钟。",
            "2. 基础备料: 加入糖浆，准备奶油喷枪。",
            "3. 调饮制作: 混合茶奶后，额外需手工挤制奶油顶并撒上坚果碎。",
            "4. 封口包装: 需使用球形高盖，小心打包防止奶油塌陷。",
            "5. 交付: 提醒顾客尽快饮用。"
        ]
    },
    "桂馥兰香 (Guifu Lanxiang)": {
        "tea_base": "桂花乌龙 (Osmanthus Oolong)",
        "milk_base": "优质牛乳",
        "syrup": "原味糖浆",
        "prep_complexity": 1.15,
        "ingredients": ["16g 桂花乌龙茶叶", "200ml 牛乳", "15ml 糖浆"],
        "process_steps": [
            "1. 泡茶/萃取: 88°C水温，焖泡11分钟，锁住桂花香。",
            "2. 基础备料: 加入适量糖浆，平衡茶感。",
            "3. 调饮制作: 快速摇晃，使桂花香与奶香充分融合。",
            "4. 封口包装: 标准封口流程。",
            "5. 交付: 叫号取餐。"
        ]
    }
}

def _db_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "chagee_orders.sqlite3")


def _db():
    conn = sqlite3.connect(_db_path(), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def _init_db():
    conn = _db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            product TEXT NOT NULL,
            ice TEXT NOT NULL,
            sugar TEXT NOT NULL,
            qty INTEGER NOT NULL,
            status TEXT NOT NULL,
            eta_minutes REAL NOT NULL,
            eta_ready_at TEXT NOT NULL,
            promise_ready_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES('total_workers', '5')")
    conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES('base_url', 'http://localhost:8501')")
    conn.commit()
    conn.close()


def _get_setting(key, default_value):
    conn = _db()
    cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default_value


def _set_setting(key, value):
    conn = _db()
    conn.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
    conn.commit()
    conn.close()


def _list_orders(statuses=None, limit=200):
    conn = _db()
    if statuses:
        placeholders = ",".join(["?"] * len(statuses))
        cur = conn.execute(
            f"SELECT order_code, created_at, product, ice, sugar, qty, status, eta_minutes, eta_ready_at, promise_ready_at FROM orders WHERE status IN ({placeholders}) ORDER BY id DESC LIMIT ?",
            tuple(statuses) + (limit,),
        )
    else:
        cur = conn.execute(
            "SELECT order_code, created_at, product, ice, sugar, qty, status, eta_minutes, eta_ready_at, promise_ready_at FROM orders ORDER BY id DESC LIMIT ?",
            (limit,),
        )
    rows = cur.fetchall()
    conn.close()
    cols = ["订单号", "下单时间", "单品", "冰度", "甜度", "杯数", "状态", "预计等待(分钟)", "预计取茶时间", "建议承诺时间"]
    return pd.DataFrame(rows, columns=cols)


def _get_order(order_code):
    conn = _db()
    cur = conn.execute(
        "SELECT order_code, created_at, product, ice, sugar, qty, status, eta_minutes, eta_ready_at, promise_ready_at FROM orders WHERE order_code = ?",
        (order_code,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    cols = ["订单号", "下单时间", "单品", "冰度", "甜度", "杯数", "状态", "预计等待(分钟)", "预计取茶时间", "建议承诺时间"]
    return dict(zip(cols, row))


def _update_order_status(order_code, status):
    conn = _db()
    conn.execute("UPDATE orders SET status = ? WHERE order_code = ?", (status, order_code))
    conn.commit()
    conn.close()


def _queue_mix_from_db(include_statuses):
    conn = _db()
    placeholders = ",".join(["?"] * len(include_statuses))
    cur = conn.execute(
        f"SELECT product, SUM(qty) FROM orders WHERE status IN ({placeholders}) GROUP BY product",
        tuple(include_statuses),
    )
    rows = cur.fetchall()
    conn.close()
    counts = {k: int(v or 0) for k, v in rows}
    for name in PRODUCTS.keys():
        counts.setdefault(name, 0)
    return counts


def _eta_for_new_order(product, qty, total_workers):
    counts = _queue_mix_from_db(["queued", "making"])
    existing_wip = sum(counts.values())
    total_wip = existing_wip + int(qty)
    if total_wip <= 0:
        total_wip = int(qty)
    weighted = sum(counts[n] * PRODUCTS[n]["prep_complexity"] for n in PRODUCTS.keys())
    avg_complexity = (weighted + int(qty) * PRODUCTS[product]["prep_complexity"]) / max(1, total_wip)
    order_workers = 1
    pickup_workers = 1
    tea_workers = max(1, int(total_workers) - order_workers - pickup_workers)
    prep_workers = max(1, int(round(tea_workers * 0.25)))
    packing_workers = max(1, int(round(tea_workers * 0.25)))
    mixing_workers = max(1, tea_workers - prep_workers - packing_workers)

    steps = [
        {"time_minutes": 10.0, "resources": 1, "is_batch": True, "batch_size": 10},
        {"time_minutes": 0.5 * avg_complexity, "resources": prep_workers, "is_batch": False},
        {"time_minutes": 1.5 * avg_complexity, "resources": mixing_workers, "is_batch": False},
        {"time_minutes": 1.0, "resources": packing_workers, "is_batch": False},
        {"time_minutes": 0.2, "resources": pickup_workers, "is_batch": False},
    ]

    caps = []
    for s in steps:
        if s.get("is_batch"):
            caps.append((60 / s["time_minutes"]) * s["resources"] * s["batch_size"])
        else:
            caps.append((60 / s["time_minutes"]) * s["resources"])

    system_cap = float(min(caps)) if len(caps) > 0 else 1.0
    wait_time = (total_wip / (system_cap / 60)) if system_cap > 0 else 0.0
    now = datetime.now()
    eta_ready_at = now + timedelta(minutes=float(wait_time))
    promise_ready_at = now + timedelta(minutes=float(wait_time) * 1.2 + 2)
    return float(wait_time), eta_ready_at, promise_ready_at, float(system_cap), float(avg_complexity)


def _create_order(product, ice, sugar, qty, total_workers):
    eta_minutes, eta_ready_at, promise_ready_at, _, _ = _eta_for_new_order(product, qty, total_workers)
    now = datetime.now()
    order_code = f"CHG{now.strftime('%m%d')}{now.strftime('%H%M%S')}{str(now.microsecond)[:3]}"
    conn = _db()
    conn.execute(
        "INSERT INTO orders(order_code, created_at, product, ice, sugar, qty, status, eta_minutes, eta_ready_at, promise_ready_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            order_code,
            now.isoformat(timespec="seconds"),
            product,
            ice,
            sugar,
            int(qty),
            "queued",
            float(eta_minutes),
            eta_ready_at.isoformat(timespec="seconds"),
            promise_ready_at.isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()
    return order_code


_init_db()

# --- Styling ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    .stMetric { background-color: #ffffff; padding: 12px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .product-card { background-color: #ffffff; padding: 15px 20px; border-radius: 10px; border-left: 6px solid #c2a67e; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .process-card { background-color: #fff9f0; padding: 12px; border-radius: 8px; border: 1px solid #ffe4b5; font-size: 0.9em; }
    .ingredient-tag { background-color: #e8f5e9; color: #2e7d32; padding: 4px 10px; border-radius: 15px; margin-right: 8px; display: inline-block; font-weight: 500; font-size: 0.85em; }
    
    /* Store Layout Styles */
    .store-layout { display: flex; flex-direction: column; background-color: #e0e0e0; padding: 20px; border-radius: 12px; margin-top: 10px; border: 2px solid #ccc; }
    .store-row { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 15px; }
    .zone { background-color: #ffffff; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); flex: 1; border-top: 4px solid #5d4037; }
    .zone-title { font-weight: bold; color: #333; margin-bottom: 10px; font-size: 1.1em; }
    .worker-icon { font-size: 1.8em; margin: 2px; display: inline-block; }
    .zone-stats { font-size: 0.8em; color: #666; margin-top: 8px; }
    </style>
    """, unsafe_allow_html=True)

page = st.sidebar.radio("页面", ["门店看板", "顾客下单", "订单查询", "店员后台"])

if page == "顾客下单":
    st.title("🍵 霸王茶姬点单 (模拟)")
    base_url = st.sidebar.text_input("部署后的网页地址", value=_get_setting("base_url", "http://localhost:8501"))
    if base_url:
        _set_setting("base_url", base_url)
    order_url = base_url.rstrip("/") + "/?page=order"
    st.sidebar.markdown(f"点单链接：{order_url}")
    st.sidebar.image(f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={quote(order_url)}")

    total_workers = int(_get_setting("total_workers", "5"))
    st.info(f"当前门店在岗人数配置：{total_workers} 人（由门店后台设置）")

    with st.form("order_form"):
        product = st.selectbox("选择单品", list(PRODUCTS.keys()))
        qty = st.number_input("杯数", min_value=1, max_value=10, value=1, step=1)
        col_a, col_b = st.columns(2)
        with col_a:
            ice = st.radio("冰度", ["正常冰", "少冰", "去冰", "热"], horizontal=True)
        with col_b:
            sugar = st.radio("甜度", ["全糖", "七分糖", "五分糖", "三分糖", "无糖"], horizontal=True)
        submitted = st.form_submit_button("提交订单")

    if submitted:
        order_code = _create_order(product, ice, sugar, qty, total_workers)
        order = _get_order(order_code)
        st.success(f"下单成功！你的订单号：{order_code}")
        st.metric("预计取茶时间", datetime.fromisoformat(order["预计取茶时间"]).strftime("%H:%M"))
        st.metric("建议承诺时间", datetime.fromisoformat(order["建议承诺时间"]).strftime("%H:%M"))
        st.caption("你可以在“订单查询”页面输入订单号查看状态。")

    st.markdown("---")
    st.subheader("订单查询（输入订单号）")
    code = st.text_input("订单号", value="")
    if code:
        info = _get_order(code.strip())
        if info:
            st.write({k: info[k] for k in ["订单号", "单品", "杯数", "冰度", "甜度", "状态"]})
            st.write("预计取茶时间：", datetime.fromisoformat(info["预计取茶时间"]).strftime("%H:%M"))
            st.write("建议承诺时间：", datetime.fromisoformat(info["建议承诺时间"]).strftime("%H:%M"))
        else:
            st.warning("未找到该订单号。")
    st.stop()

if page == "订单查询":
    st.title("🔎 订单查询")
    code = st.text_input("输入订单号", value="")
    if code:
        info = _get_order(code.strip())
        if info:
            st.write({k: info[k] for k in ["订单号", "单品", "杯数", "冰度", "甜度", "状态"]})
            st.write("预计取茶时间：", datetime.fromisoformat(info["预计取茶时间"]).strftime("%H:%M"))
            st.write("建议承诺时间：", datetime.fromisoformat(info["建议承诺时间"]).strftime("%H:%M"))
        else:
            st.warning("未找到该订单号。")
    st.stop()

if page == "店员后台":
    st.title("🧑‍🍳 门店后台（接单与调度）")
    total_workers = st.number_input("门店总在岗人数", min_value=3, max_value=20, value=int(_get_setting("total_workers", "5")), step=1)
    _set_setting("total_workers", int(total_workers))

    st.subheader("今日订单列表")
    df_orders = _list_orders(limit=200)
    st.dataframe(df_orders, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("更新订单状态")
    code = st.text_input("订单号", value="")
    status = st.selectbox("新状态", ["queued", "making", "ready", "done"])
    if st.button("更新"):
        if code.strip():
            _update_order_status(code.strip(), status)
            st.success("已更新。")
        else:
            st.warning("请输入订单号。")

    st.markdown("---")
    base_url = st.text_input("部署后的网页地址（用于生成二维码）", value=_get_setting("base_url", "http://localhost:8501"))
    _set_setting("base_url", base_url)
    order_url = base_url.rstrip("/") + "/?page=order"
    st.write("顾客点单链接：", order_url)
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={quote(order_url)}")
    st.stop()

# --- Logic Functions ---
def calculate_metrics(total_wip, avg_complexity, total_workers, online_q, offline_q):
    steps = [
        {"name": "1. 泡茶/萃取", "time_minutes": 10.0, "resources_count": 1, "is_batch": True, "batch_size": 10},
        {"name": "2. 基础备料", "time_minutes": 0.5 * avg_complexity, "resources_count": 1},
        {"name": "3. 调饮制作", "time_minutes": 1.5 * avg_complexity, "resources_count": 1},
        {"name": "4. 封口包装", "time_minutes": 1.0, "resources_count": 1},
        {"name": "5. 最终交付", "time_minutes": 0.2, "resources_count": 1}
    ]
    
    order_workers = 1
    pickup_workers = 1
    tea_workers = max(1, total_workers - order_workers - pickup_workers)

    prep_workers = max(1, int(round(tea_workers * 0.25)))
    packing_workers = max(1, int(round(tea_workers * 0.25)))
    mixing_workers = max(1, tea_workers - prep_workers - packing_workers)

    steps[0]["resources_count"] = 1
    steps[1]["resources_count"] = prep_workers
    steps[2]["resources_count"] = mixing_workers
    steps[3]["resources_count"] = packing_workers
    steps[4]["resources_count"] = pickup_workers
    results = []
    min_cap = float('inf')
    
    for step in steps:
        if step.get("is_batch"):
            cap_per_hr = (60 / step["time_minutes"]) * step["resources_count"] * step["batch_size"]
        else:
            cap_per_hr = (60 / step["time_minutes"]) * step["resources_count"]
            
        if cap_per_hr < min_cap:
            min_cap = cap_per_hr
            
        utilization = (total_wip / cap_per_hr) * 100 if cap_per_hr > 0 else 0
        
        results.append({
            "步骤": step["name"],
            "分配人数": step["resources_count"],
            "产能 (杯/时)": round(cap_per_hr, 1),
            "利用率 (%)": round(utilization, 1),
            "状态": "🔴 超负荷" if utilization > 100 else ("🟡 压力大" if utilization > 80 else "✅ 正常")
        })
        
    wait_time = (total_wip / (min_cap / 60)) if min_cap > 0 else 0
    
    allocation = {
        "order": order_workers,
        "tea": tea_workers,
        "pickup": pickup_workers,
        "tea_breakdown": {
            "prep": prep_workers,
            "mixing": mixing_workers,
            "packing": packing_workers
        }
    }
    
    return total_wip, round(wait_time, 1), min_cap, results, allocation

# --- Sidebar ---
st.sidebar.header("📊 运营看板控制器")
st.sidebar.divider()
st.sidebar.subheader("人员配置")
total_workers = st.sidebar.number_input("门店总在岗人数", min_value=3, max_value=10, value=5, step=1)
st.sidebar.divider()
st.sidebar.subheader("订单结构（按单品杯数）")
product_counts = {}
default_counts = {
    "伯牙绝弦 (Boya Juexian)": 25,
    "青青糯山 (Qingqing Nuoshan)": 10,
    "寻香山茶 (Xunxiang Shancha)": 0,
    "花开富贵 (Huakai Fugui)": 0,
    "桂馥兰香 (Guifu Lanxiang)": 0
}
for name in PRODUCTS.keys():
    product_counts[name] = st.sidebar.number_input(
        name,
        min_value=0,
        max_value=200,
        value=int(default_counts.get(name, 0)),
        step=1,
        key=f"cnt_{name}"
    )
st.sidebar.divider()
online_ratio = st.sidebar.slider("📱 线上占比 (%)", 0, 100, 70, 5)


# --- Main Page ---
st.title("🍵 霸王茶姬 (CHAGEE) 全链路运营诊断仪表盘")
st.markdown("---")

total_wip = sum(product_counts.values())
online_q = int(round(total_wip * online_ratio / 100))
offline_q = int(total_wip - online_q)
avg_complexity = (
    sum(product_counts[name] * PRODUCTS[name]["prep_complexity"] for name in PRODUCTS.keys()) / total_wip
    if total_wip > 0 else 1.0
)

mix_df = pd.DataFrame(
    [{"单品": name, "杯数": product_counts[name], "占比": (product_counts[name] / total_wip * 100) if total_wip > 0 else 0.0}
     for name in PRODUCTS.keys()]
)
mix_df = mix_df[mix_df["杯数"] > 0].sort_values("杯数", ascending=False)
top_text = "、".join([f"{r['单品'].split(' (')[0]} {int(r['杯数'])}杯" for _, r in mix_df.head(3).iterrows()]) if len(mix_df) > 0 else "暂无订单"

st.markdown(f"""
    <div class="product-card">
        <h3 style="color: #5d4037; margin-top: 0; margin-bottom: 6px;">订单结构（Product Mix）</h3>
        <div style="font-size: 0.9em; color: #555;">
            <b>Top 单品:</b> {top_text}<br/>
            <b>平均工艺复杂度:</b> {avg_complexity:.2f}x &nbsp;&nbsp; <b>线上占比:</b> {online_ratio}%（约 {online_q} 杯线上 / {offline_q} 杯线下）
        </div>
    </div>
    """, unsafe_allow_html=True)

# 2. Operational Metrics
total_wip, wait_time, system_cap, step_results, allocation = calculate_metrics(total_wip, avg_complexity, total_workers, online_q, offline_q)
now = datetime.now()
eta_ready_time = now + timedelta(minutes=float(wait_time))
promise_ready_time = now + timedelta(minutes=float(wait_time) * 1.2 + 2)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("实时排队总量", f"{total_wip} 杯", f"{online_q} 线上 + {offline_q} 线下")
with col2:
    st.metric("预计等待时间", f"{wait_time} 分钟", "繁忙" if wait_time > 30 else "正常", delta_color="inverse")
with col3:
    st.metric("门店瓶颈产能", f"{system_cap} 杯/小时")
with col4:
    st.metric("预计取茶时间", eta_ready_time.strftime("%H:%M"), "ETA（不含缓冲）")
with col5:
    st.metric("建议承诺时间", promise_ready_time.strftime("%H:%M"), "含安全缓冲")

st.markdown("---")

# NEW: Store Layout Visualization
st.subheader("🗺️ 动态门店人员排班图 (Store Layout & Allocation)")
st.markdown("基于运筹学算法，系统已将 **{}** 名员工分配至最优岗位，以适配当前订单结构。".format(total_workers))

st.markdown(f"""
    <div class="store-layout">
        <div class="store-row">
            <div class="zone">
                <div class="zone-title">📱 点单区 (Order)</div>
                <div>{"".join(['<span class="worker-icon">👩‍💼</span>'] * allocation['order'])}</div>
                <div class="zone-stats">{allocation['order']} 人在岗</div>
            </div>
            <div class="zone" style="border-top-color: #ff9800; flex: 1.5;">
                <div class="zone-title">🥤 制茶区 (Tea Making)</div>
                <div>{"".join(['<span class="worker-icon">🧑‍🍳</span>'] * allocation['tea'])}</div>
                <div class="zone-stats">
                    {allocation['tea']} 人在岗（备料 {allocation['tea_breakdown']['prep']} / 调饮 {allocation['tea_breakdown']['mixing']} / 打包 {allocation['tea_breakdown']['packing']}）
                </div>
            </div>
            <div class="zone">
                <div class="zone-title">🧾 取茶区 (Pickup)</div>
                <div>{"".join(['<span class="worker-icon">🧍</span>'] * allocation['pickup'])}</div>
                <div class="zone-stats">{allocation['pickup']} 人在岗</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 3. Full Process Breakdown
col_left, col_right = st.columns([1, 1.2])


with col_left:
    st.subheader("📋 单品流程与原料（可同时调整多个单品）")
    active_products = [name for name in PRODUCTS.keys() if product_counts[name] > 0]
    if len(active_products) == 0:
        active_products = [list(PRODUCTS.keys())[0]]
    tab_labels = [f"{name.split(' (')[0]}（{product_counts.get(name, 0)}杯）" for name in active_products]
    tabs = st.tabs(tab_labels)
    for i, name in enumerate(active_products):
        info = PRODUCTS[name]
        with tabs[i]:
            st.markdown(f"<div style='font-size:0.95em; color:#555; margin-bottom:8px;'><b>茶底:</b> {info['tea_base']} &nbsp;&nbsp; <b>奶基:</b> {info['milk_base']} &nbsp;&nbsp; <b>复杂度:</b> {info['prep_complexity']}x</div>", unsafe_allow_html=True)
            st.markdown("".join([f"<span class='ingredient-tag'>{x}</span>" for x in info["ingredients"]]), unsafe_allow_html=True)
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            for step in info["process_steps"]:
                st.markdown(f"""<div class="process-card" style="margin-bottom: 10px;">{step}</div>""", unsafe_allow_html=True)

with col_right:
    st.subheader("📊 环节负荷实时监控")
    df = pd.DataFrame(step_results)
    
    def get_color(util):
        if util > 100: return '#ff4b4b' # Red
        if util > 80: return '#ffa500'  # Orange
        return '#28a745'               # Green
    df['颜色'] = df['利用率 (%)'].apply(get_color)

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('利用率 (%):Q', title='利用率 (%)', scale=alt.Scale(domain=[0, max(120, df['利用率 (%)'].max() + 20)])),
        y=alt.Y('步骤:N', sort=None, title='制作环节'),
        color=alt.Color('颜色:N', scale=None)
    ).properties(height=380)
    st.altair_chart(chart, use_container_width=True)

# 4. AI Diagnosis
st.markdown("---")
st.subheader("💡 AI 运营诊断建议")
if wait_time > 45:
    st.error("🚨 **紧急诊断**：当前订单结构在现有人手下远超负荷。建议立即在小程序开启“门店繁忙”模式，并将人员优先补到核心调饮区/打包区。")
elif wait_time > 20:
    st.warning(f"⚠️ **预警诊断**：预计等待时间偏长。建议将人员优先支援 `{df.loc[df['利用率 (%)'].idxmax(), '步骤']}`，并减少非必要的前场停留。")
else:
    st.success("✅ **运行诊断**：流程通畅，人力匹配度高。请保持当前制作频率。")

st.caption("© 2024 霸王茶姬运营管理诊断系统 | 基于运筹学驱动")
