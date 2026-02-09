import streamlit as st
from openai import OpenAI
import random

# 1. 赛博选关 UI：高亮锁定与极致精致感
st.set_page_config(page_title="赛博侦探", layout="centered")

# 强制隐藏侧边栏
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

# 状态初始化
states = {"msgs":[], "role":"AI 猜", "over":False, "model":"gemini-2.5-flash-lite", "count":0, "pending":None}
for k, v in states.items():
    if k not in st.session_state: st.session_state[k] = v

# 锁定赛博深夜色彩方案
bg, txt, glow_c = "#121212", "#D1D1D1", "0, 210, 255"

st.markdown(f"""
    <style>
    @keyframes breathe {{
        0% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
        50% {{ box-shadow: 0 0 12px rgba({glow_c}, 0.45); border-color: rgba({glow_c}, 0.5); }}
        100% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
    }}
    .stApp {{ background-color: {bg}; color: {txt} !important; font-family: -apple-system, sans-serif; }}
    
    /* 选关按钮高亮逻辑 */
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

    .model-desc {{ 
        font-size: 0.8rem; color: {txt}; opacity: 0.6; 
        text-align: center; margin-top: -10px; margin-bottom: 15px; line-height: 1.3;
    }}

    .stChatMessage {{ 
        background-color: rgba(255,255,255,0.03) !important; border-radius: 10px; 
        padding: 10px; border: 0.6px solid rgba({glow_c}, 0.3); margin-bottom: 8px; 
    }}
    header {{visibility: hidden;}}
    .stSpinner p {{ font-size: 0.9rem; color: #00D2FF; font-style: italic; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ 赛博侦探")

# 2. 核心逻辑
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None):
    if inp: 
        st.session_state.msgs.append({"role": "user", "content": inp})
        st.session_state.count += 1
    with st.spinner("正在启动推理引擎..."):
        if st.session_state.role == "AI 猜":
            sys = "你是一个猜谜助手。我心里想一个人物，你通过是非题来猜。严禁前5轮询问性别或国籍。确定后以'答案是：[人名]'开头。"
        else:
            sys = "你已选定一个名人。用户问是非题，你仅答'是/否/模糊'并附带简短提示。严禁人设描述。第一条消息直接给出分类提示。认输即揭晓。"
        try:
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.7)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            if any(x in reply for x in ["答案是", "获胜", "真相是", "揭晓"]): st.session_state.over = True
        except Exception as e: st.error(f"📡 终端异常: {str(e)}")

if st.session_state.pending:
    ans = st.session_state.pending
    st.session_state.pending = None
    ask_ai(ans); st.rerun()

# 3. 选关画面渲染
if not st.session_state.msgs:
    st.write("---")
    st.markdown("### 🎭 任务模式")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        if st.button("AI 猜 (读心模式)", use_container_width=True, type="primary" if st.session_state.role=="AI 猜" else "secondary"):
            st.session_state.role = "AI 猜"; st.rerun()
    with m_col2:
        if st.button("我猜 (档案模式)", use_container_width=True, type="primary" if st.session_state.role=="我猜" else "secondary"):
            st.session_state.role = "我猜"; st.rerun()
            
    st.write("")
    st.markdown("### 📡 接入逻辑核心")
    descs = {
        "gemini-2.5-flash-lite": "⚡ 极速响应<br>适合连续快速对弈",
        "gemini-2.5-pro": "🧠 逻辑专家<br>擅长解构复杂线索",
        "gemini-3-pro-preview": "🔥 究极核心<br>顶级推演直觉"
    }
    models, mod_cols = list(descs.keys()), st.columns(3)
    
    for i, col in enumerate(mod_cols):
        m_id = models[i]
        with col:
            is_sel = st.session_state.model == m_id
            if st.button(m_id.replace("gemini-",""), use_container_width=True, type="primary" if is_sel else "secondary"):
                st.session_state.model = m_id; st.rerun()
            st.markdown(f'<p class="model-desc">{descs[m_id]}</p>', unsafe_allow_html=True)
    
    st.write("---")
    # 文案修改：⚡ 开始推理
    if st.button("⚡ 开始推理", use_container_width=True, type="primary"):
        ask_ai(); st.rerun()

else:
    for m in st.session_state.msgs:
        with st.chat_message(m["role"], avatar="🕵️" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    if not st.session_state.over:
        if st.session_state.role == "AI 猜":
            st.divider()
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ 是", use_container_width=True): st.session_state.pending = "是的"; st.rerun()
            if c2.button("❌ 否", use_container_width=True): st.session_state.pending = "不是"; st.rerun()
            if c3.button("❔ 模糊", use_container_width=True): st.session_state.pending = "不确定"; st.rerun()
        else:
            qc1, qc2, qc3, qc4 = st.columns([0.18, 0.22, 0.22, 0.38])
            with qc1: 
                if st.button("💡 提示"): st.session_state.pending = "请多给点提示。"; st.rerun()
            with qc2: 
                if st.button("🙅 猜不到"): st.session_state.pending = "我想不出来了，请直接揭晓答案。"; st.rerun()
            with qc3: 
                if st.button("🔄 重置"): 
                    st.session_state.msgs, st.session_state.count = [], 0
                    st.rerun()
            q = st.chat_input("输入推理提问...")
            if q: ask_ai(q); st.rerun()
    else:
        st.balloons()
        st.markdown(f'<div style="text-align:center; padding:15px; border-radius:12px; border:1px solid #00D2FF; background:rgba(0,210,255,0.03); margin:20px 0;"><h3>🎯 逻辑同步完成</h3><p>提问消耗: {st.session_state.count} 轮</p></div>', unsafe_allow_html=True)
        if st.button("🎮 重置神经回路", use_container_width=True, type="primary"):
            st.session_state.msgs, st.session_state.over, st.session_state.count = [], False, 0
            st.rerun()
