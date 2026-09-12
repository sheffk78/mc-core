#!/bin/zsh
# All-night Caleb Classes recording script
# Records remaining videos from Google Drive via BlackHole audio capture
# Runs after Court Class finishes, then records remaining videos
#
# Videos already done:
# - Court Class: parts 1-8 (0-80 min) + parts 9-18 in progress (81-178 min)
# - Endorsement Enforcement: fully recorded (~148 min)
# - Discharge Bills: parts 1-4 (0-40 min) — needs 40 min onward
#
# Still to record:
# 1. Discharge Bills: 40 min onward (need to check total duration)
# 2. In God We Trust Class
# 3. Maximum Return Tax Class
# 4. National Status Video
# 5. Securitization Mastery
# 6. Tax Workshop Replay

OUTPUT_DIR="$HOME/.openclaw/workspace/Kit/life/brands/WingPoint/training/raw-documents/caleb-classes/audio"

# Function to record a video in 10-min chunks
record_video_chunks() {
    local video_name="$1"
    local start_min="$2"
    local end_min="$3"
    local prefix="$4"
    
    local current_min=$start_min
    local chunk_num=1
    
    # Count existing chunks to continue numbering
    while [ -f "$OUTPUT_DIR/${prefix}_part${chunk_num}_${current_min}to$((current_min + 10))_256k.m4a" ]; do
        chunk_num=$((chunk_num + 1))
    done
    
    echo "=== Recording $video_name from ${start_min}m to ${end_min}m ==="
    
    while [ $current_min -lt $end_min ]; do
        local next_min=$((current_min + 10))
        if [ $next_min -gt $end_min ]; then
            next_min=$end_min
        fi
        
        local duration=$(( (next_min - current_min) * 60 ))
        local chunk_file="$OUTPUT_DIR/${prefix}_part${chunk_num}_${current_min}to${next_min}_256k.m4a"
        
        # Skip if already recorded
        if [ -f "$chunk_file" ] && [ $(stat -f%z "$chunk_file" 2>/dev/null) -gt 100000 ]; then
            echo "SKIP: $chunk_file already exists"
            current_min=$next_min
            chunk_num=$((chunk_num + 1))
            continue
        fi
        
        echo "Recording: $chunk_file (${duration}s)"
        ffmpeg -f avfoundation -i ":BlackHole 2ch" \
            -t $duration \
            -acodec aac -ab 256k \
            "$chunk_file" 2>&1
        
        echo "Finished: $chunk_file"
        current_min=$next_min
        chunk_num=$((chunk_num + 1))
        sleep 2
    done
    
    echo "=== DONE: $video_name ==="
}

# Wait for Court Class chained recording to finish
echo "Waiting for Court Class to complete..."
while pgrep -f "ffmpeg.*Court_Class" > /dev/null 2>&1; do
    sleep 30
done
echo "Court Class recording complete."

# Switch audio back to speakers between videos
SwitchAudioSource -s "BlackHole+Speakers" 2>&1
sleep 2

echo ""
echo "============================================"
echo "Court Class COMPLETE. Ready for next videos."
echo "IMPORTANT: Need to open next video in Comet"
echo "and seek to the right position, then route"
echo "audio to BlackHole and press play."
echo "============================================"
echo ""
echo "Court Class audio files recorded:"
ls -lh $OUTPUT_DIR/Court_Class_part*_256k.m4a 2>/dev/null | wc -l
echo "files total"
ls -lh $OUTPUT_DIR/Court_Class_part*_256k.m4a 2>/dev/null

echo ""
echo "Script finished. Remaining videos need manual video switching in Comet."
echo "Videos to record next:"
echo "1. Discharge Bills (resume from 40 min)"
echo "2. In God We Trust Class"
echo "3. Maximum Return Tax Class"  
echo "4. National Status Video"
echo "5. Securitization Mastery"
echo "6. Tax Workshop Replay"

# Switch audio back
SwitchAudioSource -s "BlackHole+Speakers" 2>&1
echo "Audio restored to BlackHole+Speakers"