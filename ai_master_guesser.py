import streamlit as st
from openai import OpenAI

# 1. 移动端优化：纯白简约 UI
st.set_page_config(page_title="AI 猜猜看", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1F1F1F; }
    div.stButton > button {
        border-radius: 12px; height: 4.8em; font-size: 1.1em;
        font-weight: bold; border: 1px solid #E0E0E0;
        background-color: #FFFFFF; color: #31333F; width: 100%;
        margin-bottom: 12px; transition: 0.2s;
    }
    div.stButton > button:active { transform: scale(0.96); background-color: #F8F9FA; }
    .stChatMessage { background-color: #FFFFFF; border: none; padding: 0px; }
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 状态初始化
ks = ["msgs", "over", "count"]
for k in ks:
    if k not in st.session_state: 
        st.session_state[k] = [] if k=="msgs" else (0 if k=="count" else False)

# 3. API 配置 (WildCard)
if "API_KEY" not in st.secrets:
    st.error("🔑 请配置 API_KEY"); st.stop()

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")
# 使用更快速的旗舰级小模型
MODEL = "gpt-4o-mini"

# 4. 核心逻辑
def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    sys = "你是一个读心专家。我心里想一个人物，你问是非题。一次一问带问号。确定答案后以'答案是：[人名]'开头。"
    try:
        res = client.chat.completions.create(
            model=MODEL, 
            messages=[{"role":"system","content":sys}] + st.session_state.msgs, 
            temperature=0.7
        )
        reply = res.choices[0].message.content
        st.session_state.msgs.append({"role": "assistant", "content": reply})
        # 判定结束：有关键词或完全没问号
        if st.session_state.count > 0 and ("?" not in reply and "？" not in reply or "答案是" in reply):
            st.session_state.over = True
    except: 
        st.error("🔮 信号微弱，请点击按钮重试")

# 5. UI 流程渲染
# --- 首页：开始按钮 ---
if not st.session_state.msgs:
    st.write("---")
    st.write("心里想好一个著名人物（古今中外、虚构现实均可），让 AI 来猜透你的心思。")
    if st.button("🚀 开始游戏", use_container_width=True, type="primary"):
        ask_ai()
        st.rerun()

# --- 过程中：提问与回答 ---
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

# --- 结局：揭晓答案 ---
else:
    st.balloons()
    st.chat_message("assistant", avatar="🎯").write(f"### {st.session_state.msgs[-1]['content']}")
    st.success("🎯 看来 AI 已经锁定了真相！")
    
    if st.button("🎮 再玩一局", use_container_width=True, type="primary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
