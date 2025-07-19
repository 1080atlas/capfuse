#!/usr/bin/env python3
"""
Enterprise-grade karaoke caption worker with forced alignment and smart filtering.
Integrates Gentle alignment, SpaCy filtering, advanced timing, and professional ASS generation.
"""

import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path

# Import our modular components
from alignment import GentleAligner
from filters import WordFilter
from timing import TimingOptimizer
from ass_builder import ASSBuilder


def log_progress(progress):
    """Log progress for the Node.js server to parse"""
    print(f"PROGRESS:{progress}", flush=True)


def load_preset_style(preset_id):
    """Load style configuration from preset_styles.json"""
    preset_file = Path(__file__).parent.parent / "preset_styles.json"
    with open(preset_file, 'r') as f:
        presets = json.load(f)
    
    for preset in presets:
        if preset['id'] == preset_id:
            return preset
    
    # Default to highlight-bold if preset not found
    return presets[0]


def extract_audio_for_whisper(input_file, audio_file):
    """Extract audio from video for Whisper processing."""
    print(f"Extracting audio from {input_file} to {audio_file}", flush=True)
    
    extract_cmd = [
        'ffmpeg', '-i', str(input_file), 
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # 16-bit PCM
        '-ar', '16000',  # 16kHz sample rate (whisper prefers this)
        '-ac', '1',  # Mono
        '-y',  # Overwrite
        str(audio_file)
    ]
    
    extract_result = subprocess.run(extract_cmd, capture_output=True, text=True)
    if extract_result.returncode != 0:
        print(f"Audio extraction failed: {extract_result.stderr}", file=sys.stderr)
        raise Exception("Audio extraction failed")
    
    return True


