import streamlit as st
from openai import OpenAI
import random

# 1. 精致 UI 强制色彩修正
st.set_page_config(page_title="AI 猜猜看", layout="centered")

for k, v in {"theme":"白天", "msgs":[], "role":"AI 猜", "over":False, "model":"gemini-2.5-flash-lite", "pending":None}.items():
    if k not in st.session_state: st.session_state[k] = v

with st.sidebar:
    st.session_state.theme = st.radio("🌓 风格", ["白天", "夜晚"], horizontal=True)
    if st.button("🔄 重置", use_container_width=True):
        st.session_state.msgs, st.session_state.over, st.session_state.pending = [], False, None
        st.rerun()

# 精致色彩方案：解决白天模式“白字”问题
if st.session_state.theme == "夜晚":
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#121212", "#D1D1D1", "#1E1E1E", "#D1D1D1", "#333333", "rgba(255,255,255,0.05)"
else:
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#FFFFFF", "#2C3E50", "#FFFFFF", "#34495E", "#F0F0F0", "#F9FBFC"

st.markdown(f"""
    <style>
    .stApp, .stApp p, .stApp h1, .stApp h3, .stApp label {{ color: {txt} !important; background-color: {bg}; font-family: -apple-system, sans-serif; }}
    div.stButton > button {{
        border-radius: 8px; height: 3.0em; font-size: 0.95rem; font-weight: 500;
        border: 1px solid {b_bd}; background-color: {b_bg}; color: {b_txt} !important;
        width: 100%; margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    .stChatMessage {{ background-color: {c_bg}; border-radius: 10px; padding: 12px; border: 1px solid {b_bd}; margin-bottom: 10px; }}
    .stChatMessage p {{ font-size: 1.05rem !important; line-height: 1.6; }}
    header {{visibility: hidden;}}
    .stSpinner p {{ font-size: 0.9rem !important; color: {txt}; opacity: 0.7; font-style: italic; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. API 逻辑：修复截断问题
if "API_KEY" not in st.secrets:
    st.error("🔑 Secrets 未配置 API_KEY"); st.stop()

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    waits = ["正在同步脑电波...", "正在翻阅档案...", "正在感知心思...", "正在锁定目标..."]
    with st.spinner(random.choice(waits)):
        if st.session_state.role == "AI 猜":
            sys = "你猜。严禁前5轮问性别国籍。确定后以'答案是：[人名]'开头。"
        else:
            sys = "我猜。你选定一个世界著名人物。仅答'是/否/模糊'并附带一条模糊线索。用户猜中即宣布获胜。"
        try:
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.8)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            if any(x in reply for x in ["答案是", "获胜", "恭喜"]) or (st.session_state.role == "AI 猜" and "?" not in reply and "？" not in reply):
                st.session_state.over = True
        except Exception as e: st.error(f"📡 API 异常: {str(e)}")

if st.session_state.pending:
    ans = st.session_state.pending
    st.session_state.pending = None
    ask_ai(ans); st.rerun()

# 3. 游戏流程
if not st.session_state.msgs:
    st.session_state.role = st.radio("🎭 模式", ["AI 猜 (它问我答)", "我猜 (我问它答)"], horizontal=True)
    st.session_state.model = st.radio("🔮 对象", ["gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3-pro-preview"], captions=["稳定极速", "深度逻辑", "终极智商"])
    if st.button("🚀 启动", use_container_width=True, type="primary"):
        ask_ai(); st.rerun()
elif not st.session_state.over:
    st.chat_message("assistant", avatar="🕵️").markdown(st.session_state.msgs[-1]['content'])
    if st.session_state.role == "AI 猜":
        st.divider()
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 是", use_container_width=True, type="primary"): st.session_state.pending = "是的"; st.rerun()
        if c2.button("❌ 否", use_container_width=True): st.session_state.pending = "不是"; st.rerun()
        if c3.button("❔ 模糊", use_container_width=True): st.session_state.pending = "不确定"; st.rerun()
    else:
        q = st.chat_input("向 AI 提问...")
        if q: ask_ai(q); st.rerun()
else:
    st.balloons()
    st.chat_message("assistant", avatar="🎯").markdown(st.session_state.msgs[-1]['content'])
    if st.button("🎮 再玩一局", use_container_width=True, type="primary"):
        st.session_state.msgs, st.session_state.over = [], False
        st.rerun()
