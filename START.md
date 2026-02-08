# How to Start the Voice Assistant App

## Prerequisites

1. Make sure Ollama is running:
```bash
ollama serve
```

## Start the Backend (Flask API)

Open a terminal and run:

```bash
cd backend
pip install -r requirements.txt
python server.py
```

The backend will run on `http://localhost:5000`

## Start the Frontend (React App)

Open another terminal and run:

```bash
cd react-app
npm install
npm start
```

The app will open at `http://localhost:3000`

## How to Use

1. Click the **"🎙️ Start Recording"** button
2. Speak in Hebrew when prompted
3. Wait for the AI response
4. The conversation will appear below the button
5. Click again to continue the conversation

## Architecture

- **Frontend**: React app with recording button and conversation display
- **Backend**: Flask API that triggers `listen2_single.py`
- **Voice Processing**: Uses `listen2_single.py` for speech-to-text and AI chat
- **Storage**: Conversation saved to `conversation_log.MD`

## Troubleshooting

- **Backend not connecting**: Make sure Flask server is running on port 5000
- **Ollama errors**: Ensure `ollama serve` is running
- **Microphone not working**: Check browser permissions for microphone access
