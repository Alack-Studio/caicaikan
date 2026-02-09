import streamlit as st
from openai import OpenAI

# ==========================================
# 1. 界面配置 (回归清爽简洁风格)
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🕵️", layout="centered")

# 移除复杂的暗黑滤镜，回归高易读性
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    /* 回归标准明亮按钮 */
    div.stButton > button {
        border-radius: 8px;
        height: 3.5em;
        font-weight: bold;
        border: 1px solid #d1d3d8;
        background-color: #ffffff;
        color: #31333F;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
    }
    /* 聊天气泡背景优化 */
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
    }
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
    "final_char_name": ""
}
for key, val in init_states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==========================================
# 3. API 配置 (WildCard)
# ==========================================
API_KEY = st.secrets.get("API_KEY", "")
if not API_KEY:
    st.error("🔑 请在 Secrets 中配置 API_KEY")
    st.stop()

client = OpenAI(api_key=API_KEY, base_url="https://api.gptsapi.net/v1")
CHAT_MODEL = "gemini-3-flash-preview"
IMAGE_MODEL = "dall-e-3"

# ==========================================
# 4. 核心功能函数
# ==========================================

def get_ai_response(user_input=None):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 强制 AI 逻辑
    system_p = "你是一个顶级读心神算子。我心里想一个著名人物，你只能问是非题。请务必以问号结尾。当你确定答案时，直接给出名字，不要问号。"
    
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": system_p}] + st.session_state.messages,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # 判定逻辑：只有在提问过后且没有问号时才结束
        has_q = "?" in reply or "？" in reply
        if st.session_state.question_count > 0 and not has_q:
            st.session_state.game_over = True
                
    except Exception as e:
        st.error(f"❌ 网络连接异常: {e}")

def process_final_result(reply):
    try:
        # 提取名字
        ext = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "提取文本中的人物全名。"}, {"role": "user", "content": reply}]
        )
        name = ext.choices[0].message.content.strip()
        
        # 生成真实风格图片 (去掉了简笔画风格化)
        img_res = client.images.generate(
            model=IMAGE_MODEL,
            prompt=f"A professional portrait of {name}, cinematic lighting, high quality, 4k.",
            size="1024x1024"
        )
        return name, img_res.data[0].url
    except:
        return "神秘人物", None

# ==========================================
