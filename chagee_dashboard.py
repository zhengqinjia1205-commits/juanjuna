import streamlit as st
import pandas as pd
import math
import altair as alt

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

# --- Styling ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .product-card { background-color: #ffffff; padding: 25px; border-radius: 15px; border-left: 10px solid #c2a67e; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .process-card { background-color: #fff9f0; padding: 20px; border-radius: 10px; border: 1px solid #ffe4b5; }
    .ingredient-tag { background-color: #e8f5e9; color: #2e7d32; padding: 5px 12px; border-radius: 20px; margin-right: 10px; display: inline-block; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- Logic Functions ---
def calculate_metrics(online_q, offline_q, complexity=1.0):
    steps = [
        {"name": "1. 泡茶/萃取", "time_minutes": 10.0, "resources_count": 1, "is_batch": True, "batch_size": 10},
        {"name": "2. 基础备料", "time_minutes": 0.5 * complexity, "resources_count": 1},
        {"name": "3. 调饮制作", "time_minutes": 1.5 * complexity, "resources_count": 2},
        {"name": "4. 封口包装", "time_minutes": 1.0, "resources_count": 1},
        {"name": "5. 最终交付", "time_minutes": 0.2, "resources_count": 1}
    ]
    
    total_wip = online_q + offline_q
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
            "产能 (杯/时)": cap_per_hr,
            "利用率 (%)": round(utilization, 1),
            "状态": "🔴 超负荷" if utilization > 100 else ("🟡 压力大" if utilization > 80 else "✅ 正常")
        })
        
    wait_time = (total_wip / (min_cap / 60)) if min_cap > 0 else 0
    return total_wip, round(wait_time, 1), min_cap, results

# --- Sidebar ---
st.sidebar.header("📊 运营看板控制器")
selected_product = st.sidebar.selectbox("选择当前单品", list(PRODUCTS.keys()))
st.sidebar.divider()
online_q = st.sidebar.slider("📱 线上排队 (杯)", 0, 100, 30)
offline_q = st.sidebar.slider("🛍️ 线下排队 (杯)", 0, 50, 15)

# --- Main Page ---
st.title("🍵 霸王茶姬 (CHAGEE) 全链路运营诊断仪表盘")
st.markdown("---")

# 1. Product & Ingredients Display
product_info = PRODUCTS[selected_product]
st.markdown(f"""
    <div class="product-card">
        <h2 style="color: #5d4037;">当前单品：{selected_product}</h2>
        <div style="margin: 15px 0;">
            <p><b>🔍 配方清单 (Recipe):</b></p>
            {" ".join([f'<span class="ingredient-tag">{i}</span>' for i in product_info['ingredients']])}
        </div>
        <div style="background-color: #fafafa; padding: 15px; border-radius: 8px;">
            <p><b>💡 工艺概览:</b> 该产品使用 <b>{product_info['tea_base']}</b> 作为茶底，与 <b>{product_info['milk_base']}</b> 融合，工艺复杂度为 <b>{product_info['prep_complexity']}x</b>。</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 2. Operational Metrics
total_wip, wait_time, system_cap, step_results = calculate_metrics(online_q, offline_q, product_info['prep_complexity'])
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("实时排队总量", f"{total_wip} 杯", f"{online_q} 线上 + {offline_q} 线下")
with col2:
    st.metric("预计等待时间", f"{wait_time} 分钟", "繁忙" if wait_time > 30 else "正常", delta_color="inverse")
with col3:
    st.metric("门店瓶颈产能", f"{system_cap} 杯/小时")
with col4:
    tea_needed = math.ceil(total_wip / 10)
    st.metric(f"{product_info['tea_base']} 需求", f"{tea_needed} 桶", f"每桶 10 杯")

st.markdown("---")

# 3. Full Process Breakdown
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("📋 全链路制作流程 (The Journey)")
    for step in product_info['process_steps']:
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
    st.error(f"🚨 **紧急诊断**：当前 `{selected_product}` 需求远超负荷。请立即在小程序开启“门店繁忙”模式。")
elif wait_time > 20:
    st.warning(f"⚠️ **预警诊断**：预计等待时间过长。建议抽调收银员支援 `{df.loc[df['利用率 (%)'].idxmax(), '步骤']}` 环节。")
else:
    st.success("✅ **运行诊断**：流程通畅，人力匹配度高。请保持当前制作频率。")

st.caption("© 2024 霸王茶姬运营管理诊断系统 | 基于运筹学驱动")
