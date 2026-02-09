import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions

# --- 1. 安全获取 API Key (云端模式) ---
# 部署后，我们在 Streamlit 后台填入这个 Key，代码里不出现明文
if "GEMINI_API_KEY" not in st.secrets:
    st.error("请在 Streamlit Secrets 中配置 GEMINI_API_KEY")
    st.stop()

API_KEY = st.secrets["GEMINI_API_KEY"]

# --- 2. 初始化配置 (移除 os.environ 代理) ---
# 注意：Streamlit Cloud 服务器在海外，不需要本地那套 10090 代理
try:
    genai.configure(api_key=API_KEY)
    # 之前诊断出的最强模型
    model = genai.GenerativeModel("models/gemini-3-flash-preview") 
except Exception as e:
    st.error(f"初始化失败: {e}")
    st.stop()