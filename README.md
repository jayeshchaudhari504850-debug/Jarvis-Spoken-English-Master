🤖 JARVIS AI OS v8.0
Advanced Spoken English Coach

JARVIS AI OS is a voice-based AI English conversation coach designed to help users practice spoken English through natural conversation.

It supports:

🎙️ Voice input with automatic speech/silence detection

🔊 Natural voice output using Edge TTS

🧠 Local AI through Ollama

☁️ Optional Claude API integration

🇮🇳 Indian English speech recognition

✍️ Real-time grammar and sentence correction

📈 Adaptive English difficulty

🗣️ Natural conversational practice

⌨️ Text/keyboard fallback mode

🔄 Automatic Ollama model detection and fallback

📴 Offline TTS fallback using pyttsx3

✨ Features
🎙️ Smart Voice Recording

JARVIS does not depend on PyAudio.

Microphone recording is handled using:

sounddevice
numpy


The recorder:

Waits for you to start speaking.

Detects your voice using an RMS threshold.

Continues recording while you speak.

Automatically stops after a short silence.

Has a maximum recording limit to prevent infinite recording.

This makes conversation feel more natural than using a fixed recording duration.

🧠 Two AI Brain Options

JARVIS supports two AI providers.

Option 1 — Ollama

Ollama provides local AI inference.

Advantages:

Free

Can run locally

No API key required

Your conversation can remain on your computer

Example:

JARVIS → Ollama → Local AI Model


The default model is:

llama3.2:1b


You can change it with:

JARVIS_MODEL

Option 2 — Anthropic Claude

JARVIS can also use the Anthropic API for stronger conversational reasoning.

Set:

JARVIS_BRAIN=anthropic


and provide:

ANTHROPIC_API_KEY


The API key should be stored as an environment variable.

Never hardcode your API key inside the Python file or commit it to Git.

🗣️ English Coaching

JARVIS is configured as a spoken English coach.

Its coaching behavior includes:

Grammar Correction

If your sentence contains an important mistake, JARVIS gives one short correction.

Example:

You:
Yesterday I go to market.

JARVIS:
Correction: say 'Yesterday I went to the market', not
'Yesterday I go to market'.


It then continues the conversation instead of turning the session into a grammar lecture.

Adaptive Difficulty

JARVIS starts with relatively simple English.

As the conversation becomes more fluent, it can gradually introduce:

Longer sentences

Better vocabulary

Useful phrases

Idioms

More natural spoken English

If the conversation becomes difficult, you can ask JARVIS to simplify it.

🇮🇳 Indian English Support

Speech recognition is configured for Indian English:

language="en-IN"


The default voice is:

en-IN-PrabhatNeural


You can change the voice using:

JARVIS_VOICE

🏗️ Project Architecture

The application consists of three major components.

                    ┌─────────────────────┐
                    │       JARVIS        │
                    │   Main Application  │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
         ┌──────▼──────┐               ┌──────▼──────┐
         │ SpeechEngine│               │   AI Brain  │
         └──────┬──────┘               └──────┬──────┘
                │                             │
        ┌───────┴────────┐             ┌──────┴─────────┐
        │                │             │                │
   Microphone         Speaker       Ollama          Claude API
   sounddevice        pygame        Local AI         Cloud AI
        │
   Google Speech
   Recognition

📋 Requirements

Recommended:

Python 3.11+

Working microphone

Working speaker/headphones

Internet connection for:

Google Speech Recognition

Edge TTS

Claude API

Ollama, if using the local AI brain

Python 3.14 may work with some dependencies, but if you encounter compatibility issues, Python 3.11 or 3.12 is generally the safer choice.

📦 Installation
1. Clone or download the project

Place the Python file in your project directory.

For example:

jarvis/
│
├── jarvis.py
└── README.md

2. Create a virtual environment
Windows
python -m venv .venv


Activate it:

.venv\Scripts\activate

macOS/Linux
python3 -m venv .venv


Activate it:

source .venv/bin/activate

3. Install dependencies

Install the required Python packages:

pip install numpy requests sounddevice SpeechRecognition edge-tts pygame rich pyttsx3


The application intentionally does not require PyAudio.

🧠 Ollama Setup

