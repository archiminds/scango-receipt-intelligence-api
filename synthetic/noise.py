import random
import re
from typing import List


class NoiseGenerator:
    """Generates OCR-like noise for synthetic receipt text."""

    OCR_ERRORS = {
        'character_substitutions': {
            'a': ['4', '@', 'o'],
            'e': ['3', '€'],
            'i': ['1', 'l', '!'],
            'o': ['0', 'a'],
            's': ['5', '$'],
            't': ['7', '+'],
            'l': ['1', 'i'],
            'g': ['9', 'q'],
            'b': ['6', '8'],
            'z': ['2'],
            'S': ['5', '$'],
            'O': ['0'],
            'I': ['1', 'l'],
            'B': ['8'],
        },
        'missing_characters': ['a', 'e', 'i', 'o', 'u', 't', 's'],
        'extra_characters': [' ', '.', ',', 'l', '1', '0'],
    }

    @staticmethod
    def add_ocr_noise(text: str, noise_level: float = 0.1) -> str:
        """Add OCR-like noise to text."""
        if noise_level <= 0:
            return text

        words = text.split()
        noisy_words = []

        for word in words:
            if random.random() < noise_level:
                word = NoiseGenerator._add_word_noise(word)
            noisy_words.append(word)

        return ' '.join(noisy_words)

    @staticmethod
    def _add_word_noise(word: str) -> str:
        """Add noise to a single word."""
        noise_type = random.choice(['substitute', 'missing', 'extra', 'case'])

        if noise_type == 'substitute':
            return NoiseGenerator._substitute_characters(word)
        elif noise_type == 'missing':
            return NoiseGenerator._remove_characters(word)
        elif noise_type == 'extra':
            return NoiseGenerator._add_characters(word)
        elif noise_type == 'case':
            return NoiseGenerator._change_case(word)

        return word

    @staticmethod
    def _substitute_characters(word: str) -> str:
        """Substitute characters with OCR-like errors."""
        chars = list(word)
        for i, char in enumerate(chars):
            if char in NoiseGenerator.OCR_ERRORS['character_substitutions']:
                if random.random() < 0.3:  # 30% chance
                    substitutes = NoiseGenerator.OCR_ERRORS['character_substitutions'][char]
                    chars[i] = random.choice(substitutes)

        return ''.join(chars)

    @staticmethod
    def _remove_characters(word: str) -> str:
        """Remove random characters."""
        if len(word) <= 2:
            return word

        chars = list(word)
        # Remove 1-2 characters
        remove_count = random.randint(1, min(2, len(word) - 1))
        for _ in range(remove_count):
            if chars:
                idx = random.randint(0, len(chars) - 1)
                chars.pop(idx)

        return ''.join(chars)

    @staticmethod
    def _add_characters(word: str) -> str:
        """Add random characters."""
        chars = list(word)
        # Add 1-2 characters
        add_count = random.randint(1, 2)
        extras = NoiseGenerator.OCR_ERRORS['extra_characters']

        for _ in range(add_count):
            idx = random.randint(0, len(chars))
            char = random.choice(extras)
            chars.insert(idx, char)

        return ''.join(chars)

    @staticmethod
    def _change_case(word: str) -> str:
        """Randomly change case of characters."""
        chars = list(word)
        for i, char in enumerate(chars):
            if random.random() < 0.5:
                chars[i] = char.upper() if char.islower() else char.lower()

        return ''.join(chars)

    @staticmethod
    def add_layout_noise(text: str) -> str:
        """Add layout-related noise (line breaks, spacing)."""
        lines = text.split('\n')
        noisy_lines = []

        for line in lines:
            if random.random() < 0.2:  # 20% chance
                # Add extra spaces or line breaks
                if random.random() < 0.5:
                    line = re.sub(r'(\w)', r'\1  ', line)  # Extra spaces
                else:
                    # Split line
                    words = line.split()
                    if len(words) > 2:
                        split_idx = random.randint(1, len(words) - 1)
                        line = ' '.join(words[:split_idx]) + '\n' + ' '.join(words[split_idx:])

            noisy_lines.append(line)

        return '\n'.join(noisy_lines)