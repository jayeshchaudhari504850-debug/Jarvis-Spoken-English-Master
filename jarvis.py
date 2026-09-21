"""
=============================================================================
JARVIS AI OS v8.0 - GENERAL INTELLIGENCE CORE (STABLE)
-----------------------------------------------------------------------------
Architect: Custom AI Assistant for Jayesh (Sir)
What's fixed vs v7.0:
- REMOVED pyaudio dependency entirely. It was causing
  "module 'pyaudio' has no attribute '__version__'" on newer Python (3.14)
  and silently disabling the mic. Recording is now done directly with
  `sounddevice` (which you already had installed) + a simple, reliable
  silence-detector: it starts recording once you start talking and stops
  a beat after you go quiet - no pyaudio, no fixed 5-second guess.
- Ollama 404 fix: before chatting, it checks whether the configured model
  is actually pulled. If not, it tells you EXACTLY which command to run,
  and auto-falls-back to any model you do have available so you're not
  stuck.
- Ctrl+C now exits cleanly - no more ugly traceback on shutdown.
=============================================================================
"""

import os
import re
import sys
import time
import json
import asyncio
import requests
import numpy as np
import sounddevice as sd

import speech_recognition as sr
import edge_tts
import pygame

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align
from rich import box

# =============================================================================
# SYSTEM CONFIGURATION
# =============================================================================

# BRAIN_PROVIDER = "ollama" (free, fully local, but a 1-8B model has limited
# reasoning/coherence - that's a model-size limit, not a code bug) or
# "anthropic" (uses the real Claude API for genuinely sharp, instruction-
# following conversation - needs an ANTHROPIC_API_KEY and costs a small
# amount per request; set the key as an environment variable, never hardcode
# it in this file).
BRAIN_PROVIDER = os.environ.get("JARVIS_BRAIN", "ollama").lower()

