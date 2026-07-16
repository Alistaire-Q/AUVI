import re

def is_sentence_end(word: str) -> bool:
    if not word:
        return False
    # Cocokkan tanda baca titik, seru, atau tanya, 
    # yang mungkin diikuti oleh tanda kutip atau kurung penutup, di akhir string
    return bool(re.search(r'[.!?][\'"”’\]\)]*$', word.strip()))

test_words = ["kata20.", "kata40.", "hello", "test!", "end?", "kata.test", "word", "quote.\"", "bracket.]"]
for w in test_words:
    print(f"  '{w}' -> is_sentence_end = {is_sentence_end(w)}")
