#!/usr/bin/env python3
"""
Smart word filtering for karaoke captions using SpaCy POS tagging.
Context-aware filtering that preserves semantically important words.
"""

import re
from typing import List, Dict, Set, Tuple


class WordFilter:
    """Smart word filtering with context awareness."""
    
    def __init__(self):
        # Try to import and load SpaCy model
        self.nlp = None
        self._load_spacy()
        
        # Fallback stop words (used if SpaCy is not available)
        self.fallback_stop_words = {
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
            # Pronouns (but keep personal pronouns in some contexts)
            'it', 'its', 'they', 'them', 'their', 'theirs',
            # Common words
            'that', 'this', 'these', 'those', 'some', 'any', 'all', 'each', 'every', 
            'very', 'too', 'also', 'then', 'than', 'now', 'here', 'there', 'yes', 'yeah', 'ok', 'okay'
        }
        
        # Preserve these words even if they're typically filtered
        self.preserve_patterns = {
            'emphasis': {'really', 'very', 'super', 'totally', 'absolutely', 'definitely'},
            'direction': {'up', 'down', 'in', 'out', 'over', 'under', 'through'},
            'important_pronouns': {'i', 'me', 'you', 'we', 'us'},  # Keep personal pronouns
            'questions': {'what', 'when', 'where', 'why', 'how', 'who', 'which'}
        }
    
    def _load_spacy(self):
        """Load SpaCy model if available."""
        try:
            import spacy
            # Try different model sizes, fallback gracefully
            models_to_try = ['en_core_web_sm', 'en_core_web_md', 'en_core_web_lg']
            
            for model_name in models_to_try:
                try:
                    self.nlp = spacy.load(model_name)
                    print(f"Loaded SpaCy model: {model_name}", flush=True)
                    break
                except OSError:
                    continue
                    
            if not self.nlp:
                print("No SpaCy model found. Install with: python -m spacy download en_core_web_sm", flush=True)
                print("Using fallback stop word filtering...", flush=True)
                
        except ImportError:
            print("SpaCy not installed. Install with: pip install spacy", flush=True)
            print("Using fallback stop word filtering...", flush=True)
    
    def filter_words(self, words_data: List[Dict], show_filler: bool = False) -> List[Dict]:
        """
        Filter words based on importance and context.
        
        Args:
            words_data: List of word dicts with 'word', 'start', 'end' keys
            show_filler: If True, mark filler words as inactive instead of removing them
            
        Returns:
            Filtered word list with 'active' field indicating importance
        """
        if not words_data:
            return words_data
        
        # Add full text context for better analysis
        full_text = ' '.join(word['word'] for word in words_data)
        
        if self.nlp:
            return self._filter_with_spacy(words_data, full_text, show_filler)
        else:
            return self._filter_with_fallback(words_data, show_filler)
    
    def _filter_with_spacy(self, words_data: List[Dict], full_text: str, show_filler: bool) -> List[Dict]:
        """Use SpaCy POS tagging for intelligent filtering."""
        doc = self.nlp(full_text)
        
        # Create mapping of words to their linguistic properties
        word_properties = {}
        for token in doc:
            word_properties[token.text.lower()] = {
                'pos': token.pos_,
                'tag': token.tag_,
                'dep': token.dep_,
                'is_stop': token.is_stop,
                'is_alpha': token.is_alpha,
                'lemma': token.lemma_.lower()
            }
        
        filtered_words = []
        
        for i, word_data in enumerate(words_data):
            word = word_data['word'].lower()
            
            # Default to active
            is_active = True
            
            # Get linguistic properties
            props = word_properties.get(word, {})
            
            # Determine if word should be filtered
            if self._should_filter_word(word, props, words_data, i):
                is_active = False
            
            # Override: preserve contextually important words
            if self._should_preserve_word(word, props, words_data, i):
                is_active = True
            
            # Add word to result
            word_result = word_data.copy()
            word_result['active'] = is_active
            
            # Only include if showing fillers OR word is active
            if show_filler or is_active:
                filtered_words.append(word_result)
        
        return filtered_words
    
    def _filter_with_fallback(self, words_data: List[Dict], show_filler: bool) -> List[Dict]:
        """Fallback filtering using simple stop word list."""
        filtered_words = []
        
        for i, word_data in enumerate(words_data):
            word = word_data['word'].lower()
            
            # Check if word should be filtered
            is_active = True
            
            # Filter common stop words
            if word in self.fallback_stop_words:
                is_active = False
            
            # Preserve important words
            for category, preserve_set in self.preserve_patterns.items():
                if word in preserve_set:
                    is_active = True
                    break
            
            # Preserve if part of important context (simple heuristics)
            if self._is_contextually_important(word, words_data, i):
                is_active = True
            
            word_result = word_data.copy()
            word_result['active'] = is_active
            
            # Only include if showing fillers OR word is active
            if show_filler or is_active:
                filtered_words.append(word_result)
        
        return filtered_words
    
    def _should_filter_word(self, word: str, props: Dict, words_data: List[Dict], index: int) -> bool:
        """Determine if a word should be filtered using SpaCy analysis."""
        if not props:
            return word in self.fallback_stop_words
        
        pos = props.get('pos', '')
        tag = props.get('tag', '')
        dep = props.get('dep', '')
        is_stop = props.get('is_stop', False)
        
        # Filter based on POS tags
        filter_pos = {'DET', 'ADP', 'CCONJ', 'SCONJ', 'PART'}  # Articles, prepositions, conjunctions, particles
        if pos in filter_pos:
            return True
        
        # Filter auxiliary verbs and copulas
        if tag in {'MD', 'VBZ', 'VBP', 'VBD', 'VBN'} and dep in {'aux', 'auxpass', 'cop'}:
            return True
        
        # Filter stop words (but with exceptions)
        if is_stop and word not in {'not', 'no', 'never', 'nothing', 'nobody'}:  # Keep negations
            return True
        
        return False
    
    def _should_preserve_word(self, word: str, props: Dict, words_data: List[Dict], index: int) -> bool:
        """Determine if a word should be preserved despite being a filler."""
        # Preserve words in our special categories
        for category, preserve_set in self.preserve_patterns.items():
            if word in preserve_set:
                return True
        
        # Preserve if it's part of a short phrase (≤ 2 words)
        if self._is_short_phrase(words_data, index):
            return True
        
        # Preserve if it's an important modifier
        if props.get('pos') == 'ADV' and props.get('dep') in {'advmod', 'neg'}:
            return True
        
        # Preserve numbers and proper nouns
        if props.get('pos') in {'NUM', 'PROPN'}:
            return True
        
        return False
    
    def _is_contextually_important(self, word: str, words_data: List[Dict], index: int) -> bool:
        """Simple heuristics for contextual importance (fallback method)."""
        # Preserve if part of a very short sequence
        if len(words_data) <= 3:
            return True
        
        # Preserve if it's a number or capitalized (likely proper noun)
        if word.isdigit() or (word[0].isupper() if word else False):
            return True
        
        # Preserve negations
        if word in {'not', 'no', 'never', 'nothing', 'nobody', 'none'}:
            return True
        
        return False
    
    def _is_short_phrase(self, words_data: List[Dict], index: int) -> bool:
        """Check if word is part of a short phrase (≤ 2 words)."""
        # Simple check: if there are long gaps before/after, it might be a short phrase
        # This is a simplified version - proper implementation would use pause detection
        return len(words_data) <= 2


