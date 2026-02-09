import streamlit as st
from openai import OpenAI

# ==========================================
# 1. 界面与氛围配置
# ==========================================
st.set_page_config(page_title="Gemini 3 画影神探", page_icon="🎨", layout="centered")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at center, #2b2d42 0%, #1a1a2e 100%); color: #edf2f4; }
    /* 按钮样式优化 */
    div.stButton > button {
        border-radius: 12px;
        height: 3.8em;
        background: linear-gradient(135deg, #ef476f 0%, #f78c6b 100%);
        color: white;
        border: none; font-weight: bold; letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(239, 71, 111, 0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(239, 71, 111, 0.5); }
    /* 对话框样式 */
    .stChatMessage { border-radius: 18px; background-color: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.1); }
    /* 图片说明样式 */
    .stImage caption { color: #ccc; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 状态初始化
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "game_over" not in st.session_state: st.session_state.game_over = False
if "question_count" not in st.session_state: st.session_state.question_count = 0
if "final_image_url" not in st.session_state: st.session_state.final_image_url = None

# ==========================================
# 3. WildCard API 配置
# ==========================================
API_KEY = st.secrets.get("API_KEY", "")
if not API_KEY:
    st.error("❌ 请先配置 Secrets API_KEY")
    st.stop()

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.gptsapi.net/v1"
)

# 对话模型与绘图模型
CHAT_MODEL = "gemini-3-flash-preview" # 如果报错改为 gemini-2.0-flash
IMAGE_MODEL = "dall-e-3" # 通用的绘图模型标识

# ==========================================
# 4. 核心功能函数
# ==========================================

# --- 4.1 猜人逻辑 (Gemini 3) ---
SYSTEM_PROMPT = """你现在是代号为'Gemini-3'的顶级逻辑实体。
任务：通过是非题猜出用户心中的人物。
风格：冷峻、睿智、直觉跳跃。
规则：一次只问一个是非题。当你确定率超过 95% 时，直接说出答案，例如：“答案是：[人物名字]”。"""

def get_gemini_response(user_input=None):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, *st.session_state.messages],
            temperature=0.9
        )
        ai_reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        
        # 判定结束：无问号，或明确包含猜测关键词
        if ("?" not in ai_reply and "？" not in ai_reply) or any(w in ai_reply for w in ["答案是", "猜到了", "你是"]):
            st.session_state.game_over = True
    except Exception as e:
        st.error(f"🔮 链接波动: {e}")

# --- 4.2 辅助：从回复中提取纯人名 ---
def extract_character_name(final_reply_text):
    try:
        # 用一个快速便宜的小模型来做信息抽取
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "你的任务是从用户的文本中提取出那个被猜测的人物的名字。只返回名字本身，不要任何标点符号或其他文字。"},
                {"role": "user", "content": final_reply_text}
            ]
        )
        return response.choices[0].message.content.strip()
    except:
        return "神秘人物"

# --- 4.3 核心：生成简笔画头像 (DALL-E 3) ---
def generate_line_avatar(name):
    # 核心 Prompt：强制黑色线条、简笔画、白底
    prompt = f"A minimalist black line drawing avatar of {name}. Simple ink sketch style on plain white background. No shading, no colors, pure contour lines. Hand-drawn feel."
    try:
        response = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        st.warning(f"🎨 画像绘制失败: {e}")
        return None

# ==========================================
# 5. 交互界面渲染
# ==========================================
st.title("🎨 Gemini 3：画影神探")
st.caption("⚡ 猜对即生成独家简笔画速写")

with st.sidebar:
    st.markdown("### 🔍 侦测进度")
    st.write(f"已推理：**{st.session_state.question_count}** 次")
    if st.button("🔄 抹除记忆重来", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# 启动游戏
if not st.session_state.messages:
    with st.spinner("🔮 Gemini 3 正在同步思绪..."):
        get_gemini_response()

# 游戏进行中
if not st.session_state.game_over:
    last_ai_msg = [m for m in st.session_state.messages if m["role"] == "assistant"][-1]["content"]
    with st.chat_message("assistant", avatar="✨"):
        st.markdown(f"#### {last_ai_msg}")
    st.write("---")
    
    def on_click(ans):
        st.session_state.question_count += 1
        get_gemini_response(ans)

    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", on_click=on_click, args=("是的",), use_container_width=True)
    with c2: st.button("❌ 不是", on_click=on_click, args=("不是",), use_container_width=True)
    with c3: st.button("❔ 不确定", on_click=on_click, args=("不确定",), use_container_width=True)

# 游戏结束：结算与绘图
else:
    st.balloons()
    final_reply = st.session_state.messages[-1]["content"]
    st.success("🎯 维度锁定！答案已浮现。")
    with st.chat_message("assistant", avatar="🎯"):
        st.markdown(f"### {final_reply}")

    # --- 绘图环节 ---
    # 如果还没有生成过图片，就开始生成
    if st.session_state.final_image_url is None:
        with st.spinner("🎨 正在为神秘人物绘制简笔画速写...（约需 5-10 秒）"):
            # 1. 提取名字
            char_name = extract_character_name(final_reply)
            # 2. 生成图片
            image_url = generate_line_avatar(char_name)
            # 3. 存入状态
            st.session_state.final_image_url = image_url
            st.session_state.final_char_name = char_name
            st.rerun() # 刷新以展示图片

    # 如果有图片 URL，就展示出来
    if st.session_state.final_image_url:
        st.divider()
        col_img_1, col_img_2, col_img_3 = st.columns([1, 2, 1]) # 居中展示
        with col_img_2:
            st.image(
                st.session_state.final_image_url, 
                caption=f"🖌️ AI速写：{st.session_state.final_char_name} (简笔画风格)",
                use_container_width=True
            )
    # ----------------

    st.divider()
    if st.button("🎮 再次挑战", use_container_width=True, type="primary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
