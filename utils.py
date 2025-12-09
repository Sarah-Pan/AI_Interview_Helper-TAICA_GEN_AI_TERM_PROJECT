import os
import streamlit as st
from groq import Groq
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from gtts import gTTS
import tempfile
load_dotenv()

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("❌ 未偵測到 API Key。請確認 .env 檔案已設定 GROQ_API_KEY。")
        return None
    return Groq(api_key=api_key)

def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"PDF 解析失敗: {e}")
        return ""

# utils.py

def get_ai_response(messages, model="openai/gpt-oss-120b"):
    client = get_groq_client()
    if not client: 
        def no_client_gen(): yield "API Error: No Client"
        return no_client_gen()
    
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=True, 
        )
        
        # --- 暴力抓字 Generator ---
        def text_generator():
            full_text = ""
            for chunk in stream:
                if chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_text += content
                    yield content
            
            # (除錯用) 如果 generator 結束了，我們可以把 full_text 印在 server log
            print(f"Server Log: Generated Text Length: {len(full_text)}")

        return text_generator()

    except Exception as e:
        error_msg = str(e)
        def error_generator(): yield f"Error: {error_msg}"
        return error_generator()

def transcribe_audio(audio_file, language="zh"):
    """使用 Groq Whisper 進行語音轉文字 (指定繁體中文 + 防幻覺)"""
    client = get_groq_client()
    if not client: return None

    try:
        # 確保檔案指標在開頭
        audio_file.seek(0)
        
        # 呼叫 API
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_file, "audio/wav"),
            model="whisper-large-v3",
            response_format="text",
            language=language, # 這裡設定 'zh'
            temperature=0.0,   # 低溫度減少亂猜
            # --- 關鍵修正：用繁體中文 prompt 引導模型 ---
            prompt="這是一段使用繁體中文進行的面試對話紀錄。請用繁體字輸出。"
        )
        
        # --- 🛡️ 防幻覺濾網 (Hallucination Filter) ---
        hallucinations = [
            "点赞", "订阅", "转发", "打赏", "明镜", "点点栏目", 
            "Subscribe", "channel", "watching", "MOOC", 
            "字幕", "Copyright", "權利", "视频", "視頻"
        ]
        
        # 檢查是否包含幻覺關鍵字
        for trash in hallucinations:
            if trash in transcription:
                print(f"⚠️ 偵測到 Whisper 幻覺: {transcription} -> 已忽略")
                return None
                
        # 檢查字數
        if len(transcription.strip()) < 2:
            return None
            
        # --- 額外保險：如果還是出現簡體，這裡可以做簡單轉換 (選用) ---
        # 但通常上面的 prompt 就很有效了
        
        return transcription
        
    except Exception as e:
        st.error(f"語音辨識失敗 (API Error): {e}")
        return None
    
def text_to_speech(text, language='zh-tw'):
    """將文字轉為語音並回傳暫存檔案路徑"""
    try:
        # 使用 gTTS 產生語音
        tts = gTTS(text=text, lang=language, slow=False)
        # 建立暫存檔
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        st.warning(f"語音生成失敗: {e}")
        return None

def generate_evaluation(history, resume_text, language="Chinese"):
    client = get_groq_client()
    if not client: return "API Error"

    criteria = """
    1. 邏輯與結構 (Logic & Structure): Did they use the STAR method? Was the answer organized?
    2. 內容切題度 (Relevance & Content): Did they answer the specific question asked?
    3. 表達流暢度 (Communication & Fluency): Clarity, conciseness, and confidence.
    4. 專業度與態度 (Professionalism & Attitude): Problem-solving mindset and cultural fit.
    5. 履歷一致性 (Resume Consistency): Does the answer align with the claims in their resume?
    """
    
    lang_instruction = "請用繁體中文回應" if language == "Chinese" else "Please respond in English"
    
    prompt = f"""
    You are an expert interview coach. 
    Analyze the following interview transcript based on the candidate's resume.
    
    Resume Content:
    {resume_text[:2000]}... (truncated)

    Interview Transcript:
    {history}

    --- SCORING RULES (CRITICAL) ---
    1. **Avoid Grade Inflation**: Most candidates score between 5 and 7. A score of 8 is "Good". A score of 9-10 is reserved for perfection and should be extremely rare.
    2. **Point out Flaws**: You MUST identify at least one weakness for every strength mentioned.

    Please provide a score (1-10) and detailed feedback for the following criteria:
    {criteria}

    Finally, give an overall summary and 3 specific actionable tips for improvement.
    {lang_instruction}. format the output with clear markdown headings.
    """
    
    messages = [{"role": "user", "content": prompt}]
    
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.5
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"評分生成失敗: {e}"