If you want to use the default local AI mode, install Ollama and make sure its server is running.

Then pull a model.

For the default configuration:

ollama pull llama3.2:1b


Start Ollama if it is not already running:

ollama serve


Then run JARVIS from another terminal.

Checking Installed Models

You can check your available models with:

ollama list


JARVIS also automatically checks Ollama using:

/api/tags


before starting the conversation.

If the configured model is unavailable but another model exists, JARVIS automatically falls back to an available model.

Example:

Model 'llama3.2:1b' isn't pulled.
Using 'qwen2.5:3b' instead for now.

🔑 Claude Setup

To use the Anthropic brain, set:

JARVIS_BRAIN=anthropic


and configure your API key.

Windows CMD
setx ANTHROPIC_API_KEY "your-api-key"


Open a new terminal after running setx.

PowerShell
$env:ANTHROPIC_API_KEY="your-api-key"

macOS/Linux
export ANTHROPIC_API_KEY="your-api-key"


You can also choose the model with:

JARVIS_ANTHROPIC_MODEL

⚙️ Configuration

JARVIS can be configured through environment variables.

Variable	Default	Purpose
JARVIS_BRAIN	ollama	Selects AI provider
JARVIS_OLLAMA_HOST	http://localhost:11434	Ollama server
JARVIS_MODEL	llama3.2:1b	Ollama model
JARVIS_ANTHROPIC_MODEL	configured in code	Claude model
ANTHROPIC_API_KEY	empty	Claude API key
JARVIS_VOICE	en-IN-PrabhatNeural	Edge TTS voice
🚀 Running JARVIS

Run:

python jarvis.py


You should see the JARVIS banner followed by a greeting.

JARVIS will say something similar to:

Hello Sir! I am your spoken English coach.
Let's practice - tell me, how was your day today?


Start speaking normally.

🎤 Voice Mode

In voice mode:

You speak
    ↓
Microphone
    ↓
sounddevice
    ↓
Silence Detection
    ↓
Google Speech Recognition
    ↓
AI Brain
    ↓
JARVIS Response
    ↓
Edge TTS
    ↓
Speaker


The microphone waits until you actually start talking.

After you stop speaking for approximately:

0.7 seconds


the recording ends.

⌨️ Text Mode

If a microphone is unavailable, JARVIS automatically falls back to text mode.

You can also switch manually by saying:

text mode


or:

type mode


Then type your messages in the terminal.

🛑 Stopping JARVIS

You can say:

stop

exit

quit

bye

goodbye


You can also press:

Ctrl + C


JARVIS handles the interrupt cleanly.

🗣️ Language Commands

JARVIS understands several conversational control commands.

English Only

You can say:

Talk in English


or:

English only


This enables strict English mode.

Hindi Explanation

You can say:

Hindi me samjha


or:

Hindi me bata


JARVIS will temporarily provide more Hindi support.

Easier English

You can say:

Easy karo

Simple bolo

Easy English


JARVIS will simplify the conversation.

Slow Down

You can say:

Slow down


or:

Slow karo

Return to Normal

You can say:

Normal mode


or:

Level up


to return to the default adaptive coaching behavior.

🔊 Voice Configuration

The default voice is:

en-IN-PrabhatNeural


To use another Edge TTS voice, set:

Windows CMD
setx JARVIS_VOICE "en-IN-PrabhatNeural"

PowerShell
$env:JARVIS_VOICE="en-IN-PrabhatNeural"

Linux/macOS
export JARVIS_VOICE="en-IN-PrabhatNeural"

🎚️ Audio Settings

The main audio parameters are defined near the top of the Python file.

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 500
SILENCE_HOLD_SECONDS = 0.7
MAX_RECORD_SECONDS = 20
PRE_SPEECH_TIMEOUT = 8

SAMPLE_RATE

Microphone sampling rate.

Default:

16000 Hz

SILENCE_THRESHOLD

Controls how much audio is required before JARVIS considers it speech.

If JARVIS starts recording because of background noise, this value may need to be increased.

If JARVIS does not detect your voice, it may need to be decreased.

SILENCE_HOLD_SECONDS

How long JARVIS waits after you stop speaking.

Default:

0.7 seconds


Increase it if JARVIS cuts you off too quickly.

MAX_RECORD_SECONDS

Maximum duration of one recording.

Default:

20 seconds

PRE_SPEECH_TIMEOUT

Maximum time JARVIS waits for you to start speaking.

Default:

8 seconds

🧩 Troubleshooting
❌ Ollama connection error

If you see:

Ollama not reachable at http://localhost:11434


make sure Ollama is running.

Try:

ollama serve


Then restart JARVIS.

❌ Model not found

If JARVIS says:

Model 'llama3.2:1b' isn't pulled


run:

ollama pull llama3.2:1b


Then restart the application.

❌ No microphone

If no microphone is available, JARVIS automatically starts in text mode.

Check available audio devices with:

import sounddevice as sd
print(sd.query_devices())


If necessary, select/configure the correct microphone device.

❌ Speech recognition does not understand you

The current recognizer uses:

language="en-IN"


Try speaking clearly and keep the microphone relatively close.

Speech recognition also requires an internet connection because the current implementation uses Google's recognition service.

❌ Edge TTS fails

JARVIS automatically retries Edge TTS.

If it still fails, it attempts to use:

pyttsx3


as an offline fallback.

If both fail, JARVIS continues in text-only output mode.

❌ No speaker/audio output

JARVIS can continue without audio output.

Check:

System volume

Default audio device

Headphones/speakers

pygame installation

You can reinstall pygame with:

pip install --upgrade pygame

🔐 Security

Do not put secrets directly into the Python source code.

For example, avoid:

ANTHROPIC_API_KEY = "sk-ant-xxxxxxxx"


Use an environment variable instead:

ANTHROPIC_API_KEY


If you use Git, add a .gitignore file.

Example:

.venv/
__pycache__/
*.pyc
jarvis_temp_voice.mp3
.env

📁 Recommended Project Structure
JARVIS/
│
├── jarvis.py
├── README.md
├── .gitignore
│
└── .venv/


If the project grows, you can later separate the application into:

JARVIS/
│
├── main.py
├── config.py
├── speech/
│   ├── input.py
│   └── output.py
├── brains/
│   ├── ollama.py
│   └── claude.py
├── prompts/
│   └── english_coach.txt
├── README.md
└── requirements.txt

📦 requirements.txt

You can create a requirements.txt containing:

numpy
requests
sounddevice
SpeechRecognition
edge-tts
pygame
rich
pyttsx3


Then install everything with:

pip install -r requirements.txt

⚡ Quick Start

For Ollama:

python -m venv .venv


Windows:

.venv\Scripts\activate


macOS/Linux:

source .venv/bin/activate


Install dependencies:

pip install -r requirements.txt


Pull the default model:

ollama pull llama3.2:1b


Start Ollama:

ollama serve


Run JARVIS:

python jarvis.py


Start speaking.

🎯 Design Goals

JARVIS is designed around four principles:

Natural Conversation
        +
Immediate Correction
        +
Adaptive Difficulty
        +
Fast Voice Interaction


The goal is not to make the user memorize grammar rules.

The goal is to create a conversational environment where the user can speak English repeatedly, receive small corrections, and gradually become more comfortable speaking naturally.

🛠️ Current Limitations

This version has a few practical limitations:

Speech recognition depends on Google's online recognition service.

Edge TTS requires internet access.

Small local Ollama models have limited reasoning and conversational capability.

The silence detector uses a fixed RMS threshold and may need adjustment in noisy environments.

Claude usage requires an Anthropic API key and may incur API costs.

pyttsx3 fallback voice quality depends on the voices installed on the operating system.

🔮 Possible Future Improvements

Potential future versions could add:

Wake-word detection

Conversation history saved to disk

User progress tracking

Pronunciation scoring

Speaking-speed analysis

Filler-word detection

Vocabulary progress

Daily English practice goals

Multiple English accents

Better voice activity detection

Fully offline speech recognition

Local speech-to-text models

GUI interface

Web dashboard

Session statistics

Automatic difficulty adjustment based on speaking performance

📜 License

Add your preferred license here.

For example:

MIT License

👨‍💻 Author

Jayesh

JARVIS AI OS — Spoken