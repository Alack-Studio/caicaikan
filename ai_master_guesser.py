import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 页面配置与样式
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🔮", layout="centered")

st.markdown("""
    <style>
    div.stButton > button {
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 15px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 状态全局初始化 (防止 AttributeError)
# ==========================================
# 这一步非常关键：确保所有变量在运行前都已存在
init_values = {
    "chat_session": None,
    "game_over": False,
    "question_count": 0,
    "error_msg": None,
    "current_question": "🔮 正在唤醒 AI 大脑..."
}

for key, value in init_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# 3. API 配置
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("🔑 请在 Streamlit 控制台配置 GEMINI_API_KEY")
    st.stop()

API_KEY = "".join(st.secrets["GEMINI_API_KEY"].split())
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

def safe_send(chat, msg):
    try:
        response = chat.send_message(msg)
        return response.text, None
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg: return None, "LIMIT"
        return None, err_msg

# ==========================================
# 4. 回调函数处理逻辑
# ==========================================
def handle_user_choice(ans_text):
    st.session_state.question_count += 1
    res, err = safe_send(st.session_state.chat_session, ans_text)
    
    if err == "LIMIT":
        st.session_state.question_count -= 1
        st.session_state.error_msg = "⏰ 频率太快，请等 10 秒再点。"
    elif err:
        st.session_state.error_msg = f"❌ 错误: {err}"
    else:
        st.session_state.current_question = res
        st.session_state.error_msg = None
        
        # 判定结束逻辑
        has_q = "?" in res or "？" in res
        is_guess = any(w in res for w in ["猜", "名字是", "他是", "我想到了"])
        if not has_q or is_guess:
            st.session_state.game_over = True

# ==========================================
# 5. 首次启动 AI 会话
# ==========================================
if st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])
    with st.spinner("🔮 正在连接 AI 大脑..."):
        prompt = "你现在是一个读心神算子。我心里想一个著名人物。你问是非题猜他是谁。请开始第一问。"
        res, err = safe_send(st.session_state.chat_session, prompt)
        if res:
            st.session_state.current_question = res
        else:
            st.error(f"启动失败: {err}")
            st.stop()

# ==========================================
# 6. 界面渲染
# ==========================================
st.title("🕵️ AI 读心神算子")

with st.sidebar:
    st.header("📊 战况")
    st.write(f"步数：{st.session_state.question_count}")
    if st.button("🔄 重新开始", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# 安全检查 error_msg
if st.session_state.get("error_msg"):
    st.warning(st.session_state.error_msg)

if not st.session_state.game_over:
    st.chat_message("assistant", avatar="🔮").write(st.session_state.current_question)
    st.divider
