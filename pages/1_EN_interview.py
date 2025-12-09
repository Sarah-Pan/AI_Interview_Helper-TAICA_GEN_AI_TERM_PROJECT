import streamlit as st
import os
from utils import get_ai_response, transcribe_audio, generate_evaluation, text_to_speech

st.set_page_config(page_title="English Interview", layout="wide")

st.header("🇺🇸 English Mock Interview")

# 0. Check for resume
if "resume_text" not in st.session_state or not st.session_state.resume_text:
    st.warning("⚠️ Please upload your resume on the **Home** page first.")
    st.stop()

# 1. Initialize Session State
if "messages_en" not in st.session_state:
    st.session_state.messages_en = []
if "interview_active_en" not in st.session_state:
    st.session_state.interview_active_en = True

# --- 🔊 Audio Relay (Fix for continuous flow) ---
# Check if there is audio pending from the previous run
if "pending_audio_en" in st.session_state and st.session_state.pending_audio_en:
    st.audio(st.session_state.pending_audio_en, format="audio/mp3", autoplay=True)
    del st.session_state.pending_audio_en

# --- Display History First ---
for msg in st.session_state.messages_en:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- Initial Greeting Logic (Auto-start) ---
if len(st.session_state.messages_en) == 0:
    system_prompt = f"""
    You are a professional Hiring Manager. Conduct an interview in English based on the candidate's resume.

    Resume Content: {st.session_state.resume_text}
    Rules:
    1. Ask only one question at a time.
    2. Keep your question short and concise.
    3. Do NOT provide feedback or suggestions during the interview; focus solely on asking questions and follow-ups.
    4. Maintain a professional, polite, yet rigorous tone.
    5. Start the first response by briefly welcoming the candidate to the interview, then immediately ask the first question based on their resume.
    6. Conduct the entire dialogue in English.
    7. Intersperse Behavioral Questions (e.g., "Tell me about a time you resolved a conflict within a team").
    """
    st.session_state.messages_en.append({"role": "system", "content": system_prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Interviewer is preparing the first question..."):
            # 1. Get Generator
            stream = get_ai_response(st.session_state.messages_en, model="openai/gpt-oss-120b")
            
            # 2. Buffer Text
            response_text = ""
            for chunk in stream:
                response_text += chunk
            
            # 3. Generate Audio
            audio_bytes = None
            if response_text and len(response_text.strip()) > 0:
                audio_file = text_to_speech(response_text, language='en')
                if audio_file:
                    with open(audio_file, "rb") as f:
                        audio_bytes = f.read()
                    try: os.unlink(audio_file)
                    except: pass
        
    # 4. Save & Rerun
    if response_text:
        st.write(response_text)
        st.session_state.messages_en.append({"role": "assistant", "content": response_text})
        
        if audio_bytes:
            st.session_state.pending_audio_en = audio_bytes
            st.rerun() # Force refresh to trigger audio play and reset inputs


# 2. Active Interview Loop
if st.session_state.interview_active_en:
    
    st.write("---")
    
    # --- Layout Update: Audio Only, Stacked Vertically ---
    
    # 1. Audio Recorder
    # Dynamic key to reset audio widget after every turn
    audio_value = st.audio_input("🎙️ Record Answer", key=f"audio_en_{len(st.session_state.messages_en)}")
    
    # 2. Finish Button (Placed directly below audio input)
    # Using a container or just logic order to ensure it appears below
    if st.button("🏁 Finish Interview", key="btn_finish_en", type="primary"):
        st.session_state.interview_active_en = False
        st.rerun()

    # REMOVED: st.chat_input (Text input is gone)

    user_final_input = None

    # Handle Input (Audio ONLY)
    if audio_value:
        with st.spinner("Transcribing..."):
            transcription = transcribe_audio(audio_value, language="en")
            if transcription:
                user_final_input = transcription

    # Process Answer
    if user_final_input:
        # A. Show User Input
        with st.chat_message("user"):
            st.write(user_final_input)
        st.session_state.messages_en.append({"role": "user", "content": user_final_input})

        # B. AI Response Generation
        with st.chat_message("assistant"):
            
            with st.spinner("Interviewer is thinking..."):
                # 1. Get Generator
                stream = get_ai_response(st.session_state.messages_en, model="openai/gpt-oss-120b")
                
                # 2. Buffer Text
                response_text = ""
                for chunk in stream:
                    response_text += chunk
                
                # 3. Generate Audio
                audio_bytes = None
                if response_text and len(response_text.strip()) > 0:
                    audio_file = text_to_speech(response_text, language='en')
                    if audio_file:
                        with open(audio_file, "rb") as f:
                            audio_bytes = f.read()
                        try: os.unlink(audio_file)
                        except: pass

            # 4. Save & Rerun
            if response_text:
                st.session_state.messages_en.append({"role": "assistant", "content": response_text})
                
                if audio_bytes:
                    st.session_state.pending_audio_en = audio_bytes
                
                st.rerun() # Essential for continuous flow
            else:
                st.error("❌ API returned empty response.")

# 3. Evaluation
else:
    st.success("Interview Finished. Generating Report...")
    transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages_en if m['role'] != 'system'])
    
    with st.spinner("AI is analyzing your performance..."):
        feedback = generate_evaluation(transcript, st.session_state.resume_text, language="English")
        st.markdown("### 📊 Interview Evaluation")
        st.markdown(feedback)
    
    if st.button("Restart English Interview"):
        st.session_state.messages_en = []
        st.session_state.interview_active_en = True
        st.rerun()