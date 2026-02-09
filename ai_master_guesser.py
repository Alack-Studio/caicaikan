import streamlit as st
from openai import OpenAI
import random

# 1. 极致赛博 UI：保留呼吸灯效果
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
    .stChatMessage {{ 
        background-color: rgba(255,255,255,0.03) !important; border-radius: 10px; padding: 10px; 
        border: 0.6px solid rgba({glow_c}, 0.3); margin-bottom: 8px; animation: breathe 4s infinite ease-in-out;
    }}
    header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 核心逻辑：解决提示重复与反馈缺失
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None, is_start_trigger=False):
    if inp:
        st.session_state.msgs.append({"role": "user", "content": inp})
        if not is_start_trigger: st.session_state.count += 1
    
    with st.spinner("深度检索中..."):
        if st.session_state.role == "AI 猜":
            sys = "你是一个猜谜专家。我心里想一个著名人物，你通过是非题来猜。请直接开始第一个问题，不要说废话。"
        else:
            # 解决复读与空洞提示的核心指令
            sys = ("你已选定一个世界著名的现实或虚拟人物。用户提问你答'是/否/模糊'。"
                   "【提示规则】当收到提示请求时，必须给出具体、有实义、且不与历史重复的信息（如：性别、形象是只猫、拿过诺贝尔奖等）。"
                   "【首条规则】第一条消息请直接给出模糊分类提示，如'这个人是虚拟的'。"
                   "【胜利规则】如果用户猜对了名字，你必须回复'恭喜你，答对了！'并给出简介。")
            
        try:
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}]+st.session_state.msgs, temperature=0.8)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            
            # 判定胜利与结束
            if "恭喜" in reply or "答对了" in reply:
                st.session_state.over, st.session_state.win = True, True
            elif any(x in reply for x in ["揭晓", "真相是", "公布答案"]):
                st.session_state.over, st.session_state.win = True, False
        except Exception as e: st.error(f"📡 API 异常: {str(e)}")

if st.session_state.pending:
    ans = st.session_state.pending
    st.session_state.pending = None
    ask_ai(ans); st.rerun()

# 3. 界面渲染
if not st.session_state.msgs:
    # ... (此处保持之前的模式与模型选择界面代码一致)
    st.write("---")
    st.markdown("### 🎭 模式选择")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        if st.button("AI 猜 (它问我答)", use_container_width=True, type="primary" if st.session_state.role=="AI 猜" else "secondary"):
            st.session_state.role = "AI 猜"; st.rerun()
    with m_col2:
        if st.button("我猜 (我问它答)", use_container_width=True, type="primary" if st.session_state.role=="我猜" else "secondary"):
            st.session_state.role = "我猜"; st.rerun()
    # 模型选择
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
            st.markdown(f'<p style="font-size:0.8rem; text-align:center; opacity:0.6;">{descs[m_id]}</p>', unsafe_allow_html=True)
    
    st.write("---")
    if st.button("🚀 开始推理", use_container_width=True, type="primary"):
        if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", is_start_trigger=True)
        else: ask_ai()
        st.rerun()
else:
    # 对话流展示
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
                if st.button("💡 提示"): 
                    st.session_state.pending = f"请提供一个关于性别、形象或成就的新提示，不要重复。"; st.rerun()
            with qc2: 
                if st.button("🙅 猜不到"): st.session_state.pending = "我想不出来了，请直接揭晓答案。"; st.rerun()
            with qc3: 
                # 换个人：原地重置
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
        st.markdown(f'<div style="text-align:center; padding:15px; border-radius:12px; border:1px solid #00D2FF; background:rgba(0,210,255,0.03); margin:20px 0;"><h3>{"🎯 推理成功" if st.session_state.win else "❄️ 挑战结束"}</h3><p>本次推理消耗: {st.session_state.count} 轮</p></div>', unsafe_allow_html=True)
        if st.button("🎮 换个人重新猜", use_container_width=True, type="primary"):
            st.session_state.msgs, st.session_state.over, st.session_state.win, st.session_state.count = [], False, False, 0
            if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", is_start_trigger=True)
            else: ask_ai()
            st.rerun()
