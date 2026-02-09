import streamlit as st
from openai import OpenAI

# ==========================================
# 1. 顶级 UI 美化 (精致深色侦探风)
# ==========================================
st.set_page_config(page_title="Gemini 3 画影神探", page_icon="🕵️", layout="centered")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at center, #1a1c2c 0%, #0d0e17 100%); color: #ffffff; }
    /* 精致渐变按钮 */
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
    st.error("🔑 请在 Secrets 中配置 API_KEY")
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
        
        # 判定结束：必须提问过一次且满足结束条件
        has_q = "?" in reply or "？" in reply
        guess_keywords = ["答案是", "我猜", "他是", "你是想说"]
        
        if st.session_state.question_count > 0:
            if not has_q or any(w in reply for w in guess_keywords):
                st.session_state.game_over = True
                
    except Exception as e:
        st.error(f"🔮 维度连接波动: {e}")

def process_final_result(reply):
    try:
        # 1. 提取名字
        extract_res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "只提取文本中的人名，不要多余文字。"}, 
                {"role": "user", "content": reply}
            ]
        )
        name = extract_res.choices[0].message.content.strip()
        
        # 2. 生成简笔画头像 (确保括号完全闭合)
        img_res = client.images.generate(
            model=IMAGE_MODEL,
            prompt=f"Minimalist black line drawing avatar of {name}, pure white background, simple sketch style, hand-drawn contour lines, no color.",
            size="1024x1024"
        )
        return name, img_res.data[0].url
    except Exception as e:
        st.warning(f"🎨 画像绘制失败: {e}")
        return "神秘人物", None

# ==========================================
# 5. 界面渲染逻辑
# ==========================================
st.title("🕵️ Gemini 3：画影神探")

with st.sidebar:
    st.header("📊 侦测进度")
    st.write(f"已推理步数：**{st.session_state.question_count}**")
    if st.button("🔄 开启新局", use_container_width=True):
        for k in list(st.