def transcribe_with_whisper(audio_file, output_base, precision='enterprise'):
    """
    Transcribe audio with Whisper-cpp.
    
    Args:
        audio_file: Path to audio file
        output_base: Base path for output files
        precision: 'mvp' for fast processing, 'enterprise' for full alignment
    """
    print("Starting Whisper-cpp transcription...", flush=True)
    
    model_path = Path(__file__).parent.parent / "models" / "ggml-base.bin"
    
    if precision == 'enterprise':
        # Enterprise mode: JSON output for forced alignment
        cmd = ['whisper-cli', '-m', str(model_path), '-f', str(audio_file), 
               '-oj', '-of', output_base]
    else:
        # MVP mode: Direct word-level timing (fallback)
        cmd = ['whisper-cli', '-m', str(model_path), '-f', str(audio_file), 
               '-owts', '--split-on-word', '--word-thold', '0.01',
               '-oj', '-of', output_base]
    
    print(f"Running: {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        json_file = Path(f"{output_base}.json")
        if json_file.exists():
            with open(json_file, 'r') as f:
                return json.load(f)
        else:
            print(f"Whisper JSON output not found: {json_file}", file=sys.stderr)
            return None
    else:
        print(f"Whisper failed: {result.stderr}", file=sys.stderr)
        return None


def extract_words_from_whisper(whisper_data):
    """Extract word-level timing from Whisper JSON."""
    words = []
    
    if 'transcription' in whisper_data:
        # Whisper-cpp format
        segments = whisper_data.get('transcription', [])
        for segment in segments:
            text = segment.get('text', '').strip()
            start = segment.get('offsets', {}).get('from', 0) / 1000.0  # Convert ms to seconds
            end = segment.get('offsets', {}).get('to', 0) / 1000.0
            
            # Split into words (basic splitting for segments)
            segment_words = text.split()
            if segment_words:
                word_duration = (end - start) / len(segment_words)
                for i, word in enumerate(segment_words):
                    word_start = start + (i * word_duration)
                    word_end = word_start + word_duration
                    words.append({
                        'word': word.strip(),
                        'start': word_start,
                        'end': word_end,
                        'confidence': 1.0
                    })
    
    elif 'segments' in whisper_data:
        # OpenAI Whisper format with word-level timing
        for segment in whisper_data['segments']:
            if 'words' in segment:
                for word_data in segment['words']:
                    words.append({
                        'word': word_data.get('word', '').strip(),
                        'start': float(word_data.get('start', 0)),
                        'end': float(word_data.get('end', 0)),
                        'confidence': float(word_data.get('probability', 1.0))
                    })
    
    return words


def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def burn_subtitles_with_ffmpeg(input_video, ass_file, output_video):
    """Burn subtitles into video using ffmpeg with hardware acceleration."""
    print("Starting FFmpeg subtitle burning with hardware acceleration...", flush=True)
    
    # Check for hardware acceleration support on macOS
    cmd = [
        'ffmpeg', 
        '-i', str(input_video),
        '-vf', f"subtitles='{str(ass_file)}'",
    ]
    
    # Try VideoToolbox acceleration on macOS
    try:
        # Test if VideoToolbox is available
        test_cmd = ['ffmpeg', '-hide_banner', '-hwaccels']
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        if 'videotoolbox' in result.stdout:
            print("Using VideoToolbox hardware acceleration", flush=True)
            cmd.extend(['-c:v', 'h264_videotoolbox', '-preset', 'veryfast'])
        else:
            cmd.extend(['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21'])
    except:
        cmd.extend(['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21'])
    
    cmd.extend([
        '-c:a', 'copy',  # Copy audio without re-encoding
        '-movflags', '+faststart',
        '-pix_fmt', 'yuv420p',
        '-y',
        str(output_video)
    ])
    
    print(f"Running: {' '.join(cmd)}", flush=True)
    
    # Run with progress monitoring
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        universal_newlines=True
    )
    
    while True:
        output = process.stderr.readline()
        if output == '' and process.poll() is not None:
            break
        if output and 'time=' in output:
            log_progress(85)  # FFmpeg progress
    
    if process.returncode == 0:
        print("Video processing completed successfully!", flush=True)
        log_progress(100)
        return True
    else:
        print(f"FFmpeg failed with return code: {process.returncode}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) != 7:
        print("Usage: python main_enterprise.py <job_id> <preset> <input_file> <font_size> <caption_mode> <show_filler>", file=sys.stderr)
        sys.exit(1)
    
    job_id = sys.argv[1]
    preset_id = sys.argv[2]
    input_file = sys.argv[3]
    font_size = int(sys.argv[4])
    caption_mode = sys.argv[5]  # 'sentences' or 'words'
    show_filler = sys.argv[6].lower() == 'true'
    
    # Determine precision mode based on caption mode
    precision = 'enterprise' if caption_mode == 'words' else 'mvp'
    
    log_progress(10)
    print(f"Enterprise karaoke processor starting: {caption_mode} mode, show_filler={show_filler}, precision={precision}", flush=True)
    
    # Load style preset
    style = load_preset_style(preset_id)
    style['fontSize'] = font_size
    print(f"Using style: {style['id']} with font size: {font_size}px", flush=True)
    
    # Set up file paths
    job_dir = Path(input_file).parent
    audio_file = job_dir / "audio.wav"
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{job_id}_captioned.mp4"
    
    try:
        # Step 1: Extract audio
        log_progress(20)
        extract_audio_for_whisper(input_file, audio_file)
        
        # Step 2: Transcribe with Whisper
        log_progress(30)
        whisper_data = transcribe_with_whisper(audio_file, str(job_dir / "transcription"), precision)
        if not whisper_data:
            raise Exception("Whisper transcription failed")
        
        # Step 3: Extract initial word timing
        log_progress(40)
        initial_words = extract_words_from_whisper(whisper_data)
        print(f"Extracted {len(initial_words)} words from Whisper", flush=True)
        
        if caption_mode == 'sentences':
            # For sentences mode, use existing sentence-level logic
            print("Processing in sentence mode (using existing logic)", flush=True)
            # TODO: Implement sentence mode with new modules
            # For now, fallback to original implementation
            print("Sentence mode not yet implemented in enterprise processor", file=sys.stderr)
            sys.exit(1)
        
        else:
            # Step 4: Forced alignment for enterprise precision (words mode only)
            if precision == 'enterprise':
                log_progress(45)
                print("Starting Gentle forced alignment...", flush=True)
                aligner = GentleAligner()
                aligned_data = aligner.align_audio_transcript(str(audio_file), whisper_data)
                if aligned_data:
                    aligned_words = aligned_data['words']
                    alignment_rate = aligned_data['alignment_stats']['alignment_rate']
                    print(f"Forced alignment completed: {alignment_rate:.1%} success rate", flush=True)
                else:
                    print("Forced alignment failed, using Whisper timing", flush=True)
                    aligned_words = initial_words
            else:
                aligned_words = initial_words
            
            # Step 5: Smart word filtering
            log_progress(50)
            word_filter = WordFilter()
            filtered_words = word_filter.filter_words(aligned_words, show_filler=show_filler)
            active_count = len([w for w in filtered_words if w.get('active', True)])
            print(f"Word filtering: {len(filtered_words)} total, {active_count} active words", flush=True)
            
            # Step 6: Timing optimization
            log_progress(60)
            # Get video duration for timing optimization
            probe_cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(input_file)]
            try:
                duration_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                clip_duration = float(duration_result.stdout.strip()) if duration_result.returncode == 0 else None
            except:
                clip_duration = None
            
            # Use conservative timing optimization for karaoke (disable gap merging to prevent overlaps)
            timing_optimizer = TimingOptimizer(gap_merge_threshold=0.0)  # Disable gap merging
            optimized_words = timing_optimizer.optimize_timing(filtered_words, clip_duration)
            print(f"Timing optimization completed", flush=True)
            
            # Step 7: Reading load analysis
            from ass_builder import estimate_reading_load, build_karaoke_ass
            ass_builder = ASSBuilder()
            load_stats = estimate_reading_load(optimized_words)
            print(f"Reading analysis: {load_stats['reading_difficulty']} difficulty, {load_stats['words_per_second']:.1f} words/sec", flush=True)
            
            # Step 8: Generate enterprise ASS
            log_progress(70)
            ass_content = build_karaoke_ass(optimized_words, style, video_width=1080, video_height=1920)
            ass_file = job_dir / "subtitles.ass"
            
            with open(ass_file, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            print("Enterprise ASS generation completed", flush=True)
        
        # Step 9: Burn subtitles with hardware acceleration
        log_progress(75)
        if not burn_subtitles_with_ffmpeg(input_file, ass_file, output_file):
            raise Exception("Video processing failed")
        
        # Cleanup
        try:
            audio_file.unlink()
        except:
            pass
        
        print(f"SUCCESS! Enterprise karaoke captions: {output_file}", flush=True)
        
    except Exception as e:
        print(f"Enterprise processing failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()