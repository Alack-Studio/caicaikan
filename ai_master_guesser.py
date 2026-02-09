import streamlit as st
from openai import OpenAI

# ==========================================
# 1. 顶级 UI 美化 (深色侦探风格)
# ==========================================
st.set_page_config(page_title="Gemini 3 画影神探", page_icon="🕵️", layout="centered")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at center, #1a1c2c 0%, #0d0e17 100%); color: #ffffff; }
    /* 按钮样式：精致渐变 */
    div.stButton > button {
        border-radius: 12px;
        height: 3.5em;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none; font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(168, 85, 247, 0.4); }
    /* 对话气泡美化 */
    .stChatMessage { border-radius: 15px; background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 状态全局初始化
# ==========================================
init_states = {
    "messages": [],
    "game_over": False,
    "question_count": 0,
    "final_image_url": None,
    "current_ai_reply": "",
    "final_char_name": ""
}
for key, val in init_states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==========================================
# 3. WildCard & API 配置
# ==========================================
API_KEY = st.secrets.get("API_KEY", "")
if not API_KEY:
    st.error("🔑 请在 Streamlit Secrets 中配置 API_KEY")
    st.stop()

# 使用 WildCard 中转地址
client = OpenAI(api_key=API_KEY, base_url="https://api.gptsapi.net/v1")
CHAT_MODEL = "gemini-3-flash-preview"
IMAGE_MODEL = "dall-e-3"

# ==========================================
# 4. 核心功能函数
# ==========================================

def get_ai_response(user_input=None):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
    
    system_p = "你是一个顶级读心神算子。我心里想一个著名人物，你只能问是非题。请务必以问号结尾。当你确定答案时，用'答案是：[人名]'开头。"
    
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": system_p}, *st.session_state.messages],
            temperature=0.8
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.current_ai_reply = reply
        
        # 判定游戏结束
        has_q = "?" in reply or "？" in reply
        guess_keywords = ["答案是", "我猜", "他是", "你是想说"]
        
        # 必须至少提问过一次且满足结束条件
        if st.session_state.question_count > 0:
            if not has_q or any(w in reply for w in guess_keywords):
                st.session_state.game_over = True
                
    except Exception as e:
        st.error(f"🔮 维度连接波动: {e}")

# 提取名字并生成简笔画
def process_final_result(reply):
    try:
        # 1. 提取名字
        extract_res = client.chat.completions.create(
