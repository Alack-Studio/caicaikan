import streamlit as st
from openai import OpenAI
import random

# ==============================================================================
# 1. PC 端经典 UI 架构：赛博深夜与呼吸发光
# ==============================================================================
st.set_page_config(page_title="AI 猜猜看", layout="centered")

# 强制隐藏侧边栏与页眉
st.markdown("<style>[data-testid='stSidebar'], header {display: none;}</style>", unsafe_allow_html=True)

# 赛博深夜色彩方案
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
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# ==============================================================================
# 2. 状态初始化与逻辑引擎
# ==============================================================================
states = {"msgs":[], "role":"AI 猜", "started":False, "over":False, "win":False, "model":"gemini-2.5-flash-lite", "count":0, "pending":None, "seed_category":""}
for k, v in states.items():
    if k not in st.session_state: st.session_state[k] = v

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None, hidden_trigger=False):
    if inp:
        st.session_state.msgs.append({"role": "user", "content": inp, "hidden": hidden_trigger})
        if not hidden_trigger: st.session_state.count += 1
    
    with st.spinner("正在启动推理引擎..."):
        if st.session_state.role == "AI 猜":
            sys = "你是一个侦探。目标是猜出用户想的名人。第一句话直接问问题，不要废话。确定答案回复：答案是：[人名]。"
        else:
            if not st.session_state.seed_category:
                st.session_state.seed_category = random.choice(["电影主角", "历史领袖", "动漫主角", "超级英雄", "流行歌手", "科学家"])
            sys = f"你已选定目标：【{st.session_state.seed_category}】。用户提问你只答'是/否/模糊'。用户猜中回复：🎉 恭喜你，答对了！真相是：[人名]。"
        
        try:
            api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.msgs]
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys}] + api_msgs, temperature=0.7)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            
            if any(x in reply for x in ["答案是", "恭喜", "真相是"]): st.session_state.over, st.session_state.win = True, True
            elif inp and "想不出来" in str(inp): st.session_state.over, st.session_state.win = True, False
        except Exception as e: st.error(f"📡 API 异常: {str(e)}")

if st.session_state.pending:
    payload = st.session_state.pending; st.session_state.pending = None
    ask_ai(payload, hidden_trigger=(payload == "请直接给我第一个提示。")); st.rerun()

# ==============================================================================
# 3. 经典 PC 布局逻辑
# ==============================================================================
if not st.session_state.started:
    st.write("---")
    st.markdown("### 🎭 模式选择") # 经典文案
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🤖 AI 猜 (它问我答)", use_container_width=True, type="primary" if st.session_state.role=="AI 猜" else "secondary"):
            st.session_state.role = "AI 猜"; st.rerun()
    with c2:
        if st.button("🕵️ 我猜 (我问它答)", use_container_width=True, type="primary" if st.session_state.role=="我猜" else "secondary"):
            st.session_state.role = "我猜"; st.rerun()
            
    st.write("")
    st.markdown("### 🔮 挑战对象") # 经典文案
    models_info = {"gemini-2.5-flash-lite": "⚡ 极速响应", "gemini-2.5-pro": "🧠 逻辑专家", "gemini-3-pro-preview": "🔥 究极核心"}
    m_cols = st.columns(3)
    for i, (m_key, m_desc) in enumerate(models_info.items()):
        with m_cols[i]:
            if st.button(m_key.replace("gemini-",""), use_container_width=True, type="primary" if st.session_state.model == m_key else "secondary"):
                st.session_state.model = m_key; st.rerun()
            st.markdown(f'<p class="model-desc">{m_desc}</p>', unsafe_allow_html=True)
    
    st.write("---")
    if st.button("🚀 开始推理", use_container_width=True, type="primary"):
        st.session_state.started = True
        if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", hidden_trigger=True)
        else: ask_ai()
        st.rerun()

else:
    for m in st.session_state.msgs:
        if m.get("hidden", False): continue
        with st.chat_message(m["role"], avatar="🕵️" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    if not st.session_state.over:
        if st.session_state.role == "AI 猜":
            st.divider()
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ 是", use_container_width=True): ask_ai("是"); st.rerun()
            if c2.button("❌ 否", use_container_width=True): ask_ai("否"); st.rerun()
            if c3.button("❔ 模糊", use_container_width=True): ask_ai("不确定"); st.rerun()
        else:
            # PC 端 4 按钮布局
            qc1, qc2, qc3, qc4 = st.columns([0.18, 0.22, 0.22, 0.38])
            with qc1: 
                if st.button("💡 提示"): st.session_state.pending = "提示一下，不要说废话。"; st.rerun()
            with qc2: 
                if st.button("🙅 猜不到"): st.session_state.pending = "我想不出来了，请直接揭晓答案。"; st.rerun()
            with qc3: 
                if st.button("🔄 换个人"): 
                    st.session_state.msgs, st.session_state.count, st.session_state.seed_category = [], 0, ""
                    if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", hidden_trigger=True)
                    else: ask_ai()
                    st.rerun()
            with qc4:
                if st.button("🏠 菜单"): st.session_state.started, st.session_state.msgs, st.session_state.over = False, [], False; st.rerun()
            q = st.chat_input("输入你的推理提问...")
            if q: ask_ai(q); st.rerun()
    else:
        if st.session_state.win: st.balloons()
        else: st.snow()
        st.markdown(f'<div style="text-align:center; padding:15px; border-radius:12px; border:1px solid #00D2FF; background:rgba(0,210,255,0.03); margin:20px 0;"><h3>{"🎯 推理成功" if st.session_state.win else "❄️ 结束"}</h3><p>消耗: {st.session_state.count} 轮</p></div>', unsafe_allow_html=True)
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("🎮 换个人重新猜", use_container_width=True, type="primary"):
                st.session_state.msgs, st.session_state.over, st.session_state.win, st.session_state.count, st.session_state.seed_category = [], False, False, 0, ""
                if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", hidden_trigger=True)
                else: ask_ai()
                st.rerun()
        with bc2:
            if st.button("🏠 返回选关画面", use_container_width=True):
                st.session_state.started, st.session_state.msgs, st.session_state.over = False, [], False; st.rerun()
