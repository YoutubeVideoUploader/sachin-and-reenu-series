import os
import json
import time
import math
import wave
import struct
from google import genai
from google.genai import types

def get_api_clients():
    keys = []
    if os.getenv("GEMINI_API_KEYS"):
        keys.extend([k.strip() for k in os.getenv("GEMINI_API_KEYS").split(",") if k.strip()])
    for var in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
        k = os.getenv(var)
        if k and k.strip() and k.strip() not in keys:
            keys.append(k.strip())
    if not keys:
        raise ValueError("At least one GEMINI_API_KEY environment variable is required")
    return [genai.Client(api_key=k) for k in keys]

SCRIPT_FILE = "current_episode.json"
AUDIO_DIR = "generated_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def create_silent_wav(file_path, duration=3.0, sample_rate=24000):
    """Fallback generator for empty audio so compilation never fails."""
    total_samples = int(sample_rate * duration)
    with wave.open(file_path, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b'\x00' * (total_samples * 2))
    print(f"  -> Created silent placeholder audio {file_path}")

def generate_voices():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
    
    scenes = ep_data.get("scenes", [])
    print(f"Generating {len(scenes)} voice lines for Episode {ep_data.get('episode_number')}...")
    
    clients = get_api_clients()
    client_idx = 0
    
    for sc in scenes:
        idx = sc["scene_index"]
        voice = sc.get("voice", "Kore")
        text = sc["dialogue_malayalam"]
        out_wav = os.path.join(AUDIO_DIR, f"speech_{idx}.wav")
        
        if os.path.exists(out_wav) and os.path.getsize(out_wav) > 1000:
            print(f"Skipping speech_{idx}.wav (already generated).")
            continue
            
        print(f"Synthesizing speech_{idx}.wav ({sc['speaker']} - {voice})...")
        synthesized = False
        
        # Try across available keys with backoff
        for attempt in range(len(clients) * 3):
            curr_client = clients[client_idx % len(clients)]
            active_key_idx = (client_idx % len(clients)) + 1
            try:
                config = types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice
                            )
                        )
                    )
                )
                res = curr_client.models.generate_content(
                    model="gemini-3.8-flash-tts",
                    contents=text,
                    config=config
                )
                audio_bytes = res.candidates[0].content.parts[0].inline_data.data
                with open(out_wav, "wb") as f:
                    f.write(audio_bytes)
                print(f"  -> Saved speech_{idx}.wav ({len(audio_bytes)} bytes) using key #{active_key_idx}")
                synthesized = True
                # Pacing between calls
                time.sleep(5.0)
                # Rotate key for load balancing
                client_idx += 1
                break
            except Exception as e:
                err_str = str(e)
                print(f"  -> Attempt {attempt+1} note on key #{active_key_idx}: {err_str[:120]}")
                # Rotate to next client immediately
                client_idx += 1
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print("     Rate limited on current key. Pausing 15s and rotating key...")
                    time.sleep(15.0)
                else:
                    time.sleep(4.0)
                    
        if not synthesized:
            print(f"  -> Warning: Falling back to silent WAV for speech_{idx}.wav to guarantee pipeline continuity.")
            create_silent_wav(out_wav, duration=3.5)

def generate_foley_and_score(duration=130, sample_rate=24000):
    # Ambient soundscape
    amb_path = os.path.join(AUDIO_DIR, "ambient.wav")
    if not os.path.exists(amb_path):
        import random
        total_samples = int(sample_rate * duration)
        samples = [0.0] * total_samples
        for i in range(total_samples):
            t = i / sample_rate
            hum = 0.04 * math.sin(2 * math.pi * 60 * t) + 0.02 * math.sin(2 * math.pi * 120 * t)
            noise = (random.random() * 2.0 - 1.0) * 0.025
            samples[i] = hum + noise
        
        # Lowpass filter
        val = 0.0
        filtered = [0.0] * total_samples
        for i in range(total_samples):
            val = val + 0.08 * (samples[i] - val)
            filtered[i] = val * 0.5
            
        with wave.open(amb_path, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            raw = b"".join(struct.pack('<h', int(max(-1.0, min(1.0, s)) * 32767)) for s in filtered)
            wav.writeframes(raw)
        print("Generated ambient soundscape.")

    # Romance Score
    bgm_path = os.path.join(AUDIO_DIR, "romance_score.wav")
    if not os.path.exists(bgm_path):
        total_samples = int(sample_rate * duration)
        samples = [0.0] * total_samples
        chords = [
            [146.83, 220.0, 293.66, 369.99, 440.0],
            [110.0, 164.81, 220.0, 277.18, 440.0],
            [123.47, 185.0, 246.94, 293.66, 369.99],
            [98.0, 146.83, 196.0, 246.94, 293.66]
        ]
        chord_len = 4.0
        num_chords = int(duration / chord_len) + 1
        for c_idx in range(num_chords):
            chord = chords[c_idx % len(chords)]
            c_start = int(c_idx * chord_len * sample_rate)
            for note in chord[:3]:
                for s in range(int(chord_len * sample_rate)):
                    idx = c_start + s
                    if idx < total_samples:
                        t = s / sample_rate
                        env = math.sin(math.pi * (s / (chord_len * sample_rate)))
                        samples[idx] += 0.07 * math.sin(2 * math.pi * note * t) * env
            sub_beat = chord_len / len(chord)
            for n_i, note in enumerate(chord):
                n_start = c_start + int(n_i * sub_beat * sample_rate)
                for s in range(int(1.8 * sample_rate)):
                    idx = n_start + s
                    if idx < total_samples:
                        t = s / sample_rate
                        env = math.exp(-t * 2.2)
                        samples[idx] += (0.16 * math.sin(2 * math.pi * note * t) + 0.05 * math.sin(2 * math.pi * note * 2 * t)) * env

        max_val = max(abs(s) for s in samples) or 1.0
        with wave.open(bgm_path, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            raw = b"".join(struct.pack('<h', int(max(-1.0, min(1.0, s / max_val * 0.40)) * 32767)) for s in samples)
            wav.writeframes(raw)
        print("Generated romance score.")

if __name__ == "__main__":
    generate_voices()
    generate_foley_and_score()
    print("All audio generation finished!")
