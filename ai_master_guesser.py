import streamlit as st
from openai import OpenAI
import random

# 1. 精致 UI 配置
st.set_page_config(page_title="AI 猜猜看", layout="centered")

if "theme" not in st.session_state: st.session_state.theme = "白天"
if "msgs" not in st.session_state: st.session_state.msgs = []
if "role" not in st.session_state: st.session_state.role = "AI 猜"
if "over" not in st.session_state: st.session_state.over = False
if "model" not in st.session_state: st.session_state.model = "gemini-2.5-flash-lite"
if "pending" not in st.session_state: st.session_state.pending = None

with st.sidebar:
    st.session_state.theme = st.radio("🌓 风格", ["白天", "夜晚"], horizontal=True)
    if st.button("🔄 重置进度", use_container_width=True):
        for k in ["msgs", "over", "pending"]: st.session_state[k] = [] if k=="msgs" else (None if k=="pending" else False)
        st.rerun()

# 定义精致主题
if st.session_state.theme == "夜晚":
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#121212", "#D1D1D1", "#1E1E1E", "#D1D1D1", "#2D2D2D", "rgba(255,255,255,0.05)"
else:
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#FFFFFF", "#2C3E50", "#FFFFFF", "#34495E", "#F0F0F0", "#F9FBFC"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; color: {txt}; font-family: -apple-system, sans-serif; }}
    div.stButton > button {{
        border-radius: 8px; height: 3.0em; font-size: 0.95rem; font-weight: 500;
        border: 1px solid {b_bd}; background-color: {b_bg}; color: {b_txt};
        width: 100%; margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: all 0.2s;
    }}
    div.stButton > button:active {{ transform: translateY(1px); }}
    .stChatMessage p, .stMarkdown h3 {{ font-size: 1.05rem; color: {txt}; line-height: 1.6; }}
    .stChatMessage {{ background-color: {c_bg}; border-radius: 10px; padding: 12px; border: 1px solid {b_bd}; margin-bottom: 10px; }}
    header {{visibility: hidden;}}
    /* 加载动画文字样式 */
    .stSpinner p {{ font-size: 0.9rem; color: {txt}; opacity: 0.7; font-style: italic; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 核心逻辑与 API
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    
    # 趣味等待文案集
    wait_texts = ["正在同步脑电波...", "正在翻阅历史档案...", "正在感知你的心思...", "正在编织逻辑线索...", "正在锁定目标维度..."]
    
    with st.spinner(random.choice(wait_texts)):
        sys = "你猜。严禁前5轮问性别国籍。确定后以'答案是：[人名]'开头。" if st.session_state.role == "AI 猜" else "我猜。你选定一个世界著名人物，仅回答'是/否/模糊'。"
        try:
            res = client.chat.completions.create(
                model=st.session_state.model, 
                messages=[{"role": "system", "content": sys}] + st.session_state.msgs,
                temperature=0.8
            )
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role": "assistant", "content": reply})
            if "答案是" in reply or (st.session_state.role == "AI 猜" and "?" not in reply and "？" not in reply):
                st.session_state.over = True
        except Exception as e:
            st.error(f"📡 API 访问异常: {str(e)}")

# 3. 处理点击后的待办逻辑
if st.session_state.pending:
    ans = st.session_state.pending
    st.session_state.pending = None
    ask_ai(ans)
    st.rerun()

# 4. UI 流程渲染
if not st.session_state.msgs:
    st.session_state.role = st.radio("🎭 模式：", ["AI 猜 (它问我答)", "我猜 (我问它答)"], horizontal=True)
    st.session_state.model = st.radio("🔮 挑战对象", ["gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3-pro-preview"], captions=["极速", "深度", "终极"])
    if st.button("🚀 启动游戏", use_container_width=True, type="primary"):
        ask_ai()
        st.rerun()

elif not st.session_state.over:
    st.chat_message("assistant", avatar="🕵️").markdown(f"### {st.session_state.msgs[-1]['content']}")
    
    if st.session_state.role == "AI 猜":
        st.divider()
        c1, c2, c3 = st.columns(3)
        # 点击后存入 pending 状态，触发主循环的 ask_ai
        if c1.button("✅ 是", use_container_width=True, type="primary"): 
            st.session_state.pending = "是的"; st.rerun()
        if c2.button("❌ 否", use_container_width=True): 
            st.session_state.pending = "不是"; st.rerun()
        if c3.button("❔ 模糊", use_container_width=True): 
            st.session_state.pending = "不确定"; st.rerun()
    else:
        q = st.chat_input("向 AI 提问...")
        if q: ask_ai(q); st.rerun()

else:
    st.balloons()
    st.chat_message("assistant", avatar="🎯").markdown(f"### {st.session_state.msgs[-1]['content']}")
    if st.button("🎮 再玩一局", use_container_width=True, type="primary"):
        st.session_state.msgs, st.session_state.over = [], False
        st.rerun()
