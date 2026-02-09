import streamlit as st
from openai import OpenAI

# 1. 界面配置 (精致深色侦探风)
st.set_page_config(page_title="Gemini 3 画影神探", page_icon="🕵️", layout="centered")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at center, #1a1c2c 0%, #0d0e17 100%); color: #ffffff; }
    div.stButton > button {
        border-radius: 12px; height: 3.5em;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white; border: none; font-weight: bold;
    }
    .stChatMessage { border-radius: 15px; background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); }
    </style>
    """, unsafe_allow_html=True)

# 2. 状态初始化
init_keys = ["messages", "game_over", "question_count", "final_image_url", "final_char_name"]
for key in init_keys:
    if key not in st.session_state:
        st.session_state[key] = [] if "messages" in key else (None if "url" in key or "name" in key else 0 if "count" in key else False)

# 3. API 配置
API_KEY = st.secrets.get("API_KEY", "")
if not API_KEY:
    st.error("🔑 请配置 API_KEY"); st.stop()

client = OpenAI(api_key=API_KEY, base_url="https://api.gptsapi.net/v1")
CHAT_MODEL = "gemini-3-flash-preview"
IMAGE_MODEL = "dall-e-3"

# 4. 核心逻辑
def get_ai_response(user_input=None):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
    sys_p = "你是一个顶级读心神算子。我心里想一个著名人物，你只能问是非题。确定后用'答案是：[人名]'开头。"
    try:
        res = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": sys_p}] + st.session_state.messages,
            temperature=0.8
        )
        reply = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        if st.session_state.question_count > 0:
            if "?" not in reply and "？" not in reply or "答案是" in reply:
                st.session_state.game_over = True
    except Exception as e:
        st.error(f"🔮 波动: {e}")

def process_result(reply):
    try:
        ext = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": "只提取人名"}, {"role": "user", "content": reply}])
        name = ext.choices[0].message.content.strip()
        img = client.images.generate(
            model=IMAGE_MODEL,
            prompt=f"Minimalist black line drawing avatar of {name}, white background, ink sketch style, no color.",
            size="1024x1024"
        )
        return name, img.data[0].url
    except:
        return "神秘人物", None

# 5. UI 渲染
st.title("🕵️ Gemini 3：画影神探")

with st.sidebar:
    st.write(f"步数：{st.session_state.question_count}")
    if st.button("🔄 重开", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if not st.session_state.messages:
    with st.spinner("🔮 同步中..."): get_ai_response()

if not st.session_state.game_over:
    last_msg = st.session_state.messages[-1]["content"] if st.session_state.messages else ""
    st.chat_message("assistant", avatar="🔮").write(f"#### {last_msg}")
    def on_click(ans):
        st.session_state.question_count += 1
        get_ai_response(ans)
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", on_click=on_click, args=("是的",), use_container_width=True, type="primary")
    with c2: st.button("❌ 不是", on_click=on_click, args=("不是",), use_container_width=True)
    with c3: st.button("❔ 不确定", on_click=on_click, args=("不确定",), use_container_width=True)
else:
    st.balloons(); final_reply = st.session_state.messages[-1]["content"]
    st.chat_message("assistant", avatar="🎯").write(f"### {final_reply}")
    if st.session_state.final_image_url is None:
        with st.spinner("🎨 绘图中..."):
            n, u = process_result(final_reply)
            st.session_state.final_char_name, st.session_state.final_image_url = n, u
            st.rerun()
    if st.session_state.final_image_url:
        st.divider()
        st.image(st.session_state.final_image_url, caption=f"🖌️ AI速写：{st.session_state.final_char_name}", width=400)
    if st.button("🎮 再来一局", use_container_width=True, type="primary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
