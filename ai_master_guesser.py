import streamlit as st
from openai import OpenAI

# 1. 手机端适配：纯白简约 UI
st.set_page_config(page_title="AI 猜猜看", layout="centered")
st.markdown("<style>.stApp{background-color:#FFFFFF;} div.stButton>button{border-radius:12px;height:4.5em;font-weight:bold;border:1px solid #E0E0E0;background-color:#FFFFFF;color:#31333F;width:100%;margin-bottom:12px;}</style>", unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 状态初始化 (防止变量丢失)
ks = ["msgs", "over", "count"]
for k in ks:
    if k not in st.session_state: 
        st.session_state[k] = [] if k=="msgs" else (0 if k=="count" else False)

# 3. API 配置 (WildCard)
if "API_KEY" not in st.secrets:
    st.error("🔑 请配置 API_KEY"); st.stop()

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")
MODEL = "gpt-4o"

# 4. 核心逻辑 (GPT-4o 高智商注入)
def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    sys = "你是一个顶级读心者。我心里想一个著名人物，你通过是非题来猜。严禁在前5轮询问性别、国籍或是否健在。一次一问且带问号。确定后以'答案是：[人名]'开头。"
    try:
        res = client.chat.completions.create(
            model=MODEL, 
            messages=[{"role":"system","content":sys}] + st.session_state.msgs, 
            temperature=0.8
        )
        reply = res.choices[0].message.content
        st.session_state.msgs.append({"role": "assistant", "content": reply})
        # 判定结束逻辑
        if st.session_state.count > 0 and ("?" not in reply and "？" not in reply or "答案是" in reply):
            st.session_state.over = True
    except: st.error("🔮 信号波动，请点击重试")

# 5. UI 渲染逻辑
if not st.session_state.msgs:
    st.write("---")
    st.write("想好一个人物（现实或虚构），让 GPT-4o 挑战你的大脑。")
    if st.button("🚀 开始游戏", use_container_width=True, type="primary"):
        ask_ai(); st.rerun()

elif not st.session_state.over:
    st.chat_message("assistant", avatar="🕵️").write(f"### {st.session_state.msgs[-1]['content']}")
    def btn_click(a):
        st.session_state.count += 1
        ask_ai(a)
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是", on_click=btn_click, args=("是的",), use_container_width=True, type="primary")
    with c2: st.button("❌ 否", on_click=btn_click, args=("不是",), use_container_width=True)
    with c3: st.button("❔ 模糊", on_click=btn_click, args=("不确定",), use_container_width=True)
    if st.button("🔄 重新开始", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

else:
    st.balloons()
    st.chat_message("assistant", avatar="🎯").write(f"### {st.session_state.msgs[-1]['content']}")
    if st.button("🎮 再玩一局", use_container_width=True, type="primary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
