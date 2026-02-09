import streamlit as st
from openai import OpenAI
import random

# 1. 对话式 UI 配置：精致字号与色彩修正
st.set_page_config(page_title="AI 猜猜看", layout="centered")

# 初始化状态
states = {"theme":"白天", "msgs":[], "role":"AI 猜", "over":False, "model":"gemini-2.5-flash-lite", "pending":None}
for k, v in states.items():
    if k not in st.session_state: st.session_state[k] = v

with st.sidebar:
    st.session_state.theme = st.radio("🌓 风格", ["白天", "夜晚"], horizontal=True)
    if st.button("🔄 重置所有进度", use_container_width=True):
        st.session_state.msgs, st.session_state.over = [], False
        st.rerun()

# 定义色彩
if st.session_state.theme == "夜晚":
    bg, txt, b_bd, c_bg = "#121212", "#D1D1D1", "#333333", "rgba(255,255,255,0.05)"
else:
    bg, txt, b_bd, c_bg = "#FFFFFF", "#2C3E50", "#F0F0F0", "#F9FBFC"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; color: {txt} !important; font-family: -apple-system, sans-serif; }}
    .stApp p, .stApp h1, .stApp h3, .stApp label {{ color: {txt} !important; }}
    /* 聊天气泡：1.05rem 精致字号 */
    .stChatMessage {{ background-color: {c_bg} !important; border-radius: 12px; padding: 10px; border: 1px solid {b_bd}; margin-bottom: 10px; }}
    .stChatMessage p {{ font-size: 1.05rem !important; line-height: 1.6; color: {txt} !important; }}
    /* 快捷按钮样式：精致小巧 */
    .quick-btn {{ margin-top: -15px; margin-bottom: 10px; }}
    div.stButton > button {{
        border-radius: 20px; height: 2.2em; font-size: 0.85rem; padding: 0 15px;
        background-color: transparent; color: {txt} !important; border: 1px solid {b_bd};
    }}
    header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 核心 API 与 逻辑
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    waits = ["正在同步脑电波...", "正在感知心思...", "正在编织线索..."]
    with st.spinner(random.choice(waits)):
        if st.session_state.role == "AI 猜":
            sys = "你猜。严禁前5轮问性别国籍。猜中后以'答案是：[人名]'开头。"
        else:
            sys = "我猜。你选定一个名人。仅答'是/否/模糊'并附带简短提示。如果用户说猜不到或要求换人，请大方揭晓答案。"
        try:
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.8)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            if any(x in reply for x in ["答案是", "获胜", "恭喜", "真相是"]) or (st.session_state.role == "AI 猜" and "?" not in reply and "？" not in reply):
                st.session_state.over = True
        except Exception as e: st.error(f"📡 API 异常: {str(e)}")

# 处理按钮待办
if st.session_state.pending:
    ans = st.session_state.pending
    st.session_state.pending = None
    ask_ai(ans); st.rerun()

# 3. 对话流渲染
if not st.session_state.msgs:
    st.session_state.role = st.radio("🎭 模式", ["AI 猜 (它问我答)", "我猜 (我问它答)"], horizontal=True)
    st.session_state.model = st.radio("🔮 对象", ["gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3-pro-preview"], captions=["快速", "深度", "终极"])
    if st.button("🚀 开启对话", use_container_width=True, type="primary"):
        ask_ai(); st.rerun()
else:
    for m in st.session_state.msgs:
        with st.chat_message(m["role"], avatar="🕵️" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    if not st.session_state.over:
        st.divider()
        if st.session_state.role == "AI 猜":
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ 是", use_container_width=True): st.session_state.pending = "是的"; st.rerun()
            if c2.button("❌ 否", use_container_width=True): st.session_state.pending = "不是"; st.rerun()
            if c3.button("❔ 模糊", use_container_width=True): st.session_state.pending = "不确定"; st.rerun()
        else:
            # 快捷短语栏
            sc1, sc2, sc3, sc4 = st.columns([1, 1.2, 1.2, 1])
            if sc1.button("💡 提示"): st.session_state.pending = "请多给点提示。"; st.rerun()
            if sc2.button("🙅 猜不到"): st.session_state.pending = "我想不出来了，请揭晓答案。"; st.rerun()
            if sc3.button("🔄 换个人"): 
                st.session_state.msgs = []
                ask_ai("请换一个人物开始游戏。")
                st.rerun()
            
            q = st.chat_input("向 AI 提问...")
            if q: ask_ai(q); st.rerun()
    else:
        st.balloons()
        if st.button("🎮 再玩一局", use_container_width=True, type="primary"):
            st.session_state.msgs, st.session_state.over = [], False
            st.rerun()
