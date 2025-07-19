#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path

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

def parse_wts_to_word_srt(wts_file, output_srt):
    """Convert whisper-cpp .wts output to word-level SRT format with readable timing"""
    try:
        import re
        
        with open(wts_file, 'r', encoding='utf-8') as f:
            wts_content = f.read()
        
        srt_content = ""
        word_index = 1
        
        # Extract word-level timing from drawtext commands
        # Look for the pattern: text='>...word|...' followed by :enable='between(t,start,end)'
        # The word appears after '>' and before '|'
        pattern = r"text='>[^|]*?([A-Za-z',.-]+)\|[^']*?':enable='between\(t,([0-9.]+),([0-9.]+)\)'"
        matches = re.findall(pattern, wts_content)
        
        # Common stop words to filter out for cleaner karaoke captions
        stop_words = {
            # Articles
            'a', 'an', 'the',
            # Prepositions  
            'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to', 'of', 'up', 'out', 'off', 'down', 
            'over', 'under', 'above', 'below', 'through', 'between', 'into', 'onto', 'upon',
            # Conjunctions
            'and', 'or', 'but', 'so', 'yet', 'nor', 'because', 'since', 'while', 'although', 'though',
            # Common verbs
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall',
            # Pronouns
            'i', 'me', 'my', 'mine', 'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'hers',
            'it', 'its', 'we', 'us', 'our', 'ours', 'they', 'them', 'their', 'theirs',
            # Common words
            'that', 'this', 'these', 'those', 'what', 'when', 'where', 'why', 'how', 'who', 'which',
            'some', 'any', 'all', 'each', 'every', 'no', 'not', 'very', 'too', 'so', 'just', 'only',
            'also', 'then', 'than', 'now', 'here', 'there', 'yes', 'yeah', 'ok', 'okay'
        }
        
        # Process words with improved timing and stop word filtering
        words_data = []
        for word_match in matches:
            word = word_match[0].strip()
            start_time = float(word_match[1])
            end_time = float(word_match[2])
            
            # Clean up the word (remove escape sequences and extra characters)
            word = word.replace('\\', '').strip()
            
            # Only include actual words (no punctuation-only matches)
            if word and len(word) > 0 and any(c.isalpha() for c in word):
                # Filter out stop words (case insensitive)
                if word.lower() not in stop_words:
                    words_data.append((word, start_time, end_time))
        
        # Apply improved timing rules with consistent minimum duration
        improved_words = []
        min_duration = 0.4  # 400ms minimum for readability
        max_duration = 1.5  # 1.5 seconds maximum
        
        for i, (word, original_start, original_end) in enumerate(words_data):
            start_time = original_start
            end_time = original_end
            
            # Always ensure minimum duration first
            if end_time - start_time < min_duration:
                end_time = start_time + min_duration
            
            # Then check for overlaps with next word and adjust if needed
            if i + 1 < len(words_data):
                next_word_start = words_data[i + 1][1]
                if end_time > next_word_start - 0.05:  # Leave 50ms buffer
                    end_time = next_word_start - 0.05
                    
                    # If this makes duration too short, extend backwards slightly
                    if end_time - start_time < min_duration * 0.75:  # At least 75% of minimum
                        potential_start = end_time - min_duration * 0.75
                        # Don't go before previous word end
                        if i > 0:
                            prev_word_end = improved_words[i-1][2] if improved_words else 0
                            start_time = max(potential_start, prev_word_end + 0.05)
                        else:
                            start_time = max(potential_start, 0)
            
            # Apply maximum duration
            if end_time - start_time > max_duration:
                end_time = start_time + max_duration
                
            # Final safety check - ensure end is after start
            if end_time <= start_time:
                end_time = start_time + 0.3
                
            improved_words.append((word, start_time, end_time))
        
        # Generate SRT from improved timings
        for word, start_time, end_time in improved_words:
            start_timestamp = format_timestamp(start_time)
            end_timestamp = format_timestamp(end_time)
            
            srt_content += f"{word_index}\n"
            srt_content += f"{start_timestamp} --> {end_timestamp}\n"
            srt_content += f"{word}\n\n"
            word_index += 1
        
        # Write SRT file
        with open(output_srt, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        print(f"Generated word-level SRT with {word_index - 1} key words (stop words filtered, improved timing)", flush=True)
        return True
        
    except Exception as e:
        print(f"Error parsing WTS to word-level SRT: {e}", file=sys.stderr)
        return False

def generate_srt_with_whisper(input_file, output_srt, caption_mode='sentences'):
    """Generate SRT file using whisper-cpp with optional word-level timing"""
    try:
        print("Starting transcription with whisper-cpp...", flush=True)
        log_progress(20)
        
        # Try whisper-cpp first, fallback to OpenAI Whisper if not available
        try:
            # whisper-cpp command (as specified in CLAUDE.md)
            import os
            model_path = Path(__file__).parent.parent / "models" / "ggml-base.bin"
            
            # First extract audio from video using ffmpeg
            audio_file = Path(input_file).parent / "audio.wav"
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
            
            log_progress(30)
            
            # Now run whisper-cpp on the extracted audio
            output_base = str(Path(output_srt).parent / Path(output_srt).stem)
            
            if caption_mode == 'words':
                # Use word-level timing for karaoke-style captions
                cmd = ['whisper-cli', '-m', str(model_path), '-f', str(audio_file), 
                       '-owts', '--split-on-word', '--word-thold', '0.01',
                       '-oj', '-of', output_base]  # Output JSON for word timing
                print(f"Running whisper-cpp with word-level timing: {' '.join(cmd)}", flush=True)
            else:
                # Standard sentence-level timing
                cmd = ['whisper-cli', '-m', str(model_path), '-f', str(audio_file), '-osrt', '-of', output_base]
                print(f"Running whisper-cpp with sentence-level timing: {' '.join(cmd)}", flush=True)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if caption_mode == 'words':
                    # Parse WTS output for word-level timing
                    wts_file = Path(output_srt).parent / f"{Path(output_srt).stem}.wts"
                    if wts_file.exists():
                        if parse_wts_to_word_srt(wts_file, output_srt):
                            print("whisper-cpp word-level transcription completed", flush=True)
                            # Clean up temporary files
                            try:
                                audio_file.unlink()
                                wts_file.unlink()
                                # Also clean up JSON file if it exists
                                json_file = Path(output_srt).parent / f"{Path(output_srt).stem}.json"
                                if json_file.exists():
                                    json_file.unlink()
                            except:
                                pass
                            log_progress(50)
                            return True
                    else:
                        print(f"whisper-cpp WTS output not found: {wts_file}", file=sys.stderr)
                else:
                    # Check if the SRT file was created
                    if Path(output_srt).exists():
                        print("whisper-cpp sentence-level transcription completed", flush=True)
                        # Clean up audio file
                        try:
                            audio_file.unlink()
                        except:
                            pass
                        log_progress(50)
                        return True
                    else:
                        print(f"whisper-cpp SRT output not found: {output_srt}", file=sys.stderr)
                
                print(f"whisper-cpp stdout: {result.stdout}", file=sys.stderr)
                print(f"whisper-cpp stderr: {result.stderr}", file=sys.stderr)
            else:
                print(f"whisper-cpp failed with code {result.returncode}", file=sys.stderr)
                print(f"whisper-cpp stdout: {result.stdout}", file=sys.stderr)
                print(f"whisper-cpp stderr: {result.stderr}", file=sys.stderr)
                # Fall through to OpenAI Whisper fallback
        except FileNotFoundError:
            print("whisper-cpp not found, trying OpenAI Whisper fallback", flush=True)
        except Exception as e:
            print(f"whisper-cpp error: {e}", file=sys.stderr)
        
        # Fallback to OpenAI Whisper if whisper-cpp not available
        try:
            import whisper
            model = whisper.load_model("base")
            log_progress(30)
            
            result = model.transcribe(input_file)
            log_progress(45)
            
            # Convert to SRT format
            srt_content = ""
            for i, segment in enumerate(result["segments"], 1):
                start_time = format_timestamp(segment["start"])
                end_time = format_timestamp(segment["end"])
                text = segment["text"].strip()
                srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
            
            with open(output_srt, 'w', encoding='utf-8') as f:
                f.write(srt_content)
                
            print(f"OpenAI Whisper fallback completed! Generated {len(result['segments'])} segments", flush=True)
            log_progress(50)
            return True
            
        except ImportError:
            # Final fallback to mock for development
            print("No whisper available, using mock captions for development", flush=True)
            mock_srt_content = """1
00:00:00,000 --> 00:00:03,000
Welcome to CapFuse

2
00:00:03,000 --> 00:00:06,000
AI-powered video captions

3
00:00:06,000 --> 00:00:09,000
Made with trendy styles
"""
            with open(output_srt, 'w') as f:
                f.write(mock_srt_content)
            log_progress(50)
            return True
        
    except Exception as e:
        print(f"Transcription error: {e}", file=sys.stderr)
        return False

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def convert_srt_to_ass(srt_file, ass_file, style):
    """Convert SRT to ASS with style applied (supports word-level karaoke timing)"""
    try:
        print(f"Converting SRT to ASS with style: {style['name']}", flush=True)
        
        # Read SRT content
        with open(srt_file, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        # Detect if this is word-level timing (most entries are single words)
        lines = srt_content.strip().split('\n\n')
        single_word_count = 0
        total_entries = 0
        
        for block in lines:
            if not block.strip():
                continue
            parts = block.split('\n')
            if len(parts) >= 3:
                text = ' '.join(parts[2:]).strip()
                total_entries += 1
                # Check if text is likely a single word (no spaces, reasonable length)
                if ' ' not in text and len(text) <= 15:
                    single_word_count += 1
        
        is_word_level = total_entries > 0 and (single_word_count / total_entries) > 0.7
        print(f"Detected {'word-level' if is_word_level else 'sentence-level'} timing ({single_word_count}/{total_entries} single words)", flush=True)
        
        # Build ASS style line with proper formatting
        # For word-level timing, use slightly larger font and center alignment
        font_size = style['fontSize']
        if is_word_level:
            font_size = int(font_size * 1.2)  # 20% larger for individual words
            
        ass_style = (
            f"Style: Default,{style['font']},{font_size},"
            f"{style['primaryColour']},&H000000FF,"
            f"{style.get('outlineColour', '&H00000000')},"
            f"{style.get('backColour', '&H00000000')},"
            f"1,0,0,0,100,100,0,0,1,"
            f"{style.get('outline', 0)},{style.get('shadow', 0)},"
            f"2,10,10,10,1"
        )
        
        # Generate ASS header with style and proper video resolution
        # Default to common social media vertical format, will be detected from video later
        play_res_x = 576  # Common TikTok/Instagram width
        play_res_y = 1024  # Common TikTok/Instagram height
        
        ass_content = f"""[Script Info]
Title: CapFuse Generated Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{ass_style}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # Parse SRT and convert to ASS format
        lines = srt_content.strip().split('\n\n')
        prev_end_time = None
        
        for block in lines:
            if not block.strip():
                continue
            
            parts = block.split('\n')
            if len(parts) >= 3:
                timing = parts[1]
                text = ' '.join(parts[2:])
                
                # Convert SRT timing to ASS timing format
                # SRT: 00:00:01,000 --> 00:00:04,000
                # ASS: 0:00:01.00,0:00:04.00
                start_time, end_time = timing.split(' --> ')
                start_time = start_time.replace(',', '.')
                end_time = end_time.replace(',', '.')
                
                # Convert to centiseconds (ASS format) by truncating to 2 decimal places
                def convert_to_ass_time(srt_time):
                    # Remove leading zeros from hours if they exist
                    if srt_time.startswith('00:'):
                        srt_time = srt_time[1:]  # Remove one leading zero to get 0:MM:SS.mmm
                    # Truncate milliseconds to centiseconds (2 decimal places)
                    if '.' in srt_time:
                        time_part, ms_part = srt_time.split('.')
                        ms_part = ms_part[:2].ljust(2, '0')  # Ensure 2 digits
                        return f"{time_part}.{ms_part}"
                    return srt_time
                
                start_time = convert_to_ass_time(start_time)
                end_time = convert_to_ass_time(end_time)
                
                # For word-level timing, add small gaps between words to prevent flicker
                if is_word_level and prev_end_time:
                    # Convert times to float for calculation
                    def time_to_seconds(time_str):
                        parts = time_str.split(':')
                        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    
                    def seconds_to_time(seconds):
                        hours = int(seconds // 3600)
                        minutes = int((seconds % 3600) // 60)
                        secs = seconds % 60
                        return f"{hours}:{minutes:02d}:{secs:05.2f}"
                    
                    current_start = time_to_seconds(start_time)
                    previous_end = time_to_seconds(prev_end_time)
                    
                    # Add 0.1 second gap if words are too close
                    if current_start - previous_end < 0.1:
                        start_time = seconds_to_time(previous_end + 0.1)
                
                prev_end_time = end_time
                
                # Clean up text and escape special characters
                text = str(text)  # Ensure it's a string
                text = text.replace('\\', '\\\\')
                text = text.replace('{', '\\{')
                text = text.replace('}', '\\}')
                
                # For word-level captions, ensure consistent center positioning
                if is_word_level:
                    # Add positioning and effect for karaoke-style words
                    # Position words in the center-bottom area of the video
                    center_x = play_res_x // 2  # Horizontal center
                    bottom_y = int(play_res_y * 0.85)  # 85% down from top (bottom area)
                    ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{{\\pos({center_x},{bottom_y})\\fad(100,100)}}{text}\\N\n"
                else:
                    # Standard subtitle positioning (bottom center)
                    ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\\N\n"
        
        # Write ASS file
        with open(ass_file, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        print("ASS conversion completed", flush=True)
        log_progress(70)
        return True
    except Exception as e:
        print(f"ASS conversion error: {e}", file=sys.stderr)
        return False

def burn_subtitles_with_ffmpeg(input_video, ass_file, output_video):
    """Burn subtitles into video using ffmpeg with optimized settings"""
    try:
        print("Starting ffmpeg subtitle burning...", flush=True)
        log_progress(75)
        
        # Optimized ffmpeg command for social media content
        cmd = [
            'ffmpeg', 
            '-i', str(input_video),
            '-vf', f"subtitles={str(ass_file)}",  # Use ASS file styling without override
            '-c:v', 'libx264',          # Video codec
            '-preset', 'medium',         # Encoding speed vs quality
            '-crf', '23',               # Quality (lower = better, 23 is good default)
            '-c:a', 'aac',              # Audio codec
            '-b:a', '128k',             # Audio bitrate
            '-movflags', '+faststart',   # Web optimization
            '-pix_fmt', 'yuv420p',      # Compatibility
            '-y',                       # Overwrite output file
            str(output_video)
        ]
        
        print(f"Running: {' '.join(cmd)}", flush=True)
        log_progress(80)
        
        # Run ffmpeg with real-time output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            universal_newlines=True
        )
        
        # Monitor progress
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Parse ffmpeg progress if possible
                if 'time=' in output:
                    # Extract time progress and update
                    try:
                        time_part = output.split('time=')[1].split()[0]
                        # Could parse time to calculate percentage, but keep it simple for now
                        log_progress(85)
                    except:
                        pass
                print(f"FFmpeg: {output.strip()}", flush=True)
        
        # Check if process completed successfully
        if process.returncode == 0:
            print("Video processing completed successfully!", flush=True)
            log_progress(100)
            return True
        else:
            print(f"FFmpeg failed with return code: {process.returncode}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"FFmpeg execution error: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) != 6:
        print("Usage: python main.py <job_id> <preset> <input_file> <font_size> <caption_mode>", file=sys.stderr)
        sys.exit(1)
    
    job_id = sys.argv[1]
    preset_id = sys.argv[2]
    input_file = sys.argv[3]
    font_size = int(sys.argv[4])
    caption_mode = sys.argv[5]
    
    log_progress(10)
    
    # Load style preset
    style = load_preset_style(preset_id)
    # Override fontSize with custom value
    style['fontSize'] = font_size
    print(f"Using style: {style['name']} with custom font size: {font_size}px, caption mode: {caption_mode}", flush=True)
    
    # Set up file paths
    job_dir = Path(input_file).parent
    srt_file = job_dir / "subtitles.srt"
    ass_file = job_dir / "subtitles.ass"
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{job_id}_captioned.mp4"
    
    log_progress(20)
    
    # Step 1: Generate SRT with Whisper (with caption mode)
    if not generate_srt_with_whisper(input_file, srt_file, caption_mode):
        print("Failed to generate SRT", file=sys.stderr)
        sys.exit(1)
    
    # Step 2: Convert SRT to ASS with styling
    if not convert_srt_to_ass(srt_file, ass_file, style):
        print("Failed to convert to ASS", file=sys.stderr)
        sys.exit(1)
    
    # Step 3: Burn subtitles with ffmpeg
    if not burn_subtitles_with_ffmpeg(input_file, ass_file, output_file):
        print("Failed to burn subtitles", file=sys.stderr)
        sys.exit(1)
    
    print(f"Success! Output: {output_file}", flush=True)

if __name__ == "__main__":
    main()