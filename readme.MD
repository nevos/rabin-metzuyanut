# בית החינוך רבין מצויינות - AI Voice Assistant

Hebrew voice and text AI assistant with web interface. Ask questions in Hebrew and get structured, intelligent responses.

## ✨ Features

- 🎙️ **Voice Recording** - Record questions in Hebrew
- ⌨️ **Text Input** - Type questions directly
- 🤖 **Multiple AI Models** - Choose between Gemma2, Llama3.1, DeepSeek
- ⚙️ **Customizable Settings** - Adjust model parameters and behavior
- 💬 **Conversation History** - All chats saved and displayed
- 🇮🇱 **Full Hebrew Support** - RTL interface and Hebrew AI responses
- 📊 **Response Metrics** - See model settings and response times

---

## 🚀 Quick Start

### **Prerequisites**

- macOS (Apple Silicon or Intel)
- Python 3.9+
- Node.js 16+
- 8GB+ RAM recommended

### **1. Install Ollama & Model**

Run the automated setup script:

```bash
./setup_ollama.sh
```

This will:
- Install Ollama
- Download gemma2:9b model (5.4 GB)
- Start the Ollama service

### **2. Install Python Dependencies**

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install backend packages
cd backend
pip install -r requirements.txt
cd ..
```

### **3. Install React Dependencies**

```bash
cd react-app
npm install
cd ..
```

### **4. Install ffmpeg (for audio conversion)**

```bash
brew install ffmpeg
```

---

## 🎯 Running the Application

Start three services in separate terminals:

### **Terminal 1: Ollama Model Server**
```bash
ollama serve
```

### **Terminal 2: Flask Backend**
```bash
source .venv/bin/activate
cd backend
python server.py
```
Backend runs on: http://localhost:5001

### **Terminal 3: React Frontend**
```bash
cd react-app
npm start
```
Frontend opens at: http://localhost:3000

---

## 💻 Using the Application

1. **Open**: http://localhost:3000
2. **Choose input method**:
   - Click 🎙️ **Record** button to speak
   - Or type in the text field
3. **View responses** in the conversation history
4. **Adjust settings** in ⚙️ **הגדרות** tab

---

## ⚙️ Configuration

### **Settings Available:**

- **Model Selection**: Choose AI model (Gemma2, Llama3.1, DeepSeek)
- **Temperature**: Control creativity (0.1-1.0)
- **Top P**: Control word variety (0.5-1.0)
- **Top K**: Limit vocabulary choices (10-100)
- **Repeat Penalty**: Prevent repetition (1.0-2.0)
- **Max Length**: Response length (200-2000 tokens)
- **System Context**: Custom AI behavior instructions

Settings are saved to `config_runtime.json` and applied immediately.

---

## 📁 Project Structure

```
rabin/
├── backend/
│   ├── server.py           # Flask API server
│   └── requirements.txt    # Backend dependencies
├── react-app/              # React frontend
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   └── App.css        # Styling
│   └── package.json       # Frontend dependencies
├── process_audio.py        # Audio processing pipeline
├── process_text.py         # Text processing pipeline
├── config.json             # Default configuration (immutable)
├── config_runtime.json     # Active configuration (user-modified)
├── conversation.txt        # Chat history
├── requirements.txt        # Python dependencies
└── setup_ollama.sh        # Automated Ollama setup
```

---

## 🔧 Troubleshooting

### **Port 5000 in use (AirPlay)**
Backend uses port 5001 to avoid macOS AirPlay conflicts.

### **Model timeouts**
If responses timeout (40s limit), switch to a faster model:
- ✅ **gemma2:9b** - Fast (3-8s)
- ✅ **llama3.1** - Medium (5-12s)
- ⚠️ **deepseek-r1** - Slow (15-45s, may timeout)

### **Audio not working**
- Check browser microphone permissions
- Verify ffmpeg is installed: `ffmpeg -version`

### **Backend errors**
Check virtual environment is activated:
```bash
source .venv/bin/activate
```

---

## 🎨 Technology Stack

- **Frontend**: React 18, Modern CSS with gradients
- **Backend**: Flask (Python), REST API
- **AI**: Ollama (Gemma2:9b, Llama3.1, DeepSeek)
- **Speech**: faster-whisper (Whisper model)
- **Audio**: Browser MediaRecorder, ffmpeg

---

## 📝 Default Response Format

The AI responds in structured Hebrew format:

```
הגדרה קצרה:
[1-2 sentence definition]

הסבר:
[3 sentences of detailed explanation]
```

Customize this format in the Settings tab under "הקשר מערכת".

---

## 🔒 Privacy

- All processing happens **locally**
- Conversations stored in `conversation.txt`
- No data sent to external services (except Ollama models)
- User settings in `config_runtime.json` (not tracked in git)

---

## 📄 License

Educational project for Rabin Excellence Education House.

---

*Last Updated: February 8, 2026*