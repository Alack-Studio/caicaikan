import streamlit as st
from openai import OpenAI
import random

# 1. 精致对话 UI 配置
st.set_page_config(page_title="AI 猜猜看", layout="centered")

# 初始化状态
states = {"theme":"白天", "msgs":[], "role":"AI 猜", "over":False, "model":"gemini-2.5-flash-lite"}
for k, v in states.items():
    if k not in st.session_state: st.session_state[k] = v

with st.sidebar:
    st.session_state.theme = st.radio("🌓 风格", ["白天", "夜晚"], horizontal=True)
    if st.button("🔄 重置对话", use_container_width=True):
        st.session_state.msgs, st.session_state.over = [], False
        st.rerun()

# 色彩定义
if st.session_state.theme == "夜晚":
    bg, txt, b_bg, b_txt, b_bd, c_ai, c_usr = "#121212", "#D1D1D1", "#1E1E1E", "#D1D1D1", "#333333", "#262626", "#1E3A5F"
else:
    bg, txt, b_bg, b_txt, b_bd, c_ai, c_usr = "#FFFFFF", "#2C3E50", "#FFFFFF", "#34495E", "#F0F0F0", "#F0F4F8", "#E3F2FD"

st.markdown(f"""
    <style>
    /* 全局精致感控制 */
    .stApp {{ background-color: {bg}; color: {txt} !important; font-family: -apple-system, sans-serif; }}
    .stApp p, .stApp h1, .stApp h3, .stApp label {{ color: {txt} !important; }}
    /* 聊天气泡精致化：1.05rem 字体 */
    [data-testid="stChatMessage"] {{ background-color: transparent !important; border: none !important; }}
    .stChatMessage p {{ font-size: 1.05rem !important; line-height: 1.6; color: {txt} !important; }}
    /* 修正按钮：0.95rem 字体 */
    div.stButton > button {{
        border-radius: 8px; height: 2.8em; font-size: 0.95rem; border: 1px solid {b_bd};
        background-color: {b_bg}; color: {b_txt} !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 核心 API 与 逻辑
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    waits = ["正在同步脑电波...", "正在检索档案...", "正在感知心思..."]
    with st.spinner(random.choice(waits)):
        sys = "你猜。严禁前5轮问性别国籍。猜中后以'答案是：[人名]'开头。" if st.session_state.role == "AI 猜" else "我猜。你选定一个名人。仅答'是/否/模糊'并附带简短提示。猜中即宣布获胜。"
        try:
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.8)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            if any(x in reply for x in ["答案是", "获胜", "恭喜"]) or (st.session_state.role == "AI 猜" and "?" not in reply and "？" not in reply):
                st.session_state.over = True
        except Exception as e: st.error(f"📡 API 异常: {str(e)}")

# 3. 对话流渲染
if not st.session_state.msgs:
    st.session_state.role = st.radio("🎭 模式", ["AI 猜 (它问我答)", "我猜 (我问它答)"], horizontal=True)
    st.session_state.model = st.radio("🔮 对象", ["gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3-pro-preview"], captions=["快速", "深度", "终极"])
    if st.button("🚀 开启对话", use_container_width=True, type="primary"):
        ask_ai(); st.rerun()
else:
    # 渲染历史记录
    for m in st.session_state.msgs:
        with st.chat_message(m["role"], avatar="🕵️" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    if not st.session_state.over:
        st.divider()
        if st.session_state.role == "AI 猜":
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ 是", use_container_width=True, type="primary"): ask_ai("是的"); st.rerun()
            if c2.button("❌ 否", use_container_width=True): ask_ai("不是"); st.rerun()
            if c3.button("❔ 模糊", use_container_width=True): ask_ai("不确定"); st.rerun()
        else:
            q = st.chat_input("向 AI 提问...")
            if q: ask_ai(q); st.rerun()
    else:
        st.balloons()
        st.success("🎯 游戏已结束")
        if st.button("🎮 重新来过", use_container_width=True, type="primary"):
            st.session_state.msgs, st.session_state.over = [], False
            st.rerun()
