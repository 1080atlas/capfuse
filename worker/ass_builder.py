#!/usr/bin/env python3
"""
Advanced ASS subtitle builder for enterprise karaoke captions.
Supports frame-accurate timing, active/inactive word styling, and visual effects.
"""

import math
from typing import List, Dict, Tuple, Optional


class ASSBuilder:
    """Advanced ASS subtitle generator for karaoke-style captions."""
    
    def __init__(self, video_width: int = 576, video_height: int = 1024):
        """
        Initialize ASS builder with video dimensions.
        
        Args:
            video_width: Video width for positioning calculations
            video_height: Video height for positioning calculations
        """
        self.video_width = video_width
        self.video_height = video_height
        
        # Calculate positioning
        self.center_x = video_width // 2
        self.base_y = int(video_height * 0.85)  # 85% down from top
        self.alt_y = int(video_height * 0.88)   # Alternate position for burn-in prevention
        
    def build_ass_content(self, words: List[Dict], style_config: Dict) -> str:
        """
        Build complete ASS subtitle content with karaoke effects.
        
        Args:
            words: List of word dicts with timing and active status
            style_config: Style configuration from preset
            
        Returns:
            Complete ASS subtitle content
        """
        # Generate header
        header = self._generate_header(style_config)
        
        # Generate styles
        styles = self._generate_styles(style_config)
        
        # Generate events
        events = self._generate_events(words, style_config)
        
        return header + styles + events
    
    def _generate_header(self, style_config: Dict) -> str:
        """Generate ASS header with proper video resolution."""
        return f"""[Script Info]
Title: CapFuse Enterprise Karaoke Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {self.video_width}
PlayResY: {self.video_height}

"""
    
    def _generate_styles(self, style_config: Dict) -> str:
        """Generate ASS styles for karaoke captions."""
        base_font_size = style_config.get('fontSize', 42)
        font_name = style_config.get('font', 'Poppins-SemiBold')
        
        # Single karaoke style (libass handles active/inactive automatically)
        karaoke_style = self._build_karaoke_style(
            name="KActive",
            font_name=font_name,
            font_size=base_font_size,
            primary_colour=style_config.get('primaryColour', '&H00FFFFFF'),  # Active word color
            secondary_colour='&H7FFFFFFF',  # Inactive word color (50% white)
            outline_colour=style_config.get('outlineColour', '&H00000000'),
            back_colour=style_config.get('backColour', '&H00000000'),
            outline=style_config.get('outline', 1),
            shadow=style_config.get('shadow', 0),
            alignment=2  # Bottom center
        )
        
        return f"""[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{karaoke_style}

"""
    
    def _build_karaoke_style(self, name: str, font_name: str, font_size: int, 
                           primary_colour: str, secondary_colour: str, outline_colour: str, 
                           back_colour: str, outline: int, shadow: int, alignment: int) -> str:
        """Build a karaoke ASS style line with primary and secondary colors."""
        return (
            f"Style: {name},{font_name},{font_size},"
            f"{primary_colour},{secondary_colour},"
            f"{outline_colour},{back_colour},"
            f"1,0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},10,10,10,1"
        )
    
    def _build_style(self, name: str, font_name: str, font_size: int, 
                    primary_colour: str, outline_colour: str, back_colour: str,
                    outline: int, shadow: int, alignment: int) -> str:
        """Build a single ASS style line."""
        return (
            f"Style: {name},{font_name},{font_size},"
            f"{primary_colour},&H000000FF,"
            f"{outline_colour},{back_colour},"
            f"1,0,0,0,100,100,0,0,1,"
            f"{outline},{shadow},"
            f"{alignment},10,10,10,1"
        )
    
    def _adjust_color_opacity(self, color: str, opacity: float) -> str:
        """Adjust ASS color opacity (alpha channel)."""
        if not color.startswith('&H'):
            return color
        
        # ASS colors are in format &HAABBGGRR where AA is alpha
        try:
            # Extract components
            hex_val = color[2:]  # Remove &H prefix
            if len(hex_val) == 8:
                alpha = int(hex_val[:2], 16)
                rest = hex_val[2:]
            else:
                alpha = 0
                rest = hex_val.zfill(6)
            
            # Apply opacity (0=opaque, 255=transparent in ASS)
            new_alpha = int(255 * (1 - opacity))
            
            return f"&H{new_alpha:02X}{rest}"
        except:
            return color
    
    def _generate_events(self, words: List[Dict], style_config: Dict) -> str:
        """Generate ASS events with proper libass karaoke format."""
        events_header = """[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        events = []
        
        # Group words into sentences for karaoke lines
        word_groups = self._group_words_into_sentences(words)
        
        for group_idx, word_group in enumerate(word_groups):
            if not word_group:
                continue
                
            # Alternate Y position between sentences (860 ↔ 900)
            pos_y = 900 if group_idx % 2 else 860
            
            # Build sentence timing (first word start to last word end)
            start_time = self._seconds_to_ass_time(word_group[0]['start'])
            end_time = self._seconds_to_ass_time(word_group[-1]['end'])
            
            # Build karaoke text with proper libass format
            # Start with positioning
            karaoke_parts = [f"{{\\\\pos({self.center_x},{pos_y})}}"]
            
            # Add each word with its karaoke timing in curly braces
            for word in word_group:
                duration_cs = round((word['end'] - word['start']) * 100)  # Convert to centiseconds
                clean_word = self._escape_ass_text(word['word'])
                
                # Proper libass karaoke format: {\k<duration>}word
                karaoke_parts.append(f"{{\\\\k{duration_cs}}}{clean_word}")
            
            # Join with spaces between words
            karaoke_text = "".join(karaoke_parts[0:1]) + " ".join(karaoke_parts[1:])
            
            # Create single dialogue line with Effect: Karaoke (enables karaoke parsing)
            event_line = f"Dialogue: 0,{start_time},{end_time},KActive,,0,0,0,Karaoke,{karaoke_text}"
            events.append(event_line)
        
        return events_header + "\\n".join(events) + "\\n"
    
    def _group_words_into_sentences(self, words: List[Dict]) -> List[List[Dict]]:
        """Group words into sentences ensuring no time overlaps."""
        if not words:
            return []
        
        groups = []
        current_group = []
        max_words_per_sentence = 6  # Max 6 words per sentence (reduced for better readability)
        max_sentence_duration = 3.5  # Max 3.5 seconds per sentence
        large_gap_threshold = 0.8  # 0.8 second gap indicates sentence break
        
        for word in words:
            # Check if we should start a new sentence
            should_break = False
            
            if current_group:
                # Check various break conditions
                gap_from_last = word['start'] - current_group[-1]['end']
                duration_from_first = word['start'] - current_group[0]['start']
                
                should_break = (
                    len(current_group) >= max_words_per_sentence or
                    duration_from_first > max_sentence_duration or
                    gap_from_last > large_gap_threshold
                )
            
            if should_break:
                groups.append(current_group.copy())
                current_group = []
            
            current_group.append(word)
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        # CRITICAL FIX: Ensure no sentence overlaps in time
        return self._fix_sentence_timing_overlaps(groups)
    
    def _fix_sentence_timing_overlaps(self, groups: List[List[Dict]]) -> List[List[Dict]]:
        """Fix overlapping sentence timings to prevent multiple dialogues showing simultaneously."""
        if len(groups) <= 1:
            return groups
        
        fixed_groups = []
        
        for i, group in enumerate(groups):
            if not group:
                continue
                
            # Deep copy the group to avoid modifying original
            fixed_group = [word.copy() for word in group]
            
            # If this sentence overlaps with the next one, truncate it
            if i + 1 < len(groups) and groups[i + 1]:
                next_start = groups[i + 1][0]['start']
                current_end = fixed_group[-1]['end']  # No buffer - check actual end time
                
                if current_end >= next_start:
                    # Overlap detected - truncate current sentence to end before next starts
                    gap = 0.05  # 50ms gap between sentences
                    new_end = next_start - gap
                    
                    # Update the last word's end time
                    fixed_group[-1]['end'] = new_end
                    
                    # If the truncation makes the word too short, remove it entirely
                    if fixed_group[-1]['end'] <= fixed_group[-1]['start']:
                        fixed_group.pop()
                        # If we removed the last word, check if group is empty
                        if not fixed_group:
                            continue
            
            fixed_groups.append(fixed_group)
        
        return fixed_groups
    
    def _build_word_text(self, word: Dict, pos_y: int, is_active: bool) -> str:
        """Build text with positioning and effects for a single word."""
        clean_word = self._escape_ass_text(word['word'])
        
        if is_active:
            # Active words: center position, fade in/out, karaoke highlight
            effects = [
                f"\\\\pos({self.center_x},{pos_y})",  # Center positioning
                "\\\\fad(100,100)",  # 100ms fade in/out
                "\\\\t(\\\\fscx110\\\\fscy110)",  # Scale to 110% over time
            ]
            text = "".join(effects) + clean_word
        else:
            # Inactive words: simpler positioning, no effects
            text = f"\\\\pos({self.center_x},{pos_y}){clean_word}"
        
        return text
    
    def _escape_ass_text(self, text: str) -> str:
        """Escape special characters for ASS format."""
        if not isinstance(text, str):
            text = str(text)
        
        # Escape ASS special characters
        text = text.replace('\\\\', '\\\\\\\\')
        text = text.replace('{', '\\\\{')
        text = text.replace('}', '\\\\}')
        
        return text
    
    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.CC)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        # ASS uses centiseconds (2 decimal places)
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
    
    def build_karaoke_line(self, words: List[Dict], style_config: Dict) -> str:
        """
        Alternative: Build a single karaoke line with \\k tags (experimental).
        This creates one line with karaoke timing instead of individual words.
        """
        if not words:
            return ""
        
        # Calculate total duration
        start_time = words[0]['start']
        end_time = words[-1]['end']
        
        ass_start = self._seconds_to_ass_time(start_time)
        ass_end = self._seconds_to_ass_time(end_time)
        
        # Build karaoke text with \\k tags
        karaoke_text = f"\\\\pos({self.center_x},{self.base_y})"
        
        for i, word in enumerate(words):
            # Calculate duration in centiseconds for \\k tag
            duration_cs = int((word['end'] - word['start']) * 100)
            
            # Style based on active status
            if word.get('active', True):
                karaoke_text += f"{{\\\\k{duration_cs}}}{self._escape_ass_text(word['word'])} "
            else:
                # Inactive words with different styling
                karaoke_text += f"{{\\\\k{duration_cs}\\\\alpha&H80&}}{self._escape_ass_text(word['word'])} "
        
        return f"Dialogue: 0,{ass_start},{ass_end},WordActive,,0,0,0,,{karaoke_text}"


def build_karaoke_ass(words: List[Dict], 
                     style_config: Dict, 
                     video_width: int = 576, 
                     video_height: int = 1024) -> str:
    """
    Convenience function to build karaoke ASS content.
    
    Args:
        words: List of word dictionaries with timing and active status
        style_config: Style configuration
        video_width: Video width for positioning
        video_height: Video height for positioning
        
    Returns:
        Complete ASS subtitle content
    """
    builder = ASSBuilder(video_width, video_height)
    return builder.build_ass_content(words, style_config)


def estimate_reading_load(words: List[Dict]) -> Dict:
    """
    Estimate cognitive reading load for the caption sequence.
    
    Args:
        words: List of timed words
        
    Returns:
        Dictionary with reading load metrics
    """
    if not words:
        return {}
    
    total_duration = words[-1]['end'] - words[0]['start']
    active_words = [w for w in words if w.get('active', True)]
    
    # Calculate metrics
    words_per_second = len(active_words) / total_duration if total_duration > 0 else 0
    avg_word_duration = sum(w['end'] - w['start'] for w in active_words) / len(active_words) if active_words else 0
    
    # Determine reading difficulty
    if words_per_second > 3.5:
        difficulty = "Very Hard"
    elif words_per_second > 2.5:
        difficulty = "Hard" 
    elif words_per_second > 1.5:
        difficulty = "Medium"
    else:
        difficulty = "Easy"
    
    return {
        'total_words': len(words),
        'active_words': len(active_words),
        'words_per_second': words_per_second,
        'avg_word_duration_ms': avg_word_duration * 1000,
        'reading_difficulty': difficulty,
        'total_duration': total_duration,
        'recommended_min_duration': 0.4 if words_per_second > 2.5 else 0.3
    }


if __name__ == "__main__":
    # Test script
    test_words = [
        {'word': 'One', 'start': 0.0, 'end': 0.5, 'active': True},
        {'word': 'of', 'start': 0.5, 'end': 0.8, 'active': False},
        {'word': 'my', 'start': 0.8, 'end': 1.1, 'active': False},
        {'word': 'favorite', 'start': 1.1, 'end': 1.8, 'active': True},
        {'word': 'things', 'start': 1.8, 'end': 2.3, 'active': True},
    ]
    
    test_style = {
        'fontSize': 42,
        'font': 'Poppins-SemiBold',
        'primaryColour': '&H00FFFFFF',
        'outlineColour': '&H00000000',
        'outline': 1
    }
    
    print("Testing ASS builder...")
    
    builder = ASSBuilder()
    ass_content = builder.build_ass_content(test_words, test_style)
    
    print("Generated ASS content:")
    print(ass_content[:500] + "..." if len(ass_content) > 500 else ass_content)
    
    load_stats = estimate_reading_load(test_words)
    print(f"\\nReading load: {load_stats['reading_difficulty']} ({load_stats['words_per_second']:.1f} words/sec)")