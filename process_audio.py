#!/usr/bin/env python3
"""
Process pre-recorded audio file for transcription and AI response
"""
import ollama
from faster_whisper import WhisperModel
from datetime import datetime
import sys
import os
import re
import time
import json

# Load Whisper model
model_size = "base"
model = WhisperModel(model_size, device="cpu", compute_type="int8")

# Load configuration
def load_config():
    """Load model, options, and context from config_runtime.json"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_runtime.json')
    
    # Ensure runtime config exists
    if not os.path.exists(config_path):
        default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        if os.path.exists(default_path):
            import shutil
            shutil.copy2(default_path, config_path)
            print(f"⚠️  Created config_runtime.json from defaults", file=sys.stderr)
        else:
            print(f"⚠️  ERROR: No config files found!", file=sys.stderr)
            sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        model = config.get('model', 'gemma2:9b')
        options = config.get('options', {})
        context = config.get('context', '')
        
        if not context:
            print(f"⚠️  Warning: No context in config", file=sys.stderr)
        
        return model, options, context
    except Exception as e:
        print(f"⚠️  Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)

# Initialize conversation history with context from config
model_name, model_options, context = load_config()
conversation_history = [{'role': 'system', 'content': context}]

def process_audio_file(audio_path):
    """Process an audio file and generate AI response"""
    global conversation_history
    
    start_time = time.time()  # Track start time
    
    if not os.path.exists(audio_path):
        print(f"שגיאה: קובץ אודיו לא נמצא: {audio_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"מעבד קובץ אודיו: {audio_path}", file=sys.stderr)
    
    # Transcribe audio
    try:
        segments, _ = model.transcribe(audio_path, language="he")
        user_text = " ".join([seg.text for seg in segments]).strip()
    except Exception as e:
        print(f"שגיאה בתמלול: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Check if transcription is empty
    if not user_text:
        print("⚠️  לא זיהיתי דיבור בקובץ", file=sys.stderr)
        sys.exit(1)
    
    print(f"זיהיתי: {user_text}", file=sys.stderr)
    
    # Add to conversation history
    conversation_history.append({'role': 'user', 'content': user_text})
    
    # Keep only last 5 exchanges
    max_messages = 11
    if len(conversation_history) > max_messages:
        conversation_history = [conversation_history[0]] + conversation_history[-10:]
    
    # Get AI response with configured parameters
    try:
        model_name, model_options, _ = load_config()
        # Add stop sequences
        model_options['stop'] = ['\n\n\n\n\n']
        
        print(f"⏳ שולח ל-Ollama (מודל: {model_name})...", file=sys.stderr)
        response = ollama.chat(
            model=model_name,
            messages=conversation_history,
            options=model_options
        )
        print(f"✓ קיבלתי תשובה מ-Ollama", file=sys.stderr)
        ai_response = response['message']['content'].strip()
        
        # Clean up excessive blank lines (max 2 consecutive newlines)
        ai_response = re.sub(r'\n{3,}', '\n\n', ai_response)
        
        print(f"תשובת ה-AI: {ai_response}", file=sys.stderr)
    except Exception as e:
        print(f"שגיאה בקבלת תשובה מ-AI: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Add AI response to history
    conversation_history.append({'role': 'assistant', 'content': ai_response})
    
    # Calculate response time
    end_time = time.time()
    response_time = round(end_time - start_time, 2)
    
    # Save to file
    now = datetime.now()
    timestamp_input = now.strftime("%d-%m-%y %H:%M:%S")
    timestamp_output = now.strftime("%d-%m-%y %H:%M:%S")
    
    # Include config in log
    model_name, model_options, _ = load_config()
    config_str = f"מודל: {model_name} | טמפרטורה: {model_options.get('temperature', 0.6)} | דגימה: {model_options.get('top_p', 0.9)} | מילים: {model_options.get('top_k', 40)}"
    
    log_entry = f"{timestamp_input} input:\n{user_text}\n\n{timestamp_output} output:\n{ai_response}\n\nזמן תגובה: {response_time} שניות\nתצורה: {config_str}\n\n{'='*50}\n\n"
    
    try:
        with open("conversation.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
        print("✓ נשמר לקובץ conversation.txt", file=sys.stderr)
        print("SUCCESS", file=sys.stdout)
    except Exception as e:
        print(f"שגיאה בשמירה לקובץ: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("שימוש: python process_audio.py <audio_file_path>", file=sys.stderr)
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    try:
        process_audio_file(audio_path)
        sys.exit(0)
    except Exception as e:
        print(f"שגיאה: {e}", file=sys.stderr)
        sys.exit(1)
