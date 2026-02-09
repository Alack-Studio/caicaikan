import streamlit as st
from openai import OpenAI
import random

# 1. 极致赛博 UI：呼吸灯效果与强反馈布局
st.set_page_config(page_title="赛博侦探", layout="centered")
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

# 状态初始化
states = {"msgs":[], "role":"AI 猜", "over":False, "win":False, "model":"gemini-2.5-flash-lite", "count":0, "pending":None}
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
    
    /* 选关按钮高亮 */
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
        animation: breathe 4s infinite ease-in-out;
    }}
    header {{visibility: hidden;}}
    .stSpinner p {{ font-size: 0.9rem; color: #00D2FF; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 核心逻辑：强化胜利判定
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None, is_start_trigger=False):
    if inp:
        st.session_state.msgs.append({"role": "user", "content": inp})
        if not is_start_trigger: st.session_state.count += 1
    
    with st.spinner("信号传输中..."):
        if st.session_state.role == "AI 猜":
            sys = "你是一个猜谜助手。我心里想一个人物，你通过是非题来猜。请直接开始第一个问题，不要说任何废话。"
        else:
            # 强化 AI 的结算意识：当用户猜中时，必须触发特定词汇
            sys = ("你已选定一个著名人物。收到第一个提示请求时直接给出分类提示。"
                   "随后答'是/否/模糊'。如果用户猜中了该人物的名字，你必须回复'恭喜你，答对了！'并公布答案。"
                   "若用户点击提示，提供性别、形象、粉丝群体等特征。")
            
        try:
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.7)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            
            # 强化判定矩阵
            win_keywords = ["恭喜", "答对了", "正确", "没错", "答案是", "真相是", "揭晓答案"]
            if any(x in reply for x in win_keywords):
                st.session_state.over = True
                # 在“我猜”模式下，且非认输情况下，判定为真正胜利
                if st.session_state.role == "我猜" and "揭晓答案" not in inp:
                    st.session_state.win = True
                elif st.session_state.role == "AI 猜":
                    st.session_state.win = True # AI 猜中也视为完成
        except Exception as e: st.error(f"📡 API 异常: {str(e)}")

if st.session_state.pending:
    ans = st.session_state.pending
    st.session_state.pending = None
    ask_ai(ans); st.rerun()

# 3. 界面渲染
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
    st.markdown("### 🔮 选择 Gemini 模型")
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
        if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", is_start_trigger=True)
        else: ask_ai()
        st.rerun()

else:
    # 如果已结束，且是胜利，顶部显示勋章
    if st.session_state.over and st.session_state.win:
        st.success("🏆 恭喜破案！推理成功")

    for m in st.session_state.msgs:
        if m["content"] == "请直接给我第一个提示。": continue
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
                if st.button("💡 提示"): st.session_state.pending = "提示一下，比如性别、形象或者特点？"; st.rerun()
            with qc2: 
                if st.button("🙅 猜不到"): st.session_state.pending = "我想不出来了，请直接揭晓答案。"; st.rerun()
            with qc3: 
                if st.button("🔄 换个人"): 
                    st.session_state.msgs, st.session_state.over, st.session_state.win, st.session_state.count = [], False, False, 0
                    if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", is_start_trigger=True)
                    else: ask_ai()
                    st.rerun()
            q = st.chat_input("输入你的推理提问...")
            if q: ask_ai(q); st.rerun()
    else:
        # 胜利气球 vs 失败雪花
        if st.session_state.win: st.balloons()
        else: st.snow()
        
        st.markdown(f'<div style="text-align:center; padding:15px; border-radius:12px; border:1px solid #00D2FF; background:rgba(0,210,255,0.03); margin:20px 0;"><h3>{"🎯 推理成功" if st.session_state.win else "❄️ 遗憾结束"}</h3><p>本次推理共消耗: {st.session_state.count} 轮</p></div>', unsafe_allow_html=True)
        
        if st.button("🎮 换个人重新猜", use_container_width=True, type="primary"):
            st.session_state.msgs, st.session_state.over, st.session_state.win, st.session_state.count = [], False, False, 0
            if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", is_start_trigger=True)
            else: ask_ai()
            st.rerun()
