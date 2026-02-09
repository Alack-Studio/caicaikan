import streamlit as st
import google.generativeai as genai
import time

# ==========================================
# 1. 核心配置与神秘感设置
# ==========================================
st.set_page_config(
    page_title="AI 读心神算子",
    page_icon="🕵️",
    layout="centered"
)

# 自定义 CSS 装饰
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        border-color: #ff4b4b;
    }
    .question-box {
        background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

if "GEMINI_API_KEY" not in st.secrets:
    st.error("🔑 请在控制台配置 API Key")
    st.stop()

API_KEY = "".join(st.secrets["GEMINI_API_KEY"].split())
genai.configure(api_key=API_KEY)
MODEL_NAME = 'models/gemini-flash-latest'
model = genai.GenerativeModel(MODEL_NAME)

# ==========================================
# 2. 辅助函数
# ==========================================
def safe_send(chat, msg):
    try:
        response = chat.send_message(msg)
        return response.text, None
    except Exception as e:
        err = str(e)
        if "429" in err: return None, "LIMIT"
        return None, err

# ==========================================
# 3. 侧边栏：规则与进度
# ==========================================
with st.sidebar:
    st.title("🕵️ 读心屋说明")
    st.markdown("""
    1. 在心中想好一个**著名人物**（古今中外皆可）。
    2. AI 会通过是非题来缩小范围。
    3. 如果 AI 猜到了，请大方承认！
    """)
    st.divider()
    if "question_count" in st.session_state:
        st.write(f"📊 此时进度：**第 {st.session_state.question_count + 1} 步**")
        # 模拟进度条，假设 20 步内猜出
        progress = min(st.session_state.question_count / 20, 1.0)
        st.progress(progress)
    
    if st.button("🔄 开启新局", type="secondary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# ==========================================
# 4. 游戏启动逻辑
# ==========================================
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.game_over = False
    st.session_state.question_count = 0
    st.session_state.history_display = [] # 用于展示对话流
    
    with st.status("🔮 正在穿越时空连接 AI 大脑...", expanded=True) as status:
        prompt = "你现在是一个读心神算子。我心里想一个著名人物。你只能问是非题。请开始。"
        res, err = safe_send(st.session_state.chat_session, prompt)
        if res:
            st.session_state.current_question = res
            status.update(label="✅ 大脑已连接！请开始挑战。", state="complete")
        else:
            st.error(f"连接失败: {err}")
            st.stop()

# ==========================================
# 5. 主交互界面
# ==========================================
st.header("🕵️ AI 读心神算子")

if not st.session_state.game_over:
    # 展示 AI 的问题
    with st.chat_message("assistant", avatar="🔮"):
        st.markdown(f"#### {st.session_state.current_question}")
    
    st.write("---")
    st.caption("👇 请选择你的回答：")
    
    # 交互
