import streamlit as st
from openai import OpenAI

# 1. 手机端适配：纯白背景与大按钮
st.set_page_config(page_title="AI 猜猜看", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1F1F1F; }
    div.stButton > button {
        border-radius: 12px; height: 4.2em; font-size: 1.1em;
        font-weight: bold; border: 1px solid #E0E0E0;
        background-color: #FFFFFF; color: #31333F; width: 100%;
        margin-bottom: 8px;
    }
    .stChatMessage { background-color: #F8F9FA; border-radius: 12px; }
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 状态初始化
ks = ["msgs", "over", "count", "img", "name"]
for k in ks:
    if k not in st.session_state: 
        st.session_state[k] = [] if k=="msgs" else (None if k in ["img", "name"] else 0 if k=="count" else False)

# 3. API 配置
if "API_KEY" not in st.secrets:
    st.error("🔑 请配置 API_KEY"); st.stop()

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")
M_CHAT, M_IMG = "gemini-3-flash-preview", "dall-e-3"

# 4. 核心逻辑
def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    sys = "你是一个顶级读心者。我心里想一个人物，你问是非题。一次一问且带问号。确定后以'答案是：[人名]'开头。"
    try:
        res = client.chat.completions.create(model=M_CHAT, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.8)
        reply = res.choices[0].message.content
        st.session_state.msgs.append({"role": "assistant", "content": reply})
        if st.session_state.count > 0 and ("?" not in reply and "？" not in reply or "答案是" in reply):
            st.session_state.over = True
    except: st.error("🔮 信号波动，请刷新")

def draw_img(reply):
    try:
        ext = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":"提取人名及标志性视觉特征(如Cheems需包含瘫坐、委屈表情)"},{"role":"user","content":reply}])
        desc = ext.choices[0].message.content.strip()
        p = f"A minimalist black line drawing of {desc}. Simple ink sketch style. Pure white background #FFFFFF, no shading. Seamlessly blend into white page."
        img = client.images.generate(model=M_IMG, prompt=p, size="1024x1024")
        return desc.split()[0], img.data[0].url
    except: return "神秘人物", None

# 5. UI 渲染
if not st.session_state.msgs:
    if st.button("🚀 开始游戏", use_container_width=True, type="primary"):
        ask_ai()
        st.rerun()
elif not st.session_state.over:
    st.chat_message("assistant", avatar="🕵️").write(f"### {st.session_state.msgs[-1]['content']}")
    def btn_click(a):
        st.session_state.count += 1
        ask_ai(a)
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", on_click=btn_click, args=("是的",), use_container_width=True, type="primary")
    with c2: st.button("❌ 不是", on_click=btn_click, args=("不是",), use_container_width=True)
    with c3: st.button("❔ 不确定", on_click=btn_click, args=("不确定",), use_container_width=True)
    if st.button("🔄 重新开始", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
else:
    st.balloons()
    st.chat_message("assistant", avatar="🎯").write(f"### {st.session_state.msgs[-1]['content']}")
    if st.session_state.img is None:
        with st.spinner("🖌️ 正在临摹..."):
            n, u = draw_img(st.session_state.msgs[-1]['content'])
            st.session_state.name, st.session_state.img = n, u
            st.rerun()
    if st.session_state.img:
        st.image(st.session_state.img, caption=f"🖌️ AI速写: {st.session_state.name}", use_container_width=True)
    if st.button("🎮 再玩一局", use_container_width=True, type="primary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
