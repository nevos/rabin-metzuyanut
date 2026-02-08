import ollama
from faster_whisper import WhisperModel
import speech_recognition as sr
from datetime import datetime
import os

# 1. טעינת מודל השמיעה (לוקאלי)
model_size = "base" # אפשר לשנות ל-medium לדיוק גבוה יותר בעברית
model = WhisperModel(model_size, device="cpu", compute_type="int8")

def listen_and_process():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("אני מקשיב... (דבר בעברית)")
        audio = r.listen(source)
        
        # שמירת האודיו זמנית
        with open("temp.wav", "wb") as f:
            f.write(audio.get_wav_data())

    # 2. המרה לטקסט
    segments, _ = model.transcribe("temp.wav", language="he")
    user_text = " ".join([seg.text for seg in segments])
    print(f"זיהיתי: {user_text}")

    # 3. שליחה ל-Ollama
    response = ollama.chat(model='gemma2:9b', messages=[
        {'role': 'user', 'content': user_text},
    ])
    
    ai_response = response['message']['content']
    print(f"תשובת ה-AI: {ai_response}")
    
    # 4. שמירה לקובץ עם חותמת זמן
    now = datetime.now()
    timestamp_input = now.strftime("%d-%m-%y %H:%M:%S")
    timestamp_output = now.strftime("%d-%m-%y %H:%M:%S")
    
    log_entry = f"{timestamp_input} input: {user_text}\n{timestamp_output} output: {ai_response}\n\n"
    
    with open("listen/listen_conversation_log.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    print("✓ נשמר לקובץ listen_conversation_log.txt")

if __name__ == "__main__":
    listen_and_process()