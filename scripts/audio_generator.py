import os
import json
import time
import math
import wave
import struct
import asyncio
import subprocess
import edge_tts
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

async def synthesize_edge_tts(text, speaker, out_wav):
    """Fallback high quality native Kerala Malayalam neural voice."""
    if speaker == "Sachin":
        voice, pitch, rate = "ml-IN-MidhunNeural", "-3Hz", "-2%"
    elif speaker == "Amal":
        voice, pitch, rate = "ml-IN-MidhunNeural", "+4Hz", "+6%"
    elif speaker == "Reenu":
        voice, pitch, rate = "ml-IN-SobhanaNeural", "+3Hz", "+2%"
    else:
        # Narrator
        voice, pitch, rate = "ml-IN-SobhanaNeural", "-1Hz", "-3%"
        
    temp_mp3 = out_wav.replace(".wav", ".mp3")
    comm = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate)
    await comm.save(temp_mp3)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_mp3,
        "-ar", "24000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        out_wav
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(temp_mp3):
        os.remove(temp_mp3)

def generate_voices():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
    
    scenes = ep_data.get("scenes", [])
    print(f"Generating {len(scenes)} voice lines for Episode {ep_data.get('episode_number')}...")
    
    clients = get_api_clients()
    client_count = len(clients)
    current_key_idx = 0
    
    for sc in scenes:
        idx = sc["scene_index"]
        speaker = sc.get("speaker", "Reenu")
        text = sc["dialogue_malayalam"]
        voice = sc.get("voice", "Kore" if speaker in ["Reenu", "Narrator"] else ("Fenrir" if speaker == "Sachin" else "Puck"))
        out_wav = os.path.join(AUDIO_DIR, f"speech_{idx}.wav")
        
        if os.path.exists(out_wav) and os.path.getsize(out_wav) > 1000:
            print(f"Skipping speech_{idx}.wav (already generated).")
            continue
            
        print(f"Synthesizing speech_{idx}.wav ({speaker} - Gemini Voice '{voice}')...")
        synthesized = False
        
        # Primary: Gemini TTS with Multi-Key Rotation
        if clients:
            for attempt in range(client_count):
                active_client = clients[(current_key_idx + attempt) % client_count]
                try:
                    config = types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                            )
                        )
                    )
                    res = active_client.models.generate_content(
                        model="gemini-3.8-flash-tts",
                        contents=text,
                        config=config
                    )
                    audio_bytes = res.candidates[0].content.parts[0].inline_data.data
                    with open(out_wav, "wb") as f:
                        f.write(audio_bytes)
                    print(f"  -> Saved Gemini speech_{idx}.wav ({len(audio_bytes)} bytes) using key #{((current_key_idx + attempt) % client_count) + 1}")
                    synthesized = True
                    current_key_idx = (current_key_idx + attempt + 1) % client_count
                    time.sleep(3.5) # Polite pacing to prevent 429 burst limits
                    break
                except Exception as ex:
                    print(f"  -> Gemini TTS note on key #{((current_key_idx + attempt) % client_count) + 1}: {ex}")
                    time.sleep(2.0)
                    
        # Secondary Fallback: Edge-TTS Neural Voice
        if not synthesized:
            print(f"  -> Falling back to Edge-TTS neural voice for speech_{idx}.wav...")
            try:
                asyncio.run(synthesize_edge_tts(text, speaker, out_wav))
                if os.path.exists(out_wav) and os.path.getsize(out_wav) > 1000:
                    print(f"  -> Saved Edge-TTS fallback speech_{idx}.wav ({os.path.getsize(out_wav)} bytes)")
                    synthesized = True
            except Exception as e:
                print(f"  -> Edge-TTS note: {e}")

        # Tertiary Fallback: Silent WAV
        if not synthesized:
            print(f"  -> Fallback to silent WAV for speech_{idx}.wav")
            create_silent_wav(out_wav, duration=3.5)

def generate_foley_and_score(duration=130, sample_rate=24000):
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
        
        val = 0.0
        filtered = [0.0] * total_samples
        for i in range(total_samples):
            val += 0.15 * (samples[i] - val)
            filtered[i] = val
            
        with wave.open(amb_path, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            raw = bytearray()
            for s in filtered:
                ival = max(-32767, min(32767, int(s * 32767)))
                raw.extend(struct.pack('<h', ival))
            wav.writeframes(raw)
        print("Generated ambient soundscape.")

    bgm_path = os.path.join(AUDIO_DIR, "romance_score.wav")
    if not os.path.exists(bgm_path):
        # Pick romantic BGM from curated 10-track soft acoustic/piano library
        music_dir = os.path.join("assets", "music")
        ep_num = 1
        if os.path.exists(SCRIPT_FILE):
            try:
                with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
                    ep_num = json.load(f).get("episode_number", 1)
            except Exception:
                pass
                
        tracks = sorted([f for f in os.listdir(music_dir) if f.endswith(".mp3")]) if os.path.exists(music_dir) else []
        if tracks:
            selected_track = tracks[(ep_num - 1) % len(tracks)]
            track_path = os.path.join(music_dir, selected_track)
            print(f"Loading soft romantic piano BGM '{selected_track}' for Episode {ep_num}...")
            
            # Loop and fade BGM gently to fit exact episode duration
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", track_path,
                "-t", str(duration),
                "-ar", str(sample_rate),
                "-ac", "1",
                "-af", f"volume=0.25,afade=t=in:ss=0:d=2.0,afade=t=out:st={duration-3.0}:d=3.0",
                bgm_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Successfully processed cinematic BGM: {bgm_path}")
        else:
            create_silent_wav(bgm_path, duration=duration)

if __name__ == "__main__":
    generate_voices()
    generate_foley_and_score()
    print("All audio generation finished!")
