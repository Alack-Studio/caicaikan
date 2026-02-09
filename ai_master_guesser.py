import streamlit as st
from openai import OpenAI

# 1. 页面配置：锁定纯白简约 UI
st.set_page_config(page_title="AI 猜猜看", layout="centered")
st.markdown("<style>.stApp{background-color:#FFFFFF;} div.stButton>button{border-radius:8px;height:3.5em;font-weight:bold;border:1px solid #E0E0E0;background-color:#FFFFFF;color:#31333F;}</style>", unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 状态初始化
ks = ["messages", "game_over", "count", "final_img", "char_name"]
for k in ks:
    if k not in st.session_state: st.session_state[k] = [] if k=="messages" else (None if "img" in k or "name" in k else 0 if k=="count" else False)

# 3. API 配置 (WildCard)
if "API_KEY" not in st.secrets:
    st.error("🔑 请配置 API_KEY"); st.stop()

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")
M_CHAT, M_IMG = "gemini-3-flash-preview", "dall-e-3"

# 4. 逻辑处理
def ask_ai(inp=None):
    if inp: st.session_state.messages.append({"role": "user", "content": inp})
    sys = "你是一个顶级读心者。我心里想一个人物，你问是非题。一次一问且带问号。确定后以'答案是：[人名]'开头。"
    try:
        res = client.chat.completions.create(model=M_CHAT, messages=[{"role": "system", "content": sys}] + st.session_state.messages, temperature=0.8)
        reply = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        if st.session_state.count > 0 and ("?" not in reply and "？" not in reply or "答案是" in reply):
            st.session_state.game_over = True
    except Exception as e: st.error(f"📡 链接超时: {e}")

def draw_img(reply):
    try:
        # 第一步：提取名字及【标志性视觉特征】
        ext = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role":"system","content":"提取人名并用5个词描述其最标志性的外观特征。"},{"role":"user","content":reply}]
        )
        desc = ext.choices[0].message.content.strip()
        
        # 第二步：生成高度特征化的简笔画 (增加 Pose 描述防止 generic 狗出现)
        prompt = f"A minimalist black line drawing of {desc}. Focus on the most iconic posture and facial expression. Simple ink sketch style. Pure solid white background #FFFFFF, no shading, no color. Seamlessly blend into white page."
        img = client.images.generate(model=M_IMG, prompt=prompt, size="1024x1024")
        return desc.split()[0], img.data[0].url
    except: return "神秘人物", None

# 5. UI 渲染
with st.sidebar:
    st.write(f"已提问：{st.session_state.count} 次")
    if st.button("🔄 重开", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if not st.session_state.messages:
    with st.spinner("🔮 AI 准备中..."): ask_ai()

if not st.session_state.game_over:
    if st.session_state.messages:
        st.chat_message("assistant", avatar="🕵️").write(f"### {st.session_state.messages[-1]['content']}")
    
    def btn_click(a):
        st.session_state.count += 1
        ask_ai(a)
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", on_click=btn_click, args=("是的",), use_container_width=True, type="primary")
    with c2: st.button("❌ 不是", on_click=btn_click, args=("不是",), use_container_width=True)
    with c3: st.button("❔ 不确定", on_click=btn_click, args=("不确定",), use_container_width=True)
else:
    st.balloons()
    st.chat_message("assistant", avatar="🎯").write(f"### {st.session_state.messages[-1]['content']}")
    if st.session_state.final_img is None:
        with st.spinner("🖌️ 正在捕捉灵魂画作..."):
            n, u = draw_img(st.session_state.messages[-1]['content'])
            st.session_state.char_name, st.session_state.final_img = n, u
            st.rerun()
    if st.session_state.final_img:
        st.divider()
        st.image(st.session_state.final_img, caption=f"🖌️ AI速写: {st.session_state.char_name}", width=400)
    if st.button("🎮 再来一局", use_container_width=True, type="primary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
