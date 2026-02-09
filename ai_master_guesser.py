import streamlit as st
from openai import OpenAI

# 1. UI 动态主题配置
st.set_page_config(page_title="AI 猜猜看", layout="centered")

# 初始化主题状态
if "theme" not in st.session_state:
    st.session_state.theme = "白天"

# 侧边栏：仅保留重开和主题切换
with st.sidebar:
    st.session_state.theme = st.radio("🌓 主题选择", ["白天", "夜晚"], horizontal=True)
    if st.button("🔄 重新开始", use_container_width=True):
        for k in ["msgs", "over", "count"]: 
            if k in st.session_state: del st.session_state[k]
        st.rerun()

# 根据主题定义颜色变量
if st.session_state.theme == "夜晚":
    bg, text, btn_bg, btn_txt, btn_brd, chat_bg = "#121212", "#E0E0E0", "#1E1E1E", "#E0E0E0", "#333333", "#1E1E1E"
else:
    bg, text, btn_bg, btn_txt, btn_brd, chat_bg = "#FFFFFF", "#1F1F1F", "#FFFFFF", "#31333F", "#E0E0E0", "#F8F9FA"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; color: {text}; }}
    /* 按钮样式优化：缩小高度、放大文字 */
    div.stButton > button {{
        border-radius: 10px; height: 3.2em; font-size: 1.25rem !important;
        font-weight: 600; border: 1px solid {btn_brd};
        background-color: {btn_bg}; color: {btn_txt}; width: 100%;
        margin-bottom: 8px; transition: 0.2s;
    }}
    div.stButton > button:active {{ transform: scale(0.97); }}
    /* 聊天气泡文字放大 */
    .stChatMessage p, .stMarkdown h3 {{ font-size: 1.35rem !important; color: {text}; line-height: 1.5; }}
    .stChatMessage {{ background-color: {chat_bg}; border-radius: 12px; padding: 5px 15px; margin-bottom: 10px; }}
    /* 移除多余页眉 */
    header {{visibility: hidden;}}
    /* 适配夜晚模式的单选框 */
    div[data-testid="stMarkdownContainer"] p {{ font-size: 1.1rem; color: {text}; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 核心状态初始化
ks = ["msgs", "over", "count", "model"]
for k in ks:
    if k not in st.session_state: 
        st.session_state[k] = [] if k=="msgs" else ("gemini-2.0-flash" if k=="model" else 0 if k=="count" else False)

# 3. API 配置
if "API_KEY" not in st.secrets:
    st.error("🔑 请配置 API_KEY"); st.stop()

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

# 4. 逻辑处理
def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    sys = "你是一个顶级读心者。我心里想一个著名人物，你通过是非题来猜。严禁前5轮询问性别或国籍。确定后以'答案是：[人名]'开头。"
    try:
        res = client.chat.completions.create(
            model=st.session_state.model, 
            messages=[{"role":"system","content":sys}] + st.session_state.msgs, 
            temperature=0.8
        )
        reply = res.choices[0].message.content
        st.session_state.msgs.append({"role": "assistant", "content": reply})
        if st.session_state.count > 0 and ("?" not in reply and "？" not in reply or "答案是" in reply):
            st.session_state.over = True
    except:
        st.error("📡 信号波动，请点击重试")

# 5. UI 渲染逻辑
if not st.session_state.msgs:
    st.write("---")
    st.session_state.model = st.radio(
        "🔮 选择挑战对象：",
        ["gemini-2.0-flash", "gemini-1.5-pro", "gpt-4o"],
        captions=["⚡ 极速推理", "🧠 深度逻辑", "⚖️ 稳健对弈"]
    )
    st.write("")
    if st.button("🚀 开始游戏", use_container_width=True, type="primary"):
        with st.spinner("🕵️ AI 正在同步思绪..."):
            ask_ai()
            st.rerun()

elif not st.session_state.over:
