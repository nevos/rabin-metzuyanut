from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import os
import threading
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Paths
rabin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(rabin_dir, "conversation.txt")
CONFIG_DEFAULT_FILE = os.path.join(rabin_dir, "config.json")  # Immutable defaults
CONFIG_RUNTIME_FILE = os.path.join(rabin_dir, "config_runtime.json")  # Active config

# Ensure config_runtime.json exists on startup
def ensure_runtime_config():
    """Create config_runtime.json from config.json if it doesn't exist"""
    if not os.path.exists(CONFIG_RUNTIME_FILE):
        if os.path.exists(CONFIG_DEFAULT_FILE):
            import shutil
            shutil.copy2(CONFIG_DEFAULT_FILE, CONFIG_RUNTIME_FILE)
            print(f"[CONFIG] Created config_runtime.json from defaults", flush=True)
        else:
            print(f"[CONFIG] Warning: config.json not found!", flush=True)

# Initialize runtime config on startup
ensure_runtime_config()

# Model descriptions in Hebrew with capabilities
MODEL_DESCRIPTIONS = {
    "gemma2:9b": "מודל של גוגל (Google), מהיר ויעיל במיוחד.\n\nתמיכה: עברית מצוינת, אנגלית, שפות נוספות. יכולות: הסבר מושגים, שיחה טבעית, סיכום טקסטים, תרגום.\n\nמומלץ לשימוש יומיומי - איזון מושלם בין מהירות לאיכות.",
    "llama3.1:latest": "מודל של מטא (Meta), אמין ומוכח.\n\nתמיכה: עברית טובה, אנגלית מצוינת, רב-לשוני. יכולות: שיחה מורכבת, הסבר מפורט, קוד, היגיון.\n\nיציב ואיכותי - מתאים לשימוש כללי.",
    "deepseek-r1:14b": "מודל חזק עם יכולות חשיבה מתקדמות (reasoning). פותח על ידי DeepSeek - חברת AI סינית מובילה.\n\nתמיכה: עברית, אנגלית, תכנות. יכולות: חשיבה לוגית, פתרון בעיות, הסבר מעמיק, קוד ומתמטיקה.\n\nאיטי יותר אך מדויק במיוחד - מתאים למשימות מורכבות ומחקר.",
    "llama3.3:70b": "המודל החזק ביותר של מטא - דורש 36GB+ RAM!\n\nתמיכה: כל השפות, עברית מעולה. יכולות: הבנה מתקדמת, היגיון, יצירתיות.\n\nלא מומלץ למחשב זה - גדול מדי."
}

# Model options descriptions in Hebrew with detailed explanations
OPTIONS_DESCRIPTIONS = {
    "temperature": "טמפרטורה - שולטת ברמת היצירתיות והאקראיות של התשובות.\n\nמה זה עושה: קובע כמה המודל יהיה \"נועז\" בבחירת מילים.\n\nערך נמוך (0.1-0.4): תשובות מדויקות, עקביות וצפויות. מומלץ להגדרות, עובדות ומידע מדויק.\n\nערך בינוני (0.5-0.7): איזון טוב - תשובות טבעיות ומגוונות אך עדיין ממוקדות.\n\nערך גבוה (0.8-1.0): תשובות יצירתיות, מפתיעות ומגוונות. מתאים לסיפורים או רעיונות.",
    "top_p": "דגימה גרעינית (Nucleus Sampling) - מגבילה את מאגר המילים הזמינות.\n\nמה זה עושה: בוחר רק מילים שמצטברות ל-X% מההסתברות.\n\nערך נמוך (0.5-0.7): מגוון מילים מוגבל, תשובות ממוקדות ועקביות. מתאים להגדרות והסברים.\n\nערך בינוני (0.8-0.9): איזון טוב - מגוון סביר עם עקביות.\n\nערך גבוה (0.95-1.0): מגוון מילים רחב מאוד, תשובות מגוונות ויצירתיות.",
    "top_k": "מילים מועמדות - מגביל כמה מילים המודל שוקל בכל צעד.\n\nמה זה עושה: בכל פעם שהמודל בוחר מילה, הוא רואה רק את K המילים הסבירות ביותר.\n\nערך נמוך (10-30): בחירה ממגוון מצומצם, תשובות צפויות ומדויקות.\n\nערך בינוני (35-50): איזון בין יצירתיות לדיוק.\n\nערך גבוה (60-100): מגוון גדול של אפשרויות, תשובות מגוונות ומפתיעות.",
    "repeat_penalty": "עונש על חזרות - מונע מהמודל לחזור על אותן מילים ומשפטים.\n\nמה זה עושה: מפחית את ההסתברות לבחור במילים שכבר נאמרו.\n\nערך נמוך (1.0-1.1): מעט עונש, המודל יכול לחזור על מילים. טבעי לשיחה.\n\nערך בינוני (1.2-1.3): איזון טוב - מונע חזרות מיותרות אך שומר על טבעיות.\n\nערך גבוה (1.4-2.0): עונש חמור, המודל ימנע מחזרות בכל מחיר. לפעמים לא טבעי.",
    "num_predict": "מספר מילים מקסימלי (Tokens) - מגביל כמה מילים המודל יכול לייצר.\n\nמה זה עושה: עוצר את המודל אחרי X מילים (טוקנים).\n\nערך נמוך (200-500): תשובות קצרות וממוקדות. מתאים להגדרות מהירות.\n\nערך בינוני (600-1000): תשובות מפורטות עם הסברים. האיזון המומלץ.\n\nערך גבוה (1200-2000): תשובות ארוכות ומקיפות מאוד. עלול להיות מילולי."
}

@app.route('/api/record', methods=['POST'])
def record():
    """Trigger the listen2_single.py script"""
    try:
        # Run listen2_single.py from the rabin directory with virtual environment
        rabin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        venv_python = os.path.join(rabin_dir, '.venv', 'bin', 'python')
        
        # Use venv python if it exists, otherwise use python3
        python_cmd = venv_python if os.path.exists(venv_python) else 'python3'
        
        result = subprocess.run(
            [python_cmd, 'listen2_single.py'],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=rabin_dir
        )
        
        # Log the output for debugging
        print(f"Script stdout: {result.stdout}")
        print(f"Script stderr: {result.stderr}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Recording completed',
                'debug': {
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr or result.stdout or 'Recording failed'
            }), 500
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'התגובה לקחה יותר מדי זמן (40 שניות). נסה שוב או החלף מודל מהיר יותר בהגדרות.'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/record-audio', methods=['POST'])
def record_audio():
    """Process uploaded audio file from browser recording"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Empty filename'
            }), 400
        
        # Save the uploaded audio temporarily
        rabin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        temp_webm_path = os.path.join(rabin_dir, 'temp_upload.webm')
        temp_wav_path = os.path.join(rabin_dir, 'temp_upload.wav')
        
        audio_file.save(temp_webm_path)
        
        # Convert WebM to WAV using ffmpeg
        try:
            conversion = subprocess.run(
                ['ffmpeg', '-i', temp_webm_path, '-ar', '16000', '-ac', '1', '-y', temp_wav_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if conversion.returncode != 0:
                raise Exception(f"Audio conversion failed: {conversion.stderr}")
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': 'ffmpeg not installed. Please run: brew install ffmpeg'
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Audio conversion error: {str(e)}'
            }), 500
        
        # Process the converted audio
        venv_python = os.path.join(rabin_dir, '.venv', 'bin', 'python')
        python_cmd = venv_python if os.path.exists(venv_python) else 'python3'
        
        print(f"[DEBUG] Starting process_audio.py with file: {temp_wav_path}", flush=True)
        
        result = subprocess.run(
            [python_cmd, 'process_audio.py', temp_wav_path],
            capture_output=True,
            text=True,
            timeout=40,  # 40 second timeout
            cwd=rabin_dir
        )
        
        # Log output for debugging
        print(f"[DEBUG] Script stdout: {result.stdout}", flush=True)
        print(f"[DEBUG] Script stderr: {result.stderr}", flush=True)
        print(f"[DEBUG] Return code: {result.returncode}", flush=True)
        
        # Clean up temp files
        for temp_file in [temp_webm_path, temp_wav_path]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Recording processed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr or result.stdout or 'Processing failed'
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Processing timeout'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/text-input', methods=['POST'])
def text_input():
    """Process text input directly without audio recording"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400
        
        text = data['text'].strip()
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Empty text'
            }), 400
        
        # Run the text processing script
        rabin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        venv_python = os.path.join(rabin_dir, '.venv', 'bin', 'python')
        python_cmd = venv_python if os.path.exists(venv_python) else 'python3'
        
        result = subprocess.run(
            [python_cmd, 'process_text.py', text],
            capture_output=True,
            text=True,
            timeout=40,  # 40 second timeout
            cwd=rabin_dir
        )
        
        # Log output for debugging
        print(f"Script stdout: {result.stdout}")
        print(f"Script stderr: {result.stderr}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Text processed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr or result.stdout or 'Processing failed'
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'התגובה לקחה יותר מדי זמן (40 שניות). נסה שוב או החלף מודל מהיר יותר בהגדרות.'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation', methods=['GET'])
def get_conversation():
    """Get the conversation log"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the conversation log
            entries = []
            blocks = content.split('=' * 50)
            
            for block in blocks:
                if block.strip():
                    lines = block.strip().split('\n')
                    entry = {}
                    current_field = None
                    
                    for line in lines:
                        if ' input:' in line:
                            entry['input_timestamp'] = line.split(' input:')[0]
                            current_field = 'input'
                            entry['input'] = ''
                        elif ' output:' in line:
                            entry['output_timestamp'] = line.split(' output:')[0]
                            current_field = 'output'
                            entry['output'] = ''
                        elif line.startswith('זמן תגובה:'):
                            # Extract response time
                            entry['response_time'] = line.replace('זמן תגובה:', '').strip()
                            current_field = None
                        elif line.startswith('תצורה:'):
                            # Extract config
                            entry['config'] = line.replace('תצורה:', '').strip()
                            current_field = None
                        elif current_field:
                            # Preserve newlines by adding \n instead of space
                            if entry[current_field]:
                                entry[current_field] += '\n' + line
                            else:
                                entry[current_field] = line
                    
                    if 'input' in entry and 'output' in entry:
                        entries.append(entry)
            
            return jsonify({
                'success': True,
                'entries': entries
            })
        else:
            return jsonify({
                'success': True,
                'entries': []
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of available Ollama models"""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if parts:
                        model_name = parts[0]
                        models.append({
                            'name': model_name,
                            'description': MODEL_DESCRIPTIONS.get(model_name, u'מודל AI לצ\'אט ושיחה.')
                        })
            
            return jsonify({
                'success': True,
                'models': models
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to list models'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current model configuration from runtime config"""
    try:
        ensure_runtime_config()  # Make sure it exists
        
        if os.path.exists(CONFIG_RUNTIME_FILE):
            with open(CONFIG_RUNTIME_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            return jsonify({
                'success': False,
                'error': 'Configuration file not found'
            }), 500
        
        # Add descriptions
        config['options_descriptions'] = OPTIONS_DESCRIPTIONS
        
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config', methods=['POST'])
def save_config():
    """Save model configuration to runtime config"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Save to RUNTIME config file only
        with open(CONFIG_RUNTIME_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[CONFIG] Updated runtime: model={data.get('model')}, options={data.get('options')}", flush=True)
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config/reset', methods=['POST'])
def reset_config():
    """Reset configuration to defaults by copying config.json → config_runtime.json"""
    try:
        if not os.path.exists(CONFIG_DEFAULT_FILE):
            return jsonify({
                'success': False,
                'error': 'Default config file (config.json) not found'
            }), 500
        
        # Copy defaults from config.json to config_runtime.json
        import shutil
        shutil.copy2(CONFIG_DEFAULT_FILE, CONFIG_RUNTIME_FILE)
        
        # Read and return the reset config
        with open(CONFIG_RUNTIME_FILE, 'r', encoding='utf-8') as f:
            reset_config = json.load(f)
        
        print(f"[CONFIG] Reset to defaults from config.json", flush=True)
        
        return jsonify({
            'success': True,
            'config': reset_config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/clear', methods=['POST'])
def clear_conversation():
    """Delete conversation.txt to clear chat history"""
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            print(f"[CONVERSATION] Cleared conversation history", flush=True)
            message = 'Conversation history cleared'
        else:
            message = 'No conversation history to clear'
        
        return jsonify({
            'success': True,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
