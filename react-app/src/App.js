import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [error, setError] = useState('');
  const [recordingTimer, setRecordingTimer] = useState(0);
  const [textInput, setTextInput] = useState('');
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'settings'
  const [models, setModels] = useState([]);
  const [config, setConfig] = useState(null);
  const [tempConfig, setTempConfig] = useState(null);
  const conversationsEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Load conversations function
  const loadConversations = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:5001/api/conversation');
      const data = await response.json();
      if (data.success) {
        setConversations(data.entries);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  }, []);

  // Load models
  const loadModels = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:5001/api/models');
      const data = await response.json();
      if (data.success) {
        setModels(data.models);
      }
    } catch (err) {
      console.error('Failed to load models:', err);
    }
  }, []);

  // Load config
  const loadConfig = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:5001/api/config');
      const data = await response.json();
      if (data.success) {
        setConfig(data.config);
        setTempConfig(data.config);
      }
    } catch (err) {
      console.error('Failed to load config:', err);
    }
  }, []);

  // Save config
  const saveConfig = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tempConfig),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setConfig(tempConfig);
        alert('✅ הגדרות נשמרו בהצלחה!');
      } else {
        alert('❌ שגיאה בשמירת הגדרות');
      }
    } catch (err) {
      console.error('Failed to save config:', err);
      alert('❌ שגיאה בשמירת הגדרות');
    }
  };

  // Reset to defaults
  const resetToDefaults = async () => {
    if (!window.confirm('האם אתה בטוח שברצונך לאפס את כל ההגדרות לברירת המחדל?')) {
      return;
    }
    
    try {
      const response = await fetch('http://localhost:5001/api/config/reset', {
        method: 'POST',
      });
      
      const data = await response.json();
      
      if (data.success) {
        setConfig(data.config);
        setTempConfig(data.config);
        alert('✅ ההגדרות אופסו לברירת המחדל!');
      } else {
        alert('❌ שגיאה באיפוס הגדרות');
      }
    } catch (err) {
      console.error('Failed to reset config:', err);
      alert('❌ שגיאה באיפוס הגדרות');
    }
  };

  // Clear conversation history
  const clearConversation = async () => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק את כל היסטוריית השיחות? פעולה זו אינה הפיכה!')) {
      return;
    }
    
    try {
      const response = await fetch('http://localhost:5001/api/conversation/clear', {
        method: 'POST',
      });
      
      const data = await response.json();
      
      if (data.success) {
        setConversations([]);
        alert('✅ היסטוריית השיחות נמחקה בהצלחה!');
      } else {
        alert('❌ שגיאה במחיקת היסטוריה');
      }
    } catch (err) {
      console.error('Failed to clear conversation:', err);
      alert('❌ שגיאה במחיקת היסטוריה');
    }
  };

  // Auto-scroll to bottom when conversations update (only after new message)
  useEffect(() => {
    if (conversations.length > 0) {
      // Use setTimeout to ensure DOM has updated
      setTimeout(() => {
        conversationsEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }, 100);
    }
  }, [conversations.length]); // Only trigger when length changes (new conversation added)

  // Recording timer
  useEffect(() => {
    let interval;
    if (isRecording && !isProcessing) {
      interval = setInterval(() => {
        setRecordingTimer(prev => prev + 1);
      }, 1000);
    } else {
      setRecordingTimer(0);
    }
    return () => clearInterval(interval);
  }, [isRecording, isProcessing]);

  // Load conversation log on mount and periodically (only when processing)
  useEffect(() => {
    loadConversations();
    let interval;
    if (isProcessing) {
      interval = setInterval(loadConversations, 1000); // Check every second while processing
    } else {
      interval = setInterval(loadConversations, 3000); // Check less frequently when idle
    }
    return () => clearInterval(interval);
  }, [isProcessing, loadConversations]);

  // Load models and config on mount
  useEffect(() => {
    loadModels();
    loadConfig();
  }, [loadModels, loadConfig]);

  const handleRecordToggle = async () => {
    if (!isRecording) {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
        setError('');
      } catch (err) {
        setError('Microphone access denied: ' + err.message);
      }
    } else {
      // Stop recording and process
      const mediaRecorder = mediaRecorderRef.current;
      
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        setIsRecording(false);
        setIsProcessing(true);

        mediaRecorder.onstop = async () => {
          // Stop all tracks
          mediaRecorder.stream.getTracks().forEach(track => track.stop());

          // Create audio blob
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          
          try {
            // Send audio to backend
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            const response = await fetch('http://localhost:5001/api/record-audio', {
              method: 'POST',
              body: formData,
            });

            const data = await response.json();

            if (data.success) {
              await loadConversations();
            } else {
              setError(data.error || 'Failed to process recording');
            }
          } catch (err) {
            setError('Failed to connect to server: ' + err.message);
          } finally {
            setIsProcessing(false);
          }
        };
      }
    }
  };

  const handleTextSubmit = async (e) => {
    e.preventDefault();
    
    if (!textInput.trim()) {
      return;
    }

    setIsProcessing(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:5001/api/text-input', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: textInput.trim() }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setTextInput('');
        await loadConversations();
      } else {
        setError(data.error || 'Failed to process text');
      }
    } catch (err) {
      setError('Failed to connect to server: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>בית החינוך רבין מצויינות</h1>
          <div className="tabs">
            <button 
              className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              💬 צ'אט
            </button>
            <button 
              className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              ⚙️ הגדרות
            </button>
          </div>
        </div>
      </header>

      {activeTab === 'settings' && tempConfig && config && (
        <div className="settings-panel">
          <h2>הגדרות מודל AI</h2>
          
          <div className="settings-grid">
          <div className="setting-group">
            <label>מודל:</label>
            <select 
              value={tempConfig.model} 
              onChange={(e) => setTempConfig({...tempConfig, model: e.target.value})}
              className="model-select"
            >
              {models.length === 0 ? (
                <option>טוען מודלים...</option>
              ) : (
                models.map(model => (
                  <option key={model.name} value={model.name}>
                    {model.name}
                  </option>
                ))
              )}
            </select>
            {models.find(m => m.name === tempConfig.model) && (
              <p className="setting-description">
                {models.find(m => m.name === tempConfig.model).description}
              </p>
            )}
          </div>

          <div className="setting-group">
            <label>
              טמפרטורה: {tempConfig.options.temperature}
            </label>
            <input 
              type="range" 
              min="0" 
              max="1" 
              step="0.1" 
              value={tempConfig.options.temperature}
              onChange={(e) => setTempConfig({
                ...tempConfig, 
                options: {...tempConfig.options, temperature: parseFloat(e.target.value)}
              })}
            />
            <p className="setting-description">{config.options_descriptions?.temperature || 'טמפרטורה - שולטת ביצירתיות'}</p>
          </div>

          <div className="setting-group">
            <label>
              דגימה גרעינית (top_p): {tempConfig.options.top_p}
            </label>
            <input 
              type="range" 
              min="0" 
              max="1" 
              step="0.05" 
              value={tempConfig.options.top_p}
              onChange={(e) => setTempConfig({
                ...tempConfig, 
                options: {...tempConfig.options, top_p: parseFloat(e.target.value)}
              })}
            />
            <p className="setting-description">{config.options_descriptions?.top_p || 'דגימה גרעינית'}</p>
          </div>

          <div className="setting-group">
            <label>
              מילים מועמדות (top_k): {tempConfig.options.top_k}
            </label>
            <input 
              type="range" 
              min="10" 
              max="100" 
              step="5" 
              value={tempConfig.options.top_k}
              onChange={(e) => setTempConfig({
                ...tempConfig, 
                options: {...tempConfig.options, top_k: parseInt(e.target.value)}
              })}
            />
            <p className="setting-description">{config.options_descriptions?.top_k || 'מספר מילים מועמדות'}</p>
          </div>

          <div className="setting-group">
            <label>
              עונש חזרות (repeat_penalty): {tempConfig.options.repeat_penalty}
            </label>
            <input 
              type="range" 
              min="1" 
              max="2" 
              step="0.1" 
              value={tempConfig.options.repeat_penalty}
              onChange={(e) => setTempConfig({
                ...tempConfig, 
                options: {...tempConfig.options, repeat_penalty: parseFloat(e.target.value)}
              })}
            />
            <p className="setting-description">{config.options_descriptions?.repeat_penalty || 'עונש על חזרות'}</p>
          </div>

          <div className="setting-group">
            <label>
              מילים מקסימלי (num_predict): {tempConfig.options.num_predict}
            </label>
            <input 
              type="range" 
              min="200" 
              max="2000" 
              step="100" 
              value={tempConfig.options.num_predict}
              onChange={(e) => setTempConfig({
                ...tempConfig, 
                options: {...tempConfig.options, num_predict: parseInt(e.target.value)}
              })}
            />
            <p className="setting-description">{config.options_descriptions?.num_predict || 'מספר מילים מקסימלי'}</p>
          </div>
          </div>

          <div className="context-section">
            <h3>הקשר מערכת (System Context)</h3>
            <textarea
              value={tempConfig.context || ''}
              onChange={(e) => setTempConfig({...tempConfig, context: e.target.value})}
              className="context-textarea"
              placeholder="הזן הנחיות למערכת AI..."
              rows="15"
            />
            <p className="setting-description">
              זהו ההקשר שנשלח למודל AI בכל שיחה. הוא מגדיר את התנהגות המודל, סגנון התשובות והפורמט.
            </p>
          </div>

          <div className="settings-actions">
            <button onClick={saveConfig} className="save-button">💾 שמור הגדרות</button>
            <button onClick={resetToDefaults} className="reset-button">🔄 איפוס לברירת מחדל</button>
            <button onClick={clearConversation} className="clear-button">🗑️ מחק שיחות</button>
            <button onClick={() => setActiveTab('chat')} className="cancel-button">↩️ חזור לצ'אט</button>
          </div>
        </div>
      )}

      {activeTab === 'chat' && (
      <main className="App-main">
        <div className="top-section">
          <div className="input-section">
            <button
              onClick={handleRecordToggle}
              disabled={isProcessing}
              className={`record-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
            >
              {isProcessing ? (
                <>
                  <span className="pulse"></span>
                  Processing...
                </>
              ) : isRecording ? (
                <>
                  <span className="pulse"></span>
                  🛑 {recordingTimer}s
                </>
              ) : (
                <>
                  🎙️ Record
                </>
              )}
            </button>

            <div className="divider">
              <span>או</span>
            </div>

            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !isProcessing && textInput.trim()) {
                  handleTextSubmit(e);
                }
              }}
              placeholder="הקלד כאן..."
              className="text-input"
              disabled={isProcessing}
            />
            
            <button 
              onClick={handleTextSubmit}
              className="send-button"
              disabled={isProcessing || !textInput.trim()}
            >
              💬
            </button>

            {error && <div className="error-message">{error}</div>}
          </div>
        </div>

        <div className="conversations">
          <h2>היסטוריית שיחה</h2>
          <div className="conversations-scroll">
            {conversations.length === 0 ? (
              <p className="no-conversations">אין שיחות עדיין. לחץ על כפתור ההקלטה או הקלד טקסט כדי להתחיל!</p>
            ) : (
              <>
                {conversations.map((conv, index) => (
                  <div key={index} className="conversation-item">
                    <div className="input-section">
                      <div className="label">
                        <div className="label-right">
                          <span className="icon">👤</span>
                        </div>
                        <div className="label-left">
                          <span className="timestamp">{conv.input_timestamp}</span>
                        </div>
                      </div>
                      <div className="content">{conv.input}</div>
                    </div>
                    <div className="output-section">
                      <div className="label">
                        <div className="label-right">
                          <span className="icon">🤖</span>
                        </div>
                        <div className="label-left">
                          <span className="timestamp">{conv.output_timestamp}</span>
                        </div>
                      </div>
                      <div className="output-with-config">
                        {conv.config && (
                          <div className="config-badge" title={conv.config}>
                            {conv.config.split('|').map((item, i) => (
                              <div key={i} className="config-item">{item.trim()}</div>
                            ))}
                            {conv.response_time && (
                              <div className="config-item time-item">⏱️ {conv.response_time}</div>
                            )}
                          </div>
                        )}
                        <div className="content">{conv.output}</div>
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={conversationsEndRef} />
              </>
            )}
          </div>
        </div>
      </main>
      )}
    </div>
  );
}

export default App;
