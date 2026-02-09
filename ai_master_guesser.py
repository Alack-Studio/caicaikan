import streamlit as st
from openai import OpenAI
import random

# 1. 极致赛博 UI：呼吸灯效果与选关布局
st.set_page_config(page_title="赛博侦探", layout="centered")
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

# 状态初始化
states = {"msgs":[], "role":"AI 猜", "over":False, "model":"gemini-2.5-flash-lite", "count":0, "pending":None}
for k, v in states.items():
    if k not in st.session_state: st.session_state[k] = v

bg, txt, glow_c = "#121212", "#D1D1D1", "0, 210, 255"

st.markdown(f"""
    <style>
    @keyframes breathe {{
        0% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
        50% {{ box-shadow: 0 0 10px rgba({glow_c}, 0.4); border-color: rgba({glow_c}, 0.5); }}
        100% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
    }}
    .stApp {{ background-color: {bg}; color: {txt} !important; font-family: -apple-system, sans-serif; }}
    div.stButton > button {{
        border-radius: 12px; height: 3.2em; font-size: 0.95rem !important;
        background-color: transparent; color: {txt} !important;
        border: 1px solid rgba({glow_c}, 0.2); transition: 0.3s all;
    }}
    div.stButton > button[kind="primary"] {{
        background-color: rgba({glow_c}, 0.1) !important;
        border: 2px solid #00D2FF !important;
        box-shadow: 0 0 15px rgba({glow_c}, 0.5) !important;
        animation: breathe 2s infinite ease-in-out;
        color: #00D2FF !important; font-weight: bold;
    }}
    .model-desc {{ font-size: 0.8rem; color: {txt}; opacity: 0.6; text-align: center; margin-top: -10px; margin-bottom: 15px; }}
    .stChatMessage {{ 
        background-color: rgba(255,255,255,0.03) !important; border-radius: 10px; 
        padding: 10px; border: 0.6px solid rgba({glow_c}, 0.3); margin-bottom: 8px; 
    }}
    header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 核心逻辑重组
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None):
    if inp: 
        st.session_state.msgs.append({"role": "user", "content": inp})
        st.session_state.count += 1
    with st.spinner("数据传输中..."):
        if st.session_state.role == "AI 猜":
            # 移除性别国籍限制，要求直接提问
            sys = "你是一个猜谜助手。我心里想一个著名人物，你通过是非题来猜。请直接开始第一个问题，不要说废话。"
        else:
            # 强化开局提示风格
            sys = ("你已选定一个著名人物。如果是第一条消息，请直接给出一个极其模糊但相关的身份类别提示，"
                   "例如：'提示你一下，这个人是虚拟的' 或 '这个人是个政治家' 等。"
                   "用户提问后，你答'是/否/模糊'。如果用户点击提示，请提供关于性别、形象、粉丝群体等具体特征。")
            
        try:
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.7)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            if any(x in reply for x in ["答案是", "揭晓", "真相是"]): st.session_state.over = True
        except Exception as e: st.error(f"📡 API 异常: {str(e)}")

if st.session_state.pending:
    ans = st.session_state.pending
    st.session_state.pending = None
    ask_ai(ans); st.rerun()

# 3. 选关画面：文案简化
if not st.session_state.msgs:
    st.write("---")
    st.markdown("### 🎭 模式选择")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        if st.button("AI 猜 (它问我答)", use_container_width=True, type="primary" if st.session_state.role=="AI 猜" else "secondary"):
            st.session_state.role = "AI 猜"; st.rerun()
    with m_col2:
        if st.button("我猜 (我问它答)", use_container_width=True, type="primary" if st.session_state.role=="我猜" else "secondary"):
            st.session_state.role = "我猜"; st.rerun()
            
    st.write("")
    st.markdown("### 🔮 选择 Gemini 模型") # 还原以前的标题
    descs = {"gemini-2.5-flash-lite": "⚡ 极速响应", "gemini-2.5-pro": "🧠 逻辑专家", "gemini-3-pro-preview": "🔥 究极核心"}
    models, mod_cols = list(descs.keys()), st.columns(3)
    
    for i, col in enumerate(mod_cols):
        m_id = models[i]
        with col:
            is_sel = st.session_state.model == m_id
            if st.button(m_id.replace("gemini-",""), use_container_width=True, type="primary" if is_sel else "secondary"):
                st.session_state.model = m_id; st.rerun()
            st.markdown(f'<p class="model-desc">{descs[m_id]}</p>', unsafe_allow_html=True)
    
    st.write("---")
    if st.button("🚀 开始推理", use_container_width=True, type="primary"):
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
            qc1, qc2, qc3, qc4 = st.columns([0.18, 0.22, 0.22, 0.38])
            with qc1: 
                # 点击提示时发送特定引导词
                if st.button("💡 提示"): st.session_state.pending = "提示一下，比如性别、形象或者特点？"; st.rerun()
            with qc2: 
                if st.button("🙅 猜不到"): st.session_state.pending = "揭晓答案，公布真相。"; st.rerun()
            with qc3: 
                # 换个人：重置消息但不回选关页面
                if st.button("🔄 换个人"): 
                    st.session_state.msgs, st.session_state.count = [], 0
                    ask_ai(); st.rerun()
            q = st.chat_input("输入你的推理提问...")
            if q: ask_ai(q); st.rerun()
    else:
        st.balloons()
        st.markdown(f'<div style="text-align:center; padding:15px; border-radius:12px; border:1px solid #00D2FF; background:rgba(0,210,255,0.03); margin:20px 0;"><h3>🎯 推理结束</h3><p>提问消耗: {st.session_state.count} 轮</p></div>', unsafe_allow_html=True)
        if st.button("🎮 换个人重新猜", use_container_width=True, type="primary"):
            st.session_state.msgs, st.session_state.over, st.session_state.count = [], False, 0
            # 直接开始新对局
            ask_ai(); st.rerun()
