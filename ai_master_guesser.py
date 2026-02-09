import streamlit as st
from openai import OpenAI

# 1. 页面配置与白底 CSS
st.set_page_config(page_title="AI 猜猜看", page_icon="🕵️", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1F1F1F; }
    div.stButton > button {
        border-radius: 8px; height: 3.5em; font-weight: bold;
        border: 1px solid #E0E0E0; background-color: #FFFFFF; color: #31333F;
    }
    div.stButton > button:hover { border-color: #FF4B4B; color: #FF4B4B; }
    .stChatMessage { background-color: #F8F9FA; border-radius: 12px; border: 1px solid #F0F0F0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 状态初始化
init_vals = {"messages": [], "game_over": False, "question_count": 0, "final_img": None, "char_name": ""}
for k, v in init_vals.items():
    if k not in st.session_state: st.session_state[k] = v

# 3. API 配置 (WildCard)
API_KEY = st.secrets.get("API_KEY", "")
if not API_KEY:
    st.error("🔑 请配置 API_KEY"); st.stop()

client = OpenAI(api_key=API_KEY, base_url="https://api.gptsapi.net/v1")
CHAT_MODEL = "gemini-3-flash-preview"
IMAGE_MODEL = "dall-e-3"

# 4. 逻辑函数
def get_ai_response(user_input=None):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
    sys_p = "你是一个顶级读心者。我心里想一个人物，你问是非题。一次一问且带问号。确定后以'答案是：[人名]'开头。"
    try:
        res = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": sys_p}] + st.session_state.messages,
            temperature=0.8
        )
        reply = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        if st.session_state.question_count > 0 and ("?" not in reply and "？" not in reply or "答案是" in reply):
            st.session_state.game_over = True
    except Exception as e:
        st.error(f"📡 链接超时: {e}")

def generate_img(reply):
    try:
        ext = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": "提取人名"}, {"role": "user", "content": reply}])
        name = ext.choices[0].message.content.strip()
        # 强制纯白背景和极简线条
        img_res = client.images.generate(
            model=IMAGE_MODEL,
            prompt=f"A minimalist black line drawing of {name}. Simple ink sketch style. Pure solid white background (#FFFFFF) with absolutely NO shading, NO colors, NO gradients. Seamlessly blend into a white webpage.",
            size="1024x1024"
        )
        return name, img_res.data[0].url
    except: return "神秘人物", None

# 5. UI 布局
with st.sidebar:
    st.header("📊 战况")
    st.write(f"已提问：{st.session_state.question_count} 次")
    if st.button("🔄 重开", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if not st.session_state.messages:
    with st.spinner("🔮 AI 准备中..."): get_ai_response()

if not st.session_state.game_over:
    if st.session_state.messages:
        last_reply = st.session_state.messages[-1]["content"]
        st.chat_message("assistant", avatar="🕵️").write(f"### {last_reply}")
    
    st.divider()
    def on_click(ans):
        st.session_state.question_count += 1
        get_ai_response(ans)
    
    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", on_click=on_click, args=("是的",), use_container_width=True, type="primary")
    with c2: st.button("❌ 不是", on_click=on_click, args=("不是",), use_container_width=True)
    with c3: st.button("❔ 不确定", on_click=on_click, args=("不确定",), use_container_width=True)
else:
    st.balloons(); final_reply = st.session_state.messages[-1]["content"]
    st.chat_message("assistant", avatar="🎯").write(f"### {final_reply}")
    if st.session_state.final_img is None:
        with st.spinner("🖌️ 正在临摹..."):
            n, u = generate_img(final_reply)
            st.session_state.char_name, st.session_state.final_img = n, u
            st.rerun()
    if st.session_state.final_img:
        st.
