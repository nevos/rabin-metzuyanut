#!/usr/bin/env python3
"""
Test script to verify all dependencies for listen.py are properly installed
"""

import sys

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing package imports...")
    
    try:
        import ollama
        print("✓ ollama imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ollama: {e}")
        return False
    
    try:
        from faster_whisper import WhisperModel
        print("✓ faster_whisper imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import faster_whisper: {e}")
        return False
    
    try:
        import speech_recognition as sr
        print("✓ speech_recognition imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import speech_recognition: {e}")
        return False
    
    try:
        import pyaudio
        print("✓ pyaudio imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pyaudio: {e}")
        return False
    
    return True

def test_ollama_connection():
    """Test if Ollama service is running and llama3.1 model is available"""
    print("\nTesting Ollama connection...")
    
    try:
        import ollama
        
        # Try to list available models
        models = ollama.list()
        print("✓ Ollama service is running")
        
        # Check if llama3.1 is available
        # The models response structure has 'models' key with list of model dicts
        if 'models' in models and models['models']:
            model_names = []
            for model in models['models']:
                # Handle different possible keys (name, model, etc.)
                name = model.get('name', model.get('model', ''))
                model_names.append(name)
            
            if any('llama3.1' in name for name in model_names):
                print("✓ llama3.1 model is available")
                return True
            else:
                print("✗ llama3.1 model not found")
                print(f"  Available models: {model_names}")
                print("  Run: ollama pull llama3.1")
                return False
        else:
            print("✗ No models found")
            print("  Run: ollama pull llama3.1")
            return False
            
    except Exception as e:
        print(f"✗ Failed to connect to Ollama: {e}")
        print("  Make sure Ollama is running: ollama serve")
        return False

def test_whisper_model():
    """Test if Whisper model can be loaded"""
    print("\nTesting Whisper model loading...")
    
    try:
        from faster_whisper import WhisperModel
        print("  Loading base model (this may take a moment on first run)...")
        model = WhisperModel("base", device="cpu", compute_type="int8")
        print("✓ Whisper model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to load Whisper model: {e}")
        return False

def test_microphone():
    """Test if microphone is accessible"""
    print("\nTesting microphone access...")
    
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        
        # Try to list microphones
        mic_list = sr.Microphone.list_microphone_names()
        if mic_list:
            print(f"✓ Found {len(mic_list)} microphone(s)")
            print(f"  Default microphone: {mic_list[0]}")
        else:
            print("✗ No microphones found")
            return False
        
        # Try to initialize microphone
        with sr.Microphone() as source:
            print("✓ Microphone initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to access microphone: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing listen.py dependencies")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Package Imports", test_imports()))
    results.append(("Ollama Connection", test_ollama_connection()))
    results.append(("Whisper Model", test_whisper_model()))
    results.append(("Microphone Access", test_microphone()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to run listen.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before running listen.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
