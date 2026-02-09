import streamlit as st
from openai import OpenAI
import random

# 1. 极简精致 UI：强制色彩对比，解决白底白字问题
st.set_page_config(page_title="AI 猜猜看", layout="centered")

if "theme" not in st.session_state: st.session_state.theme = "白天"
if "msgs" not in st.session_state: st.session_state.msgs = []
if "role" not in st.session_state: st.session_state.role = "AI 猜"
if "over" not in st.session_state: st.session_state.over = False
if "model" not in st.session_state: st.session_state.model = "gemini-2.5-flash-lite"
if "pending" not in st.session_state: st.session_state.pending = None

with st.sidebar:
    st.session_state.theme = st.radio("🌓 视觉风格", ["白天", "夜晚"], horizontal=True)
    if st.button("🔄 重置所有进度", use_container_width=True):
        for k in ["msgs", "over", "pending"]: st.session_state[k] = [] if k=="msgs" else (None if k=="pending" else False)
        st.rerun()

# 定义精致主题色标
if st.session_state.theme == "夜晚":
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#121212", "#E0E0E0", "#1E1E1E", "#E0E0E0", "#333333", "rgba(255,255,255,0.05)"
else:
    # 修复：确保白天模式文字为深色（#2C3E50）
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#FFFFFF", "#2C3E50", "#FFFFFF", "#34495E", "#F0F0F0", "#F9FBFC"

st.markdown(f"""
    <style>
    /* 强制全局文字颜色，防止隐身 */
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label {{ 
        color: {txt} !important; 
        background-color: {bg}; 
        font-family: -apple-system, sans-serif; 
    }}
    /* 精致按钮样式 */
    div.stButton > button {{
        border-radius: 8px; height: 3.0em; font-size: 0.95rem; font-weight: 500;
        border: 1px solid {b_bd}; background-color: {b_bg}; color: {b_txt} !important;
        width: 100%; margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: 0.2s;
    }}
    div.stButton > button:active {{ transform: translateY(1px); }}
    /* 精致聊天气泡 */
    .stChatMessage {{ background-color: {c_bg}; border-radius: 10px; padding: 12px; border: 1px solid {b_bd}; margin-bottom: 12px; }}
    .stChatMessage p {{ font-size: 1.05rem !important; line-height: 1.6; }}
    header {{visibility: hidden;}}
    /* 加载动画文字 */
    .stSpinner p {{ font-size: 0.9rem !important; color: {txt}; opacity: 0.7; font-style: italic; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 核心逻辑与 API
client = OpenAI(api_key=st.secrets["API_