def filter_words(words_data: List[Dict], show_filler: bool = False) -> List[Dict]:
    """
    Convenience function for filtering words.
    
    Args:
        words_data: List of word dictionaries with 'word', 'start', 'end'
        show_filler: If True, include filler words marked as inactive
        
    Returns:
        Filtered words with 'active' field
    """
    filter_instance = WordFilter()
    return filter_instance.filter_words(words_data, show_filler)


if __name__ == "__main__":
    # Test script
    test_words = [
        {'word': 'One', 'start': 0.02, 'end': 0.13},
        {'word': 'of', 'start': 0.15, 'end': 0.21},
        {'word': 'my', 'start': 0.21, 'end': 0.29},
        {'word': 'favorite', 'start': 0.29, 'end': 0.64},
        {'word': 'things', 'start': 0.64, 'end': 0.9},
        {'word': 'to', 'start': 0.9, 'end': 0.97},
        {'word': 'do', 'start': 0.98, 'end': 1.12},
        {'word': 'is', 'start': 1.12, 'end': 1.28},
        {'word': 'working', 'start': 5.62, 'end': 6.06},
        {'word': 'really', 'start': 7.64, 'end': 8.04},
        {'word': 'hard', 'start': 8.04, 'end': 8.30},
    ]
    
    print("Testing word filtering...")
    print("\nWith filler words hidden:")
    filtered = filter_words(test_words, show_filler=False)
    for word in filtered:
        print(f"  {word['word']} ({word.get('active', True)})")
    
    print("\nWith filler words shown:")
    filtered_with_filler = filter_words(test_words, show_filler=True)
    for word in filtered_with_filler:
        active_str = "ACTIVE" if word.get('active', True) else "inactive"
        print(f"  {word['word']} ({active_str})")