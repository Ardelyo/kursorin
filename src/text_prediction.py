"""
Text Prediction Module
Provides word suggestions based on current input
"""

import logging
from typing import List

class TextPredictor:
    """Simple text prediction engine"""

    def __init__(self):
        # Basic dictionary of common English words (can be expanded or loaded from file)
        self.common_words = [
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
            "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
            "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
            "hello", "help", "home", "how", "happy", "here", "have", "has", "had",
            "world", "work", "word", "where", "when", "why", "write", "way",
            "good", "great", "game", "get", "go", "going", "gone", "got",
            "please", "play", "place", "people", "person", "part", "problem",
            "thanks", "thank", "that", "this", "those", "these", "time", "take"
        ]
        # Sort for binary search or just keep simple for now
        self.common_words.sort()

    def get_suggestions(self, current_input: str, max_suggestions: int = 3) -> List[str]:
        """Get word suggestions based on current input prefix"""
        if not current_input:
            return []

        current_input = current_input.lower()
        suggestions = []

        # Simple prefix matching
        for word in self.common_words:
            if word.startswith(current_input):
                suggestions.append(word)
                if len(suggestions) >= max_suggestions:
                    break
        
        return suggestions

    def learn_word(self, word: str):
        """Add a new word to the dictionary (runtime learning)"""
        if word.lower() not in self.common_words:
            self.common_words.append(word.lower())
            self.common_words.sort()
