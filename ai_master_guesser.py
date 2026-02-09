import streamlit as st
from openai import OpenAI
import random

# 1. 赛博深夜 UI：保留精致发光，去除冗余描述
st.set_page_config(page_title="AI 猜猜看", layout="centered")

# 初始化状态
states = {"msgs":[], "role":"AI 猜", "over":False, "model":"gemini-2.5-flash-lite", "count":0, "pending":None}
for k, v in states.items():
    if k not in st.session_state: st.session_state[k] = v

with st.sidebar:
    if st.button("🔄 重置所有进度", use_container_width=True):
        for k in ["msgs", "over", "count", "pending"]: 
            st.session_state[k] = [] if k=="msgs" else (0 if k=="count" else (None if k=="pending" else False))
        st.rerun()

# 赛博蓝光变量
bg, txt, glow_c, c_bg = "#121212", "#D1D1D1", "0, 210, 255", "rgba(255,255,255,0.03)"

st.markdown(f"""
    <style>
    @keyframes breathe {{
        0% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
        50% {{ box-shadow: 0 0 10px rgba({glow_c}, 0.4); border-color: rgba({glow_c}, 0.5); }}
        100% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
    }}
    .stApp {{ background-color: {bg}; color: {txt} !important; font-family: -apple-system, sans-serif; }}
    .stApp p, .stApp h1, .stApp h3 {{ color: {txt} !important; }}
    
    /* 极简气泡 */
    .stChatMessage {{ 
        background-color: {c_bg} !important; border-radius: 10px; padding: 10px; 
        border: 0.6px solid rgba({glow_c}, 0.3); animation: breathe 4s infinite ease-in-out; margin-bottom: 8px; 
    }}
    .stChatMessage p {{ font-size: 1.05rem !important; line-height: 1.6; color: {txt} !important; }}
    
    /* 左对齐快捷气泡 */
    div.stButton > button {{
        border-radius: 20px; height: 2.1em; font-size: 0.85rem !important;
        padding: 0 12px; background-color: transparent; 
        color: {txt} !important; border: 0.8px solid rgba({glow_c}, 0.3);
        transition: 0.3s all;
    }}
    div.stButton > button:hover {{ border-color: #00D2FF; color: #00D2FF !important; }}
    
    /* 结算展示 */
    .rank-badge {{
        text-align: center; padding: 15px; border-radius: 12px;
        border: 1px solid #00D2FF; background: rgba(0, 210, 255, 0.03);
        margin: 20px 0;
    }}
    header {{visibility: hidden;}}
    .stSpinner p {{ font-size: 0.9rem !important; color: #00D2FF; opacity: 0.7; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 核心 API 与 纯净逻辑
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None):
    if inp: 
        st.session_state.msgs.append({"role": "user", "content": inp})
        st.session_state.count += 1
    
    with st.spinner("处理中..."):
        if st.session_state.role == "AI 猜":
            sys = "你是一个猜谜助手。我心里想一个著名人物，你通过是非题来猜。严禁前5轮询问性别或国籍。确定后以'答案是：[人名]'开头。"
        else:
            # “我猜”模式：纯净引导逻辑
            sys = ("你已选定一个世界著名人物。用户问是非题，你仅答'是/否/模糊'并附带简短提示。"
                   "严禁进行任何角色扮演。第一条消息请直接给出欢迎语和极其模糊的分类提示。")
            
        try:
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.7)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            if any(x in reply for x in ["答案是", "获胜", "恭喜", "揭晓答案"]):
                st.session_state.over = True
        except Exception as e: st.error(f"📡 API 异常: {str(e)}")

if st.session_state.pending:
    ans = st.session_state.pending
    st.session_state.pending = None
    ask_ai(ans); st.rerun()

# 3. 游戏渲染
if not st.session_state.msgs:
    st.session_state.role = st.radio("🎭 模式：", ["AI 猜 (它问我答)", "我猜 (我问它答)"], horizontal=True)
    st.session_state.model = st.radio("🔮 对象", ["gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3-pro-preview"], captions=["快速", "深度", "终极"])
    if st.button("🚀 开始游戏", use_container_width=True, type="primary"):
        ask_ai(); st.rerun()
else:
    for m in st.session_state.msgs:
        with st.chat_message(m["role"], avatar="🕵️" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    if not st.session_state.over:
        if st.session_state.role == "AI 猜":
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ 是", use_container_width=True): st.session_state.pending = "是的"; st.rerun()
            if c2.button("❌ 否", use_container_width=True): st.session_state.pending = "不是"; st.rerun()
            if c3.button("❔ 模糊", use_container_width=True): st.session_state.pending = "不确定"; st.rerun()
        else:
            # 快捷功能左对齐
            qc1, qc2, qc3, qc4 = st.columns([0.18, 0.22, 0.22, 0.38])
            with qc1: 
                if st.button("💡 提示"): st.session_state.pending = "请多给点提示。"; st.rerun()
            with qc2: 
                if st.button("🙅 猜不到"): st.session_state.pending = "我想不出来了，请揭晓答案。"; st.rerun()
            with qc3: 
                if st.button("🔄 换一个"): 
                    st.session_state.msgs, st.session_state.count = [], 0
                    ask_ai(); st.rerun()
            q = st.chat_input("输入你的问题...")
            if q: ask_ai(q); st.rerun()
    else:
        st.balloons()
        st.markdown(f'<div class="rank-badge"><h3>🎯 游戏结束</h3><p>总计消耗提问: {st.session_state.count} 次</p></div>', unsafe_allow_html=True)
        if st.button("🎮 再玩一局", use_container_width=True, type="primary"):
            st.session_state.msgs, st.session_state.over, st.session_state.count = [], False, 0
            st.rerun()
