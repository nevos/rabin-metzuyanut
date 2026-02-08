# 1. התקן Ollama
brew install ollama

# 2. התחל Ollama service
ollama serve

# 3. הורד מודל gemma2:9b model (5.4 GB)
ollama pull gemma2:9b

# 4. בדוק שזה עובד it works
echo "🧪 Testing model..."
ollama run gemma2:9b "תגיד שלום"





