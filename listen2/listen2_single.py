import ollama
from faster_whisper import WhisperModel
import speech_recognition as sr
from datetime import datetime
import os
import sys
import re

# 1. טעינת מודל השמיעה (לוקאלי)
model_size = "base"
model = WhisperModel(model_size, device="cpu", compute_type="int8")

# הגדרת ההקשר והיסטוריה
context = """אתה עוזר אדיב ודברן המסייע להסביר מושגים. המשתמש יבקש ממך להסביר או להגדיר משהו, ואתה תיתן הסבר מפורט על המושג.

הנחיות לתשובות:
1. תמיד לסגנן את התשובה בעברית פורמלית בלבד - אסור להשתמש באותיות לטיניות או מילים באנגלית
2. פרמט את התשובה עם שורות ריקות בין פסקאות ומקטעים
3. השתמש בפסקאות קצרות (2-3 משפטים לכל היותר)
4. הוסף שורה ריקה אחרי כל כותרת או נקודה מרכזית
5. מבנה התשובה:
   - פסקת פתיחה קצרה (הגדרה כללית)
   - שורה ריקה
   - פירוט בנקודות או פסקאות נפרדות
   - שורה ריקה בין כל נקודה
6. אם נשאלת שאלה, ענה עליה ישירות תחילה, ואז הרחב במידת הצורך
7. הימנע מחזרות מיותרות
8. שמור על רציפות בשיחה - זכור את ההקשר של השיחה הקודמת

דוגמה לפורמט נכון:
"לידה היא התהליך הטבעי שבו תינוק יוצא מרחם האם לעולם.

התהליך כולל מספר שלבים:

שלב ההריון: במשך כ-9 חודשים העובר מתפתח ברחם האם.

שלב הלידה עצמה: כולל צירים, התרחבות צוואר הרחם, ולבסוף יציאת התינוק.

אחרי הלידה: יוצא השליה והתינוק מתחיל לנשום בעצמו."
"""

# Load history from log file
def load_history_from_log(log_file="listen2/listen2_conversation_log.txt", max_exchanges=5):
    """Load the last N conversation exchanges from the log file"""
    history = []
    
    if not os.path.exists(log_file):
        return history
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by separator
        blocks = content.split('=' * 50)
        
        # Get last N blocks (each block is one exchange)
        recent_blocks = [b for b in blocks if b.strip()][-max_exchanges:]
        
        for block in recent_blocks:
            lines = block.strip().split('\n')
            user_msg = None
            ai_msg = None
            current_field = None
            
            for line in lines:
                if ' input:' in line:
                    current_field = 'input'
                    user_msg = ''
                elif ' output:' in line:
                    current_field = 'output'
                    ai_msg = ''
                elif current_field == 'input' and user_msg is not None:
                    user_msg += line + '\n'
                elif current_field == 'output' and ai_msg is not None:
                    ai_msg += line + '\n'
            
            # Add to history
            if user_msg and user_msg.strip():
                history.append({'role': 'user', 'content': user_msg.strip()})
            if ai_msg and ai_msg.strip():
                history.append({'role': 'assistant', 'content': ai_msg.strip()})
        
        print(f"📖 טענתי {len(history)//2} חילופי דברים מההיסטוריה", file=sys.stderr)
        return history
        
    except Exception as e:
        print(f"⚠️  שגיאה בטעינת היסטוריה: {e}", file=sys.stderr)
        return history

# Initialize conversation history with context and previous exchanges
conversation_history = [{'role': 'system', 'content': context}]
previous_history = load_history_from_log()
conversation_history.extend(previous_history)

def listen_and_process():
    global conversation_history
    
    r = sr.Recognizer()
    # Adjust for ambient noise and set more lenient thresholds
    r.energy_threshold = 300  # Lower threshold for quieter speech
    r.dynamic_energy_threshold = True
    
    with sr.Microphone() as source:
        print("מכוון לרעש רקע...", file=sys.stderr)
        r.adjust_for_ambient_noise(source, duration=1)
        print("אני מקשיב... (דבר בעברית)", file=sys.stderr)
        audio = r.listen(source, timeout=10, phrase_time_limit=15)
        
        # שמירת האודיו זמנית
        with open("temp.wav", "wb") as f:
            f.write(audio.get_wav_data())

    # 2. המרה לטקסט
    segments, _ = model.transcribe("temp.wav", language="he")
    user_text = " ".join([seg.text for seg in segments]).strip()
    
    # בדיקה אם הקלט ריק
    if not user_text:
        print("⚠️  לא זיהיתי דיבור. נסה שוב...", file=sys.stderr)
        sys.exit(1)  # Exit with error code so backend knows it failed
    
    print(f"זיהיתי: {user_text}", file=sys.stderr)

    # 3. הוספת הקלט של המשתמש להיסטוריה
    conversation_history.append({'role': 'user', 'content': user_text})

    # 4. שמירת רק 5 חילופי דברים אחרונים (+ הודעת המערכת)
    max_messages = 11
    if len(conversation_history) > max_messages:
        conversation_history = [conversation_history[0]] + conversation_history[-10:]

    # 5. שליחה ל-Ollama עם ההיסטוריה המצומצמת
    response = ollama.chat(
        model='gemma2:9b',
        messages=conversation_history,
        options={
            'temperature': 0.6,
            'top_p': 0.9,
            'top_k': 40,
            'repeat_penalty': 1.2,
            'num_predict': 800,
            'stop': ['\n\n\n\n\n'],
        }
    )
    
    ai_response = response['message']['content'].strip()
    
    # Clean up excessive blank lines
    ai_response = re.sub(r'\n{3,}', '\n\n', ai_response)
    
    print(f"תשובת ה-AI: {ai_response}", file=sys.stderr)
    
    # 6. הוספת תשובת ה-AI להיסטוריה
    conversation_history.append({'role': 'assistant', 'content': ai_response})
    
    # 7. שמירה לקובץ עם חותמת זמן
    now = datetime.now()
    timestamp_input = now.strftime("%d-%m-%y %H:%M:%S")
    timestamp_output = now.strftime("%d-%m-%y %H:%M:%S")
    
    log_entry = f"{timestamp_input} input:\n{user_text}\n\n{timestamp_output} output:\n{ai_response}\n\n{'='*50}\n\n"
    
    with open("listen2/listen2_conversation_log.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    print("✓ נשמר לקובץ listen2_conversation_log.txt", file=sys.stderr)
    print("SUCCESS", file=sys.stdout)  # Signal success to backend
    return True

if __name__ == "__main__":
    try:
        result = listen_and_process()
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"שגיאה: {e}", file=sys.stderr)
        sys.exit(1)
