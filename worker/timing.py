#!/usr/bin/env python3
"""
Advanced timing optimization for karaoke captions.
Ensures readable word durations while maintaining natural speech rhythm.
"""

import math
from typing import List, Dict, Tuple, Optional


class TimingOptimizer:
    """Advanced timing optimization for word-level captions."""
    
    def __init__(self, 
                 min_duration: float = 0.45,
                 max_duration: float = 1.5,
                 gap_merge_threshold: float = 0.10,
                 active_word_bonus: float = 0.2):
        """
        Initialize timing optimizer with configurable parameters.
        
        Args:
            min_duration: Minimum word display time (seconds)
            max_duration: Maximum word display time (seconds) 
            gap_merge_threshold: Merge gaps shorter than this (seconds)
            active_word_bonus: Extra time for active/important words (seconds)
        """
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.gap_merge_threshold = gap_merge_threshold
        self.active_word_bonus = active_word_bonus
    
    def optimize_timing(self, words_data: List[Dict], clip_duration: Optional[float] = None) -> List[Dict]:
        """
        Optimize word timing for readability while preserving natural rhythm.
        
        Args:
            words_data: List of word dicts with 'word', 'start', 'end', 'active' keys
            clip_duration: Total clip duration to clamp final word timing
            
        Returns:
            Words with optimized timing
        """
        if not words_data:
            return words_data
        
        # Sort by start time to ensure proper order
        words = sorted(words_data, key=lambda w: w['start'])
        
        # Phase 1: Apply minimum durations and gaps
        words = self._apply_minimum_durations(words)
        
        # Phase 2: Merge short gaps between words
        words = self._merge_short_gaps(words)
        
        # Phase 3: Resolve overlaps
        words = self._resolve_overlaps(words)
        
        # Phase 4: Apply maximum durations
        words = self._apply_maximum_durations(words)
        
        # Phase 5: Clamp to clip duration
        if clip_duration:
            words = self._clamp_to_clip_duration(words, clip_duration)
        
        # Phase 6: Final validation
        words = self._validate_timing(words)
        
        return words
    
    def _apply_minimum_durations(self, words: List[Dict]) -> List[Dict]:
        """Ensure all words meet minimum duration requirements."""
        optimized_words = []
        
        for word in words:
            optimized_word = word.copy()
            
            current_duration = word['end'] - word['start']
            min_dur = self.min_duration
            
            # Give active words extra time
            if word.get('active', True):
                min_dur += self.active_word_bonus
            
            if current_duration < min_dur:
                # Extend end time first
                optimized_word['end'] = word['start'] + min_dur
            
            optimized_words.append(optimized_word)
        
        return optimized_words
    
    def _merge_short_gaps(self, words: List[Dict]) -> List[Dict]:
        """Merge words separated by very short gaps."""
        if len(words) <= 1:
            return words
        
        merged_words = [words[0].copy()]
        
        for i in range(1, len(words)):
            current_word = words[i].copy()
            prev_word = merged_words[-1]
            
            gap = current_word['start'] - prev_word['end']
            
            if gap <= self.gap_merge_threshold:
                # Merge by extending previous word to current word start
                prev_word['end'] = current_word['start']
                merged_words[-1] = prev_word
            
            merged_words.append(current_word)
        
        return merged_words
    
    def _resolve_overlaps(self, words: List[Dict]) -> List[Dict]:
        """Resolve overlapping word timings."""
        if len(words) <= 1:
            return words
        
        resolved_words = []
        
        for i, word in enumerate(words):
            current_word = word.copy()
            
            # Check for overlap with next word
            if i + 1 < len(words):
                next_word = words[i + 1]
                
                if current_word['end'] > next_word['start']:
                    # Calculate overlap split point
                    overlap_start = next_word['start']
                    overlap_end = current_word['end']
                    overlap_duration = overlap_end - overlap_start
                    
                    # Split overlap 70/30 favoring the word that starts first
                    split_point = overlap_start + (overlap_duration * 0.3)
                    
                    # Leave small buffer between words
                    buffer = 0.05  # 50ms buffer
                    current_word['end'] = split_point - buffer
                    
                    # Ensure minimum duration is still met
                    if current_word['end'] - current_word['start'] < self.min_duration * 0.75:
                        # Adjust by moving start time backward slightly
                        potential_start = current_word['end'] - self.min_duration * 0.75
                        if i > 0:
                            prev_end = resolved_words[-1]['end'] if resolved_words else 0
                            current_word['start'] = max(potential_start, prev_end + 0.05)
                        else:
                            current_word['start'] = max(potential_start, 0)
            
            resolved_words.append(current_word)
        
        return resolved_words
    
    def _apply_maximum_durations(self, words: List[Dict]) -> List[Dict]:
        """Apply maximum duration limits to prevent words hanging too long."""
        limited_words = []
        
        for word in words:
            limited_word = word.copy()
            
            duration = word['end'] - word['start']
            if duration > self.max_duration:
                limited_word['end'] = word['start'] + self.max_duration
            
            limited_words.append(limited_word)
        
        return limited_words
    
    def _clamp_to_clip_duration(self, words: List[Dict], clip_duration: float) -> List[Dict]:
        """Ensure no word extends beyond the clip duration."""
        clamped_words = []
        
        for word in words:
            clamped_word = word.copy()
            
            if clamped_word['end'] > clip_duration:
                clamped_word['end'] = clip_duration
            
            if clamped_word['start'] >= clip_duration:
                # Skip words that start after clip ends
                continue
            
            # Ensure word still has minimum duration after clamping
            if clamped_word['end'] - clamped_word['start'] < 0.1:  # 100ms minimum
                clamped_word['start'] = max(0, clamped_word['end'] - 0.1)
            
            clamped_words.append(clamped_word)
        
        return clamped_words
    
    def _validate_timing(self, words: List[Dict]) -> List[Dict]:
        """Final validation to ensure timing consistency."""
        validated_words = []
        
        for word in words:
            validated_word = word.copy()
            
            # Ensure end is always after start
            if validated_word['end'] <= validated_word['start']:
                validated_word['end'] = validated_word['start'] + 0.3
            
            # Ensure non-negative start time
            if validated_word['start'] < 0:
                validated_word['start'] = 0
                validated_word['end'] = max(validated_word['end'], 0.3)
            
            validated_words.append(validated_word)
        
        return validated_words
    
    def get_timing_stats(self, words: List[Dict]) -> Dict:
        """Get statistics about timing optimization."""
        if not words:
            return {}
        
        durations = [w['end'] - w['start'] for w in words]
        gaps = []
        
        for i in range(len(words) - 1):
            gap = words[i + 1]['start'] - words[i]['end']
            gaps.append(gap)
        
        return {
            'total_words': len(words),
            'duration_stats': {
                'min': min(durations),
                'max': max(durations),
                'avg': sum(durations) / len(durations),
                'median': sorted(durations)[len(durations) // 2]
            },
            'gap_stats': {
                'min': min(gaps) if gaps else 0,
                'max': max(gaps) if gaps else 0,
                'avg': sum(gaps) / len(gaps) if gaps else 0,
                'negative_gaps': len([g for g in gaps if g < 0])
            },
            'timing_range': {
                'start': words[0]['start'],
                'end': words[-1]['end'],
                'total_duration': words[-1]['end'] - words[0]['start']
            }
        }


def optimize_word_timing(words_data: List[Dict], 
                        clip_duration: Optional[float] = None,
                        min_duration: float = 0.45,
                        max_duration: float = 1.5) -> List[Dict]:
    """
    Convenience function for timing optimization.
    
    Args:
        words_data: List of word dictionaries
        clip_duration: Optional clip duration for clamping
        min_duration: Minimum word display time
        max_duration: Maximum word display time
        
    Returns:
        Words with optimized timing
    """
    optimizer = TimingOptimizer(min_duration=min_duration, max_duration=max_duration)
    return optimizer.optimize_timing(words_data, clip_duration)


def calculate_reading_speed(words: List[Dict]) -> float:
    """
    Calculate effective reading speed in words per minute.
    
    Args:
        words: List of timed words
        
    Returns:
        Reading speed in WPM
    """
    if len(words) < 2:
        return 0
    
    total_duration = words[-1]['end'] - words[0]['start']
    if total_duration <= 0:
        return 0
    
    words_per_minute = (len(words) * 60) / total_duration
    return words_per_minute


if __name__ == "__main__":
    # Test script
    test_words = [
        {'word': 'One', 'start': 0.02, 'end': 0.13, 'active': True},
        {'word': 'of', 'start': 0.15, 'end': 0.21, 'active': False},
        {'word': 'favorite', 'start': 0.29, 'end': 0.64, 'active': True},
        {'word': 'things', 'start': 0.64, 'end': 0.9, 'active': True},
        {'word': 'really', 'start': 7.64, 'end': 8.04, 'active': True},
    ]
    
    print("Testing timing optimization...")
    print("\nOriginal timing:")
    for word in test_words:
        duration = (word['end'] - word['start']) * 1000
        print(f"  {word['word']:10s}: {duration:3.0f}ms ({word['start']:.2f}s-{word['end']:.2f}s)")
    
    optimizer = TimingOptimizer()
    optimized = optimizer.optimize_timing(test_words, clip_duration=10.0)
    
    print("\nOptimized timing:")
    for word in optimized:
        duration = (word['end'] - word['start']) * 1000
        print(f"  {word['word']:10s}: {duration:3.0f}ms ({word['start']:.2f}s-{word['end']:.2f}s)")
    
    stats = optimizer.get_timing_stats(optimized)
    print(f"\nStats: {stats['total_words']} words, avg duration: {stats['duration_stats']['avg']*1000:.0f}ms")
    print(f"Reading speed: {calculate_reading_speed(optimized):.0f} WPM")