OLLAMA_HOST = os.environ.get("JARVIS_OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("JARVIS_MODEL", "llama3.2:1b")

ANTHROPIC_MODEL = os.environ.get("JARVIS_ANTHROPIC_MODEL", "claude-sonnet-5")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

VOICE_MODEL = os.environ.get("JARVIS_VOICE", "en-IN-PrabhatNeural")

STOP_WORDS = {"stop", "exit", "quit", "bye", "goodbye", "alvida", "chalo bye"}
TEXT_MODE_WORDS = {"text mode", "type mode", "keyboard mode"}

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 500       # RMS level below which audio counts as "quiet"
SILENCE_HOLD_SECONDS = 0.7     # how long you must be quiet before we stop (was 1.2 - faster turn-taking)
MAX_RECORD_SECONDS = 20        # hard cap so it never records forever
PRE_SPEECH_TIMEOUT = 8          # how long to wait for you to start talking

SUPERNOVA_PROMPT = """
You are JARVIS, an advanced Spoken English Coach for Jayesh (Sir), an Indian
learner practicing spoken English through voice conversation.

CORE DIRECTIVES:
0. OBEY EXPLICIT INSTRUCTIONS FIRST, ALWAYS: If Sir asks you to change
   difficulty, topic, or briefly explain something in Hindi, do it
   immediately and keep it up until he says otherwise. This overrides
   directive 1 below only for the specific thing he asked.
1. ENGLISH BY DEFAULT: Reply in simple, correct spoken English at all times,
   unless Sir explicitly asks for Hindi/Hinglish. You may give a one-word
   Hindi meaning in brackets ONLY when teaching a genuinely new/hard word,
   e.g. "That's called 'reluctant' (Hindi: anichchhuk)."
2. GENTLE, IMMEDIATE CORRECTION: If Sir's last message had a grammar,
   word-choice, or sentence-structure mistake, start your reply with ONE
   short correction line in this exact style:
   "Correction: say '<fixed sentence>', not '<what he said>'."
   Only correct ONE mistake per turn (the most important one) - don't list
   several, don't nitpick minor things, and skip this line entirely if his
   sentence was already correct. Never be harsh or make him feel bad.
3. REAL CONVERSATION, NOT A LECTURE: After any correction, continue as a
   natural conversation on whatever topic Sir raised - react to what he
   actually said, then ask ONE relevant follow-up question to keep him
   talking. Never randomly change topic or recite unrelated facts.
4. TEACH ONE NEW THING AT A TIME: Every few turns, naturally introduce one
   useful word, phrase, or idiom relevant to the conversation, with a
   one-line meaning and a tiny example - don't turn it into a vocabulary
   dump.
5. ADAPTIVE DIFFICULTY: Start with short, simple sentences. As Sir responds
   fluently and correctly across several turns, gradually use slightly
   longer sentences and richer vocabulary. If he struggles or asks you to
   slow down, simplify immediately.
6. KEEP IT SPOKEN-FRIENDLY: Since this is spoken aloud, keep replies short
   (2-4 sentences max, including any correction), use natural spoken
   rhythm, and avoid anything that only makes sense written (no bullet
   symbols, no markdown).
7. HONESTY: If unsure about something Sir asks, say so plainly instead of
   guessing confidently.
"""

console = Console()

# =============================================================================
# UI HELPERS
# =============================================================================

def ui_banner() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = (
        "[bold cyan]"
        "  ██████╗  █████╗ ██████╗ ██╗   ██╗██╗███████╗\n"
        "  ██╔══██╗██╔══██╗██╔══██╗██║   ██║██║██╔════╝\n"
        "  ██████╔╝███████║██████╔╝██║   ██║██║███████╗\n"
        "  ██╔══██╗██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║\n"
        "  ██║  ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║\n"
        "  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝\n"
        "  [SPOKEN ENGLISH COACH v9.0 - ADVANCED CONVERSATION PRACTICE]"
        "[/bold cyan]"
    )
    console.print(Align.center(banner))
    console.rule(style="cyan")


def ui_jarvis_say(text: str) -> None:
    console.print(Panel(text, title="🤖 JARVIS", border_style="cyan", box=box.ROUNDED))


def ui_user_said(text: str) -> None:
    console.print(Panel(text, title="🗣️ YOU (Sir)", border_style="green", box=box.ROUNDED))


def ui_system(text: str, style: str = "dim") -> None:
    console.print(f"[{style}]{text}[/{style}]")

# =============================================================================
# AUDIO INPUT (pyaudio-free) / OUTPUT SUBSYSTEM
# =============================================================================

class SpeechEngine:
    def __init__(self, voice: str = VOICE_MODEL):
        self.voice = voice
        self.recognizer = sr.Recognizer()

        # Quick check that a usable input device exists (no pyaudio needed).
        self.mic_available = True
        try:
            sd.check_input_settings(samplerate=SAMPLE_RATE, channels=1)
        except Exception as err:
            self.mic_available = False
            ui_system(f"No usable microphone found ({err}). Falling back to text mode.", style="bold yellow")

        try:
            pygame.mixer.init()
            self.audio_available = True
        except Exception as err:
            self.audio_available = False
            ui_system(f"No audio output device detected ({err}). Replies will be text-only.", style="bold yellow")

        self.offline_engine = None
        try:
            import pyttsx3
            self.offline_engine = pyttsx3.init()
        except Exception:
            self.offline_engine = None

    # ---- Recording (sounddevice, no pyaudio) --------------------------------

    def _record_until_silence(self) -> np.ndarray | None:
        """
        Waits for speech to start, records it, and auto-stops once you've
        been quiet for SILENCE_HOLD_SECONDS. Returns int16 mono samples,
        or None if nothing was said within PRE_SPEECH_TIMEOUT.
        """
        block_duration = 0.1  # seconds per chunk we analyze
        block_size = int(SAMPLE_RATE * block_duration)

        frames = []
        started = False
        silence_run = 0.0
        elapsed_waiting = 0.0
        elapsed_recording = 0.0

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=block_size) as stream:
            while True:
                block, _ = stream.read(block_size)
                rms = float(np.sqrt(np.mean(block.astype(np.float32) ** 2)))

                if not started:
                    if rms > SILENCE_THRESHOLD:
                        started = True
                        frames.append(block.copy())
                    else:
                        elapsed_waiting += block_duration
                        if elapsed_waiting >= PRE_SPEECH_TIMEOUT:
                            return None
                    continue

                frames.append(block.copy())
                elapsed_recording += block_duration

                if rms < SILENCE_THRESHOLD:
                    silence_run += block_duration
                    if silence_run >= SILENCE_HOLD_SECONDS:
                        break
                else:
                    silence_run = 0.0

                if elapsed_recording >= MAX_RECORD_SECONDS:
                    break

        if not frames:
            return None
        return np.concatenate(frames, axis=0)

    def listen(self) -> str | None:
        if not self.mic_available:
            return None

        try:
            with Progress(
                SpinnerColumn(style="cyan"),
                TextColumn("[cyan]Listening... (boliye Sir)[/cyan]"),
                console=console,
                transient=True,
            ) as bar:
                bar.add_task("listening", total=None)
                samples = self._record_until_silence()

            if samples is None:
                return None

            audio_data = sr.AudioData(samples.tobytes(), SAMPLE_RATE, 2)
            text = self.recognizer.recognize_google(audio_data, language="en-IN").strip()
            if text:
                ui_user_said(text)
                return text
            return None

        except sr.UnknownValueError:
            ui_system("Samajh nahi aaya, phir se boliye please.", style="yellow")
            return None
        except Exception as err:
            ui_system(f"Mic Error: {err}", style="red")
            return None

    # ---- Speaking (edge-tts with offline fallback) --------------------------

    async def _async_generate_audio(self, text: str, file_path: str) -> None:
        tts = edge_tts.Communicate(text, self.voice)
        await tts.save(file_path)

    def _speak_offline(self, text: str) -> bool:
        if not self.offline_engine:
            return False
        try:
            self.offline_engine.say(text)
            self.offline_engine.runAndWait()
            return True
        except Exception as err:
            ui_system(f"Offline voice also failed: {err}", style="red")
            return False

    def speak(self, text: str) -> None:
        ui_jarvis_say(text)

        if not self.audio_available:
            return

        clean_text = re.sub(r"\[.*?\]", "", text)
        clean_text = re.sub(r"[*_~`#]", "", clean_text).strip()
        if not clean_text:
            return

        temp_audio_file = "jarvis_temp_voice.mp3"
        last_err = None

        for _ in range(2):
            try:
                asyncio.run(self._async_generate_audio(clean_text, temp_audio_file))
                if not os.path.exists(temp_audio_file) or os.path.getsize(temp_audio_file) == 0:
                    raise RuntimeError("No audio was received from edge-tts.")

                pygame.mixer.music.load(temp_audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                pygame.mixer.music.unload()
                os.remove(temp_audio_file)
                return
            except (KeyboardInterrupt, asyncio.CancelledError):
                raise
            except Exception as err:
                last_err = err
                if os.path.exists(temp_audio_file):
                    try:
                        os.remove(temp_audio_file)
                    except OSError:
                        pass
                time.sleep(0.3)

        ui_system(f"Online voice failed after retries ({last_err}). Trying offline voice...", style="yellow")
        if not self._speak_offline(clean_text):
            ui_system("Voice output unavailable this turn - continuing in text only.", style="red")

# =============================================================================
# SHARED LANGUAGE-LOCK MIXIN (used by both local and Claude brains)
# =============================================================================

class LanguageLockMixin:
    def _init_language_lock(self):
        self.language_lock = None

    def _check_language_switch(self, user_text: str) -> None:
        t = user_text.lower()
        if any(p in t for p in ["talk in english", "speak in english", "english me baat", "only english", "english only", "strict english"]):
            self.language_lock = "Strict mode: reply in English ONLY, no Hindi words or brackets at all, until Sir says otherwise."
        elif any(p in t for p in ["hindi me samjha", "hindi me bata", "hindi mein explain", "matlab kya"]):
            self.language_lock = "Sir wants the current point explained with a bit more Hindi support - explain simply, mixing in Hindi where it helps understanding, then go back to English coaching after."
        elif any(p in t for p in ["easy karo", "slow karo", "simple bolo", "easy english", "slow down"]):
            self.language_lock = "Sir wants it easier - use very short, simple sentences and basic vocabulary until he asks to level up again."
        elif any(p in t for p in ["normal mode", "default mode", "wapas normal", "level up", "harder karo"]):
            self.language_lock = None  # back to default adaptive coaching

    def _build_system_prompt(self) -> str:
        system_prompt = SUPERNOVA_PROMPT
        if self.language_lock:
            system_prompt += f"\n\nCURRENT OVERRIDE (obey this over everything else): {self.language_lock}"
        return system_prompt

# =============================================================================
# AI BRAIN - OPTION A: CLAUDE API (real reasoning, needs ANTHROPIC_API_KEY)
# =============================================================================

class ClaudeCore(LanguageLockMixin):
    def __init__(self, model: str = ANTHROPIC_MODEL, api_key: str = ANTHROPIC_API_KEY):
        self.model = model
        self.api_key = api_key
        self.history = []
        self._init_language_lock()
        self.online = bool(api_key)
        if not self.online:
            ui_system(
                "WARNING: ANTHROPIC_API_KEY not set. Set it as an environment "
                "variable to use the Claude brain, e.g.:\n"
                "  setx ANTHROPIC_API_KEY \"your-key-here\"   (Windows, new terminal after)\n"
                "  export ANTHROPIC_API_KEY=\"your-key-here\" (Mac/Linux)",
                style="bold red",
            )
        else:
            ui_system(f"Claude brain connected. Using model: {self.model}", style="green")

    def chat(self, user_text: str) -> str:
        if not self.online:
            return "Arey Sir, ANTHROPIC_API_KEY set nahi hai, isliye Claude brain use nahi ho sakta abhi."

        self._check_language_switch(user_text)
        self.history.append({"role": "user", "content": user_text})
        trimmed_history = self.history[-20:]

        try:
            res = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 500,
                    "system": self._build_system_prompt(),
                    "messages": trimmed_history,
                },
                timeout=60,
            )
            res.raise_for_status()
            data = res.json()
            response_text = "".join(
                block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
            ).strip()
            self.history.append({"role": "assistant", "content": response_text})
            return response_text or "Sir, kuch samajh nahi aaya reply mein, phir se try karo."
        except Exception as err:
            return f"Arey Sir, Claude brain se connect nahi ho paya ({err}). Phir se try karo."

    def chat_stream(self, user_text: str):
        """Claude API is already fast enough single-shot, so this just wraps
        chat() in the same generator interface main() expects."""
        yield self.chat(user_text)

