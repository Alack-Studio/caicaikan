import streamlit as st
from openai import OpenAI

# ==========================================
# 1. 页面配置 (清爽明亮风格)
# ==========================================
st.set_page_config(page_title="AI 猜猜看", page_icon="🕵️", layout="centered")

# 强制设置背景为纯白，确保简笔画完美融合
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1F1F1F; }
    /* 按钮样式：简洁高对比度 */
    div.stButton > button {
        border-radius: 8px;
        height: 3.5em;
        font-weight: bold;
        border: 1px solid #E0E0E0;
        background-color: #FFFFFF;
        color: #31333F;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        border-color: #FF4B4B;
        color: #FF4B4B;
    }
    /* 气泡样式 */
    .stChatMessage {
        background-color: #F8F9FA;
        border-radius: 12px;
        border: 1px solid #F0F0F0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 状态初始化 (放在渲染前，防止空白)
# ==========================================
st.title("🕵️ AI 猜猜看")

if "messages" not in st.session_state: st.session_state.messages = []
if "game_over" not in st.session_state: st.session_state.game_over = False
if "question_count" not in st.session_state: st.session_state.question_count = 0
if "final_img" not in st.session_state: st.session_state.final_img = None
if "char_name" not in st.session_state: st.session_state.char_name = ""

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
# 4. 逻辑函数
# ==========================================

def get_ai_response(user_input=None):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
    
    sys_p = "你是一个顶级读心者。我心里想一个著名人物，你只能问是非题。一次一问。必须以问号结尾。确定答案后以'答案是：[人名]'开头。"
    
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": sys_p}] + st.session_state.messages,
            temperature=0.8
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # 判定逻辑：至少提问1次，且没有问号或包含答案关键词
        has_q = "?" in reply or "？" in reply
        if st.session_state.question_count > 0 and (not has_q or "答案是" in reply):
            st.session_state.game_over = True
                
    except Exception as e:
        st.error(f"📡 连接中断，请重试: {e}")

def generate_blended_drawing(reply):
    try:
        # 1. 提取名字
        ext = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "提取人名"}, {"role": "user", "content": reply}]
        )
        name = ext.choices[0].message.content.strip()
        
        # 2. 生成简笔画 (核心：强制纯白背景以融合 UI)
        img_res = client.images.generate(
            model=IMAGE_MODEL,
            prompt=f"A minimalist black line drawing of {name}. Simple ink sketch style. Pure solid #FFFFFF white background with NO shading, NO colors, NO gradients. The drawing should blend seamlessly into a white webpage.",
            size="1024x1024"
        )
        return name, img_res.data[0].url
    except:
        return "神秘人物", None

# ==========================================
# 5. 交互渲染
# ==========================================
with st.sidebar:
    st.header("📊 战况")
    st.write(f"已提问：{st.session_state.question
