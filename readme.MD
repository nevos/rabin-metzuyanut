# Listen.py - Voice to AI Chat

Hebrew voice-to-text transcription with Ollama AI integration.

## Installation

### 1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install ollama faster-whisper SpeechRecognition pyaudio
```

### 2. Install PyAudio dependencies (macOS):
```bash
brew install portaudio
```

### 3. Install and setup Ollama:
```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve

# Pull the required model (in a new terminal)
ollama pull llama3.1
```

## Testing Installation

Before running the main script, test that everything is set up correctly:

```bash
python test_setup.py
```

This will verify:
- ✓ All Python packages are installed
- ✓ Ollama service is running
- ✓ llama3.1 model is available
- ✓ Whisper model can load
- ✓ Microphone access works

## Usage

```bash
python listen.py
```

Speak in Hebrew when prompted, and the AI will respond to your input.

### Output

Each conversation is automatically saved to `conversation.txt` in UTF-8 format (with RTL support for Hebrew) with:
- Timestamp followed by "input:" on one line, then the input text on the next line
- Timestamp followed by "output:" on one line, then the output text on the next line
- Separator line between conversations

Example log entry:
```
08-02-26 14:30:45 input:
מה השעה?

08-02-26 14:30:47 output:
השעה היא 14:30.

==================================================

```