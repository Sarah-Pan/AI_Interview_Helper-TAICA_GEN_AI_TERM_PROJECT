import streamlit as st
import os
from utils import get_ai_response, transcribe_audio, generate_evaluation, text_to_speech

st.set_page_config(page_title="中文模擬面試", layout="wide")

st.header("🇹🇼 中文模擬面試")

# 0. 檢查履歷
if "resume_text" not in st.session_state or not st.session_state.resume_text:
    st.warning("⚠️ 請先返回 **Home** 頁面上傳履歷。")
    st.stop()

# 1. 初始化 Session State
if "messages_cn" not in st.session_state:
    st.session_state.messages_cn = []
if "interview_active_cn" not in st.session_state:
    st.session_state.interview_active_cn = True

# --- 🔊 接力棒語音播放 (確保流程順暢) ---
# 檢查是否有上一輪留下來要播放的語音
if "pending_audio_cn" in st.session_state and st.session_state.pending_audio_cn:
    st.audio(st.session_state.pending_audio_cn, format="audio/mp3", autoplay=True)
    del st.session_state.pending_audio_cn

# --- 先顯示歷史對話 ---
for msg in st.session_state.messages_cn:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- Agent 主動開場邏輯 ---
if len(st.session_state.messages_cn) == 0:
    system_prompt = f"""
    你是一位專業的面試官。請根據使用者的履歷內容進行中文面試。

    履歷內容: {st.session_state.resume_text}
    規則：
    1. 一次只問一個問題。
    2. 問題要簡短精確。
    3. *不要* 給予建議或回饋，只要專注於提問和追問。
    4. 保持專業、客氣但嚴謹的語氣。
    5. 第一句話請先簡單開場歡迎使用者來到面試，並直接開始針對履歷問第一個問題。
    6. 使用繁體中文進行對話。
    7. 穿插行為面試問題 (例如：「請舉例說明你在團隊中解決衝突的經驗」)。
    """
    st.session_state.messages_cn.append({"role": "system", "content": system_prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("面試官正在準備提問..."):
            # 1. 取得產生器 (中文建議使用 llama-3.3-70b-versatile)
            stream = get_ai_response(st.session_state.messages_cn, model="llama-3.3-70b-versatile")
            
            # 2. 後台接收文字
            response_text = ""
            for chunk in stream:
                response_text += chunk
            
            # 3. 生成語音
            audio_bytes = None
            if response_text and len(response_text.strip()) > 0:
                # 設定為中文語音
                audio_file = text_to_speech(response_text, language='zh-tw')
                if audio_file:
                    with open(audio_file, "rb") as f:
                        audio_bytes = f.read()
                    try: os.unlink(audio_file)
                    except: pass
        
    # 4. 顯示與存檔
    if response_text:
        st.write(response_text)
        st.session_state.messages_cn.append({"role": "assistant", "content": response_text})
        
        if audio_bytes:
            st.session_state.pending_audio_cn = audio_bytes
            st.rerun() # 強制刷新以播放語音並重置輸入框


# 2. 面試進行中邏輯
if st.session_state.interview_active_cn:
    
    st.write("---")
    
    # --- 介面修正：僅保留語音，垂直排列 ---
    
    # 1. 錄音按鈕
    # 使用 dynamic key 確保每次對話後錄音元件會重置
    audio_value = st.audio_input("🎙️ 語音回答", key=f"audio_cn_{len(st.session_state.messages_cn)}")
    
    # 2. 完成按鈕 (直接放在錄音按鈕下方)
    if st.button("🏁 完成面試", key="btn_finish_cn", type="primary"):
        st.session_state.interview_active_cn = False
        st.rerun()

    # 已移除 st.chat_input (文字輸入框)

    user_final_input = None

    # 處理輸入 (僅語音)
    if audio_value:
        with st.spinner("🎤 正在辨識..."):
            transcription = transcribe_audio(audio_value, language="zh")
            if transcription:
                user_final_input = transcription

    # 提交回答與生成
    if user_final_input:
        # A. 顯示使用者回答
        with st.chat_message("user"):
            st.write(user_final_input)
        st.session_state.messages_cn.append({"role": "user", "content": user_final_input})

        # B. AI 生成回應
        with st.chat_message("assistant"):
            
            with st.spinner("面試官正在思考..."):
                # 1. 取得產生器
                stream = get_ai_response(st.session_state.messages_cn, model="llama-3.3-70b-versatile")
                
                # 2. 後台接收文字
                response_text = ""
                for chunk in stream:
                    response_text += chunk
                
                # 3. 生成語音
                audio_bytes = None
                if response_text and len(response_text.strip()) > 0:
                    audio_file = text_to_speech(response_text, language='zh-tw')
                    if audio_file:
                        with open(audio_file, "rb") as f:
                            audio_bytes = f.read()
                        try: os.unlink(audio_file)
                        except: pass

            # 4. 存檔與刷新
            if response_text:
                st.session_state.messages_cn.append({"role": "assistant", "content": response_text})
                
                if audio_bytes:
                    st.session_state.pending_audio_cn = audio_bytes
                
                st.rerun() # 必要的流程控制
            else:
                st.error("❌ API 未回傳任何文字")

# 3. 面試結束
else:
    st.success("✅ 面試已結束，正在生成評估報告...")
    
    transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages_cn if m['role'] != 'system'])
    
    with st.spinner("AI 正在分析表現..."):
        feedback = generate_evaluation(transcript, st.session_state.resume_text, language="Chinese")
        st.markdown("### 📊 面試評分與回饋")
        st.markdown(feedback)
    
    if st.button("重新開始中文面試"):
        st.session_state.messages_cn = []
        st.session_state.interview_active_cn = True
        st.rerun()