# =============================================================================
# AI BRAIN - OPTION B: LOCAL OLLAMA (free, fully offline, weaker reasoning)
# =============================================================================

class SupernovaCore(LanguageLockMixin):
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host
        self.model = model
        self.history = []
        self._init_language_lock()
        self.online = self._resolve_model()

    def _resolve_model(self) -> bool:
        """Confirms the model is actually pulled; falls back to whatever IS
        available and tells the user how to get the one they asked for."""
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=5)
            res.raise_for_status()
            available = [m["name"] for m in res.json().get("models", [])]
        except Exception as err:
            ui_system(
                f"WARNING: Ollama not reachable at {self.host} ({err}). "
                "Run 'ollama serve' in another terminal, then restart this script.",
                style="bold red",
            )
            return False

        if not available:
            ui_system(
                f"WARNING: Ollama is running but no models are pulled. "
                f"Run 'ollama pull {self.model}' then restart.",
                style="bold red",
            )
            return False

        if self.model in available:
            ui_system(f"Ollama connected. Using model: {self.model}", style="green")
            return True

        fallback = available[0]
        ui_system(
            f"Model '{self.model}' isn't pulled (run 'ollama pull {self.model}' to get it). "
            f"Using '{fallback}' instead for now.",
            style="bold yellow",
        )
        self.model = fallback
        return True

    def chat(self, user_text: str) -> str:
        """Non-streaming (kept for compatibility). Prefer chat_stream()."""
        return "".join(self.chat_stream(user_text))

    def chat_stream(self, user_text: str):
        """Yields sentences as soon as each one is complete, instead of
        waiting for the whole reply - this is what makes replies feel fast:
        JARVIS starts speaking sentence 1 while sentence 2 is still being
        generated, rather than waiting for the full 100-150 tokens."""
        self._check_language_switch(user_text)
        self.history.append({"role": "user", "content": user_text})
        trimmed_history = self.history[-12:]
        messages = [{"role": "system", "content": self._build_system_prompt()}] + trimmed_history

        full_reply = ""
        buffer = ""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {"num_predict": 150, "temperature": 0.6},
            }
            with requests.post(f"{self.host}/api/chat", json=payload, timeout=120, stream=True) as res:
                res.raise_for_status()
                for line in res.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        buffer += token
                        full_reply += token
                        # Flush on sentence-ending punctuation so we can start
                        # speaking without waiting for the rest of the reply.
                        while True:
                            match = re.search(r'[.!?](\s|$)', buffer)
                            if not match:
                                break
                            end = match.end()
                            sentence = buffer[:end].strip()
                            buffer = buffer[end:]
                            if sentence:
                                yield sentence
                    if chunk.get("done"):
                        break

            if buffer.strip():
                yield buffer.strip()

            if full_reply.strip():
                self.history.append({"role": "assistant", "content": full_reply.strip()})
            else:
                yield "Sir, kuch reply nahi mila, phir se try karo."

        except requests.exceptions.HTTPError as err:
            yield f"Arey Sir, model '{self.model}' ka error aaya ({err}). Check karo ki ye pull hua hai."
        except Exception as err:
            yield f"Arey Sir, brain se connect nahi ho paya ({err}). Phir se try karo."

# =============================================================================
# MAIN EXECUTION ROUTINE
# =============================================================================

def main():
    ui_banner()

    speech = SpeechEngine()

    if BRAIN_PROVIDER == "anthropic":
        ai = ClaudeCore()
    else:
        ai = SupernovaCore()

    voice_mode = speech.mic_available
    if not voice_mode:
        ui_system("Starting in TEXT mode (no mic found).", style="bold yellow")

    speech.speak(
        "Hello Sir! I am your spoken English coach. Let's practice - "
        "tell me, how was your day today?"
    )

    try:
        while True:
            if voice_mode:
                user_input = speech.listen()
                if user_input is None:
                    continue
            else:
                try:
                    user_input = console.input("[bold green]You: [/bold green]").strip()
                except EOFError:
                    break
                if not user_input:
                    continue

            lowered = user_input.lower().strip()

            if lowered in STOP_WORDS:
                break
            if lowered in TEXT_MODE_WORDS:
                voice_mode = False
                ui_system("Switched to text mode.", style="yellow")
                continue

            for sentence in ai.chat_stream(user_input):
                speech.speak(sentence)

    except KeyboardInterrupt:
        pass

    speech.speak("Sahi hai Sir! Milte hain phir, take care!")


if __name__ == "__main__":
    main()