import re
from collections import Counter
import math


class CavemanCompressor:
    def __init__(self, reduction=0.5, min_words=5):
        self.reduction = reduction
        self.min_words = min_words

        self.stopwords = set([
            "the","a","an","and","or","but","if","then","so",
            "very","really","just","please","could","would",
            "should","can","will","be","is","are","was","were",
            "this","that","these","those","with","about","into",
            "from","by","as","it","you","we","they","your"
        ])

    # --- CLEAN ---
    def clean(self, text):
        text = text.lower()
        text = re.sub(r"[^\w\s:.]", "", text)
        return text

    # --- SPLIT ---
    def split_sentences(self, text):
        return [s.strip() for s in re.split(r"[.:\n]", text) if s.strip()]

    # --- WORD SCORE ---
    def word_scores(self, words):
        freq = Counter(words)
        max_freq = max(freq.values()) if freq else 1

        scores = {}
        for w in words:
            if w in self.stopwords:
                continue
            scores[w] = freq[w] / max_freq

        return scores

    # --- SENTENCE SCORE ---
    def sentence_score(self, sentence, scores):
        words = sentence.split()
        if not words:
            return 0

        score = sum(scores.get(w, 0) for w in words)
        return score / len(words)

    # --- COMPRESS ---
    def compress(self, text):
        text = self.clean(text)
        sentences = self.split_sentences(text)

        all_words = text.split()
        scores = self.word_scores(all_words)

        ranked = sorted(
            sentences,
            key=lambda s: self.sentence_score(s, scores),
            reverse=True
        )

        target_sentences = max(1, int(len(sentences) * (1 - self.reduction)))
        selected = ranked[:target_sentences]

        # --- trim words inside sentences ---
        final = []
        for s in selected:
            words = [w for w in s.split() if w not in self.stopwords]

            target_len = max(self.min_words, int(len(words) * 0.7))
            final.append(" ".join(words[:target_len]))

        return "\n".join(final)

cave = CavemanCompressor(reduction=0.6)

prompt = """
You are a highly skilled data analyst with years of experience.
Please analyze the dataset and provide detailed insights about trends,
patterns, and anomalies. Make sure the explanation is clear and complete.
"""

print(cave.compress(prompt))
