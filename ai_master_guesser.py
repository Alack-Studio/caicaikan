import streamlit as st
from openai import OpenAI
import random

# 1. 赛博深夜 UI：呼吸灯与精致布局
st.set_page_config(page_title="赛博侦探事务所", layout="centered")

# 初始化状态
states = {"msgs":[], "role":"AI 猜", "over":False, "model":"gemini-2.5-flash-lite", "count":0, "pending":None}
for k, v in states.items():
    if k not in st.session_state: st.session_state[k] = v

with st.sidebar:
    if st.button("🔄 重置所有进度", use_container_width=True):
        for k in ["msgs", "over", "count", "pending"]: st.session_state[k] = [] if k=="msgs" else (0 if k=="count" else (None if k=="pending" else False))
        st.rerun()

# 锁定深夜色调与赛博蓝光变量
bg, txt, glow_c, c_bg = "#121212", "#D1D1D1", "0, 210, 255", "rgba(255,255,255,0.03)"

st.markdown(f"""
    <style>
    @keyframes breathe {{
        0% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
        50% {{ box-shadow: 0 0 12px rgba({glow_c}, 0.45); border-color: rgba({glow_c}, 0.6); }}
        100% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
    }}
    .stApp {{ background-color: {bg}; color: {txt} !important; font-family: -apple-system, sans-serif; }}
    .stApp p, .stApp h1, .stApp h3, .stApp label {{ color: {txt} !important; }}
    
    /* 对话气泡：极细呼吸感 */
    .stChatMessage {{ 
        background-color: {c_bg} !important; border-radius: 12px; padding: 10px; 
        border: 0.6px solid rgba({glow_c}, 0.4); animation: breathe 3.5s infinite ease-in-out; margin-bottom: 10px; 
    }}
    .stChatMessage p {{ font-size: 1.05rem !important; line-height: 1.6; color: {txt} !important; }}
    
    /* 快捷气泡：左对齐 pill 样式 */
    div.stButton > button {{
        border-radius: 20px; height: 2.1em; font-size: 0.85rem !important;
        padding: 0 12px; background-color: transparent; 
        color: {txt} !important; border: 0.8px solid rgba({glow_c}, 0.4);
        animation: breathe 3s infinite ease-in-out; transition: 0.3s all;
    }}
    div.stButton > button:hover {{ animation: none; border-color: #00D2FF; color: #00D2FF !important; box-shadow: 0 0 15px rgba({glow_c}, 0.6); }}
    
    /* 结算勋章布局 */
    .rank-badge {{
        text-align: center; padding: 15px; border-radius: 15px;
        border: 1px solid #00D2FF; background: rgba(0, 210, 255, 0.05);
        box-shadow: 0 0 20px rgba(0, 210, 255, 0.2); margin: 20px 0; animation: breathe 2s infinite ease-in-out;
    }}
    header {{visibility: hidden;}}
    .stSpinner p {{ font-size: 0.9rem !important; color: #00D2FF; opacity: 0.8; font-style: italic; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ 赛博侦探事务所")

# 2. 核心逻辑与 API
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def get_rank_info(n):
    if n < 10: return "🏆 读心之神", "你的思维几乎已经和数字核心完美同步，真相在你面前毫无秘密。"
    if n <= 15: return "🕵️ 名侦探", "逻辑缜密，难逃法眼。事务所需要你这样的精英。"
    if n <= 20: return "👮 初级警员", "表现尚可，但你的推理似乎在某些环节出现了跳跃。"
    return "🤡 围观群众", "真相就在眼前，你却在迷雾中优雅地漫步。下次带上放大镜吧。"

def ask_ai(inp=None):
    if inp: 
        st.session_state.msgs.append({"role": "user", "content": inp})
        st.session_state.count += 1
    
    waits = ["正在同步脑电波...", "正在检索档案...", "正在锁定频率..."]
    with st.spinner(random.choice(waits)):
        if st.session_state.role == "AI 猜":
            sys = "你猜。严禁前5轮问性别国籍。猜中后以'答案是：[人名]'开头。"
        else:
            sys = ("我猜。你选定一个世界著名人物。仅答'是/否/模糊'并附带简短提示。"
                   "如果是开局的第一条消息，请以冷酷且神秘的侦探身份做开局宣言，并给出一个极模糊的身份提示。")
            
        try:
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.8)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            if any(x in reply for x in ["答案是", "获胜", "恭喜", "真相是"]):
                st.session_state.over = True
        except Exception as e: st.error(f"📡 API 异常: {str(e)}")

if st.session_state.pending:
    ans = st.session_state.pending
    st.session_state.pending = None
    ask_ai(ans); st.rerun()

# 3. 游戏渲染
if not st.session_state.msgs:
    st.session_state.role = st.radio("🎭 模式选择", ["AI 猜 (它问我答)", "我猜 (我问它答)"], horizontal=True)
    st.session_state.model = st.radio("🔮 挑战对象", ["gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3-pro-preview"], captions=["快速响应", "逻辑深度", "终极智商"])
    if st.button("🚀 开启侦探模式", use_container_width=True, type="primary"):
        ask_ai(); st.rerun()
else:
    for m in st.session_state.msgs:
        with st.chat_message(m["role"], avatar="🕵️" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    if not st.session_state.over:
        st.write("") 
        if st.session_state.role == "AI 猜":
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ 是", use_container_width=True): st.session_state.pending = "是的"; st.rerun()
            if c2.button("❌ 否", use_container_width=True): st.session_state.pending = "不是"; st.rerun()
            if c3.button("❔ 模糊", use_container_width=True): st.session_state.pending = "不确定"; st.rerun()
        else:
            # 快捷气泡左对齐实现
            qc1, qc2, qc3, qc4 = st.columns([0.18, 0.22, 0.22, 0.38])
            with qc1: 
                if st.button("💡 提示"): st.session_state.pending = "请多给点提示。"; st.rerun()
            with qc2: 
                if st.button("🙅 猜不到"): st.session_state.pending = "我想不出来了，请揭晓答案。"; st.rerun()
            with qc3: 
                if st.button("🔄 换个人"): 
                    st.session_state.msgs, st.session_state.count = [], 0
                    ask_ai(); st.rerun()
            
            q = st.chat_input("向侦探提问...")
            if q: ask_ai(q); st.rerun()
    else:
        st.balloons()
        # 展示勋章与评价
        rank_t, rank_d = get_rank_info(st.session_state.count)
        st.markdown(f"""
            <div class="rank-badge">
                <h2 style="color:#00D2FF; margin:0;">{rank_t}</h2>
                <p style="margin:10px 0 0 0; opacity:0.8;">{rank_d}</p>
                <small style="opacity:0.5;">提问次数: {st.session_state.count} | 模型: {st.session_state.model}</small>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🎮 再玩一局", use_container_width=True, type="primary"):
            st.session_state.msgs, st.session_state.over, st.session_state.count = [], False, 0
            st.rerun()
