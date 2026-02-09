import streamlit as st
from openai import OpenAI
import random

# 1. 赛博选关 UI：去除侧边栏，重构布局
st.set_page_config(page_title="赛博侦探", layout="centered")

# 强制隐藏侧边栏
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

# 初始化状态
states = {"msgs":[], "role":"AI 猜", "over":False, "model":"gemini-2.5-flash-lite", "count":0, "pending":None}
for k, v in states.items():
    if k not in st.session_state: st.session_state[k] = v

# 锁定色调与呼吸灯动画
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
    
    /* 选关卡片样式 */
    div[data-testid="stExpander"] {{
        background-color: {c_bg} !important; border: 0.8px solid rgba({glow_c}, 0.3);
        border-radius: 12px; animation: breathe 4s infinite;
    }}
    
    /* 聊天气泡 */
    .stChatMessage {{ 
        background-color: {c_bg} !important; border-radius: 10px; padding: 10px; 
        border: 0.6px solid rgba({glow_c}, 0.3); animation: breathe 4s infinite ease-in-out; margin-bottom: 8px; 
    }}
    .stChatMessage p {{ font-size: 1.05rem !important; line-height: 1.6; color: {txt} !important; }}
    
    /* 快捷气泡左对齐 */
    div.stButton > button {{
        border-radius: 20px; height: 2.1em; font-size: 0.85rem !important;
        padding: 0 12px; background-color: transparent; 
        color: {txt} !important; border: 0.8px solid rgba({glow_c}, 0.3);
        transition: 0.3s all;
    }}
    div.stButton > button:hover {{ border-color: #00D2FF; color: #00D2FF !important; box-shadow: 0 0 10px rgba({glow_c}, 0.4); }}
    
    /* 结算展示 */
    .rank-badge {{
        text-align: center; padding: 15px; border-radius: 12px;
        border: 1px solid #00D2FF; background: rgba(0, 210, 255, 0.03); margin: 20px 0;
    }}
    header {{visibility: hidden;}}
    .stSpinner p {{ font-size: 0.9rem !important; color: #00D2FF; opacity: 0.7; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ 赛博侦探")

# 2. 核心逻辑
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None):
    if inp: 
        st.session_state.msgs.append({"role": "user", "content": inp})
        st.session_state.count += 1
    with st.spinner("数据检索中..."):
        if st.session_state.role == "AI 猜":
            sys = "你猜。严禁前5轮问性别国籍。确定后以'答案是：[人名]'开头。"
        else:
            sys = ("你已选定一个世界著名人物。仅答'是/否/模糊'并附带简短提示。严禁人设描述。第一条消息请直接给出欢迎语和极其模糊的分类提示。")
        try:
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.7)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            if any(x in reply for x in ["答案是", "获胜", "恭喜", "真相是"]): st.session_state.over = True
        except Exception as e: st.error(f"📡 API 异常: {str(e)}")

if st.session_state.pending:
    ans = st.session_state.pending
    st.session_state.pending = None
    ask_ai(ans); st.rerun()

# 3. 游戏流程：重构选关画面
if not st.session_state.msgs:
    st.write("---")
    st.markdown("### 💠 选择你的任务阶段")
    # 模式选择
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        if st.button("🎭 AI 猜 (读心模式)", use_container_width=True, type="primary" if st.session_state.role=="AI 猜" else "secondary"):
            st.session_state.role = "AI 猜"; st.rerun()
    with m_col2:
        if st.button("🔍 我猜 (档案模式)", use_container_width=True, type="primary" if st.session_state.role=="我猜" else "secondary"):
            st.session_state.role = "我猜"; st.rerun()
            
    st.write("")
    st.markdown("### 📡 接入 AI 终端")
    # 模型选择
    mod1, mod2, mod3 = st.columns(3)
    models = ["gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3-pro-preview"]
    for i, col in enumerate([mod1, mod2, mod3]):
        with col:
            is_sel = st.session_state.model == models[i]
            if st.button(models[i].replace("gemini-",""), use_container_width=True, type="primary" if is_sel else "secondary"):
                st.session_state.model = models[i]; st.rerun()
    
    st.write("---")
    if st.button("🚀 初始化游戏终端", use_container_width=True):
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
            # 快捷功能左对齐
            qc1, qc2, qc3, qc4 = st.columns([0.18, 0.22, 0.22, 0.38])
            with qc1: 
                if st.button("💡 提示"): st.session_state.pending = "请多给点提示。"; st.rerun()
            with qc2: 
                if st.button("🙅 猜不到"): st.session_state.pending = "我想不出来了，请揭晓答案。"; st.rerun()
            with qc3: 
                if st.button("🔄 重置"): 
                    st.session_state.msgs, st.session_state.count = [], 0
                    st.rerun()
            q = st.chat_input("输入你的问题...")
            if q: ask_ai(q); st.rerun()
    else:
        st.balloons()
        st.markdown(f'<div class="rank-badge"><h3>🎯 逻辑同步完成</h3><p>提问次数: {st.session_state.count}</p></div>', unsafe_allow_html=True)
        if st.button("🎮 开启新一轮终端链接", use_container_width=True, type="primary"):
            st.session_state.msgs, st.session_state.over, st.session_state.count = [], False, 0
            st.rerun()
