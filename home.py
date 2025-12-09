import streamlit as st
from utils import extract_text_from_pdf

st.set_page_config(page_title="AI 模擬面試 Agent", layout="wide")

st.title("📂 準備您的面試")

# --- 初始化全域 Session State ---
# 這些變數會在不同頁面間共享
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

# 用於重置面試狀態的 Helper
def reset_interview_state():
    st.session_state.messages_cn = []
    st.session_state.messages_en = []
    st.session_state.interview_active_cn = True
    st.session_state.interview_active_en = True

st.markdown("""
### 歡迎使用 AI 模擬面試系統
請先在此頁面上傳您的 **PDF 履歷**。完成後，請從左側側邊欄選擇 **中文** 或 **英文** 面試。
""")

st.divider()

st.header("步驟 1: 上傳履歷")
uploaded_file = st.file_uploader("選擇 PDF 檔案", type="pdf")

if uploaded_file is not None:
    # 如果使用者上傳了新檔案，我們應該清除舊的對話紀錄，以免邏輯混亂
    text = extract_text_from_pdf(uploaded_file)
    
    if text != st.session_state.resume_text:
        st.session_state.resume_text = text
        reset_interview_state() # 重置對話
        st.toast("新履歷已上傳，面試紀錄已重置！", icon="✅")
    
    st.success("履歷解析成功！請點擊左側分頁開始面試。")
    
    with st.expander("預覽解析後的履歷內容"):
        st.text(st.session_state.resume_text[:1000] + "...")
else:
    if st.session_state.resume_text:
        st.info("目前系統已存有一份履歷。若要更換，請重新上傳。")
    else:
        st.warning("請先上傳履歷才能進行面試。")