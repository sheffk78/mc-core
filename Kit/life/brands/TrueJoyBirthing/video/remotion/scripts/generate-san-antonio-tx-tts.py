#!/usr/bin/env python3
"""Generate TTS audio for San Antonio TX video scenes, pad, merge, and update data file."""
import json, base64, subprocess, os, re, sys, time, shutil
from pathlib import Path

# Get API key
api_key = None
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line.startswith("MISTRAL_API_KEY="):
            api_key = line.split("=", 1)[1].strip()
            break

if not api_key:
    print("ERROR: No MISTRAL_API_KEY found")
    sys.exit(1)

# Read scene data file
data_file = "src/data/san-antonio-tx-data.ts"
with open(data_file) as f:
    content = f.read()

# Extract narrations and scene IDs using regex
narrations = re.findall(r'narration:\s*"((?:[^"\\]|\\.)*)"', content)
scene_ids = re.findall(r'scene_id:\s*"([^"]+)"', content)

print(f"Found {len(scene_ids)} scenes, {len(narrations)} narrations")

# Shelbi voice ID (consistent per recurring-mistakes block #5)
VOICE_ID = "331c27cd-1809-43c2-853d-4c167f184670"
MODEL = "voxtral-mini-tts-latest"

def generate_tts(text, output_path):
    """Generate TTS using Mistral Voxtral API (OpenAI-compatible /v1/audio/speech)."""
    payload = json.dumps({
        "model": MODEL,
        "input": text,
        "voice": VOICE_ID,
        "response_format": "wav"
    })

    curl_cmd = [
        "curl", "-s", "-X", "POST",
        "https://api.mistral.ai/v1/audio/speech",
        "-H", f"Authorization: Bearer {api_key}",
        "-H", "Content-Type: application/json",
        "-d", payload
    ]

    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: curl failed: {result.stderr}")
        return False, 0

    try:
        data = json.loads(result.stdout)
        if "audio_data" not in data:
            print(f"  ERROR: no audio_data in response: {result.stdout[:200]}")
            return False, 0
        wav_bytes = base64.b64decode(data["audio_data"])
        with open(output_path, "wb") as f:
            f.write(wav_bytes)
        return True, len(wav_bytes)
    except Exception as e:
        print(f"  ERROR: {e}")
        return False, 0

def get_duration(wav_path):
    """Get duration of a wav file using ffprobe."""
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "csv=p=0", str(wav_path)
    ], capture_output=True, text=True)
    return float(result.stdout.strip())

def pad_wav(input_path, output_path, pad_seconds=0.33):
    """Pad wav with silence at the end using ffmpeg."""
    subprocess.run([
        "ffmpeg", "-y", "-i", str(input_path),
        "-af", f"apad=pad_dur={pad_seconds}",
        str(output_path)
    ], capture_output=True)

audio_dir = Path("public/audio/san-antonio-tx")
audio_dir.mkdir(parents=True, exist_ok=True)

scene_data = []
success_count = 0
for scene_id, narration in zip(scene_ids, narrations):
    print(f"\nGenerating TTS for {scene_id}: {narration[:80]}...")
    out_path = audio_dir / f"{scene_id}.wav"
    ok, info = generate_tts(narration, out_path)
    if ok:
        raw_dur = get_duration(out_path)
        print(f"  Ã¢ÂÂ Saved {scene_id}.wav ({info} bytes, {raw_dur:.2f}s)")
        scene_data.append({"scene_id": scene_id, "raw": round(raw_dur, 2)})
        success_count += 1
    else:
        print(f"  Ã¢ÂÂ FAILED for {scene_id}")
        sys.exit(1)

# Pad each scene and create master
padded_data = []
padded_files = []

for entry in scene_data:
    scene_id = entry["scene_id"]
    raw_dur = entry["raw"]

    raw_path = audio_dir / f"{scene_id}.wav"
    padded_path = audio_dir / f"{scene_id}-padded.wav"

    pad_wav(raw_path, padded_path)

    actual_padded = get_duration(padded_path)
    entry["padded"] = round(actual_padded, 2)
    padded_data.append(entry)
    padded_files.append(str(padded_path))
    print(f"  {scene_id}: {raw_dur:.2f}s -> {actual_padded:.2f}s")

# Save durations.json
durations_path = audio_dir / "durations.json"
with open(durations_path, "w") as f:
    json.dump(padded_data, f, indent=2)
print(f"\nSaved durations.json")

# Merge all padded wavs into master
master_path = audio_dir / "san-antonio-tx-master.wav"
concat_list = audio_dir / "concat_list.txt"
with open(concat_list, "w") as f:
    for pfile in padded_files:
        f.write(f"file '{pfile}'\n")

subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", str(concat_list), "-c", "copy", str(master_path)
], capture_output=True)

master_dur = get_duration(master_path)
print(f"Master wav: {master_dur:.2f}s")

# Clean up concat list
concat_list.unlink()

# Copy to audio dir for composition
audio_composition_dir = Path("audio/san-antonio-tx")
audio_composition_dir.mkdir(parents=True, exist_ok=True)
shutil.copy(str(master_path), str(audio_composition_dir / "san-antonio-tx-master.wav"))
print(f"Copied master to {audio_composition_dir / 'san-antonio-tx-master.wav'}")

# Update data file with actual durations
print("\nUpdating data file with actual durations...")
with open(data_file) as f:
    content = f.read()

# Update each scene's duration_seconds with the padded duration
for entry in padded_data:
    scene_id = entry["scene_id"]
    padded_dur = entry["padded"]
    pattern = rf'(scene_id:\s*"{re.escape(scene_id)}".*?duration_seconds:\s*)[\d.]+'
    content = re.sub(pattern, rf'\g<1>{padded_dur}', content, flags=re.DOTALL)

# Update total duration in metadata
total_dur = sum(e["padded"] for e in padded_data)
content = re.sub(r'(duration_seconds:\s*)[\d.]+(?=,\s*\n\s*fps)', rf'\g<1>{round(total_dur, 2)}', content, count=1)

with open(data_file, "w") as f:
    f.write(content)

print(f"Updated {data_file} with actual durations")
print(f"Total duration: {total_dur:.2f}s")

print(f"\n{'='*60}")
print(f"Done: {success_count} scenes generated, master wav built")
