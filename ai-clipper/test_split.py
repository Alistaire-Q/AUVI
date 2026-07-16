"""Debug: kenapa split tidak bekerja?"""
import sys, re
sys.path.insert(0, "backend")

def is_sentence_end(word):
    if not word: return False
    return bool(re.search(r'[.!?][\'"”’\]\)]*$', word.strip()))

# Simulasi words
words = []
for i in range(1320):
    start = i * 0.5
    end = start + 0.4
    word = f"kata{i}"
    if i > 0 and i % 20 == 0:
        word += "."
    words.append({"word": word, "start": round(start, 3), "end": round(end, 3)})

# Count boundaries
boundaries = [w for w in words if is_sentence_end(w["word"])]
print(f"\nBoundaries found: {len(boundaries)}")

from services.analyzer import _split_long_clips, _force_split_single_clip

clip = {
    "start": 0.0, "end": 659.9, "duration": 659.9,
    "score": 80, "category": "Key Point", "title": "Test", "words": words
}

print(f"\n=== Test 1: _split_long_clips ===")
result = _split_long_clips([clip], words)
print(f"Output: {len(result)} clips")
for c in result:
    print(f"  Clip {c['index']}: {c['start']:.1f}s - {c['end']:.1f}s ({c['duration']:.0f}s)")

print(f"\n=== Test 2: _force_split_single_clip ===")
result2 = _force_split_single_clip([clip], words, 659.9, 5)
print(f"Output: {len(result2)} clips")
for c in result2:
    print(f"  Clip {c['index']}: {c['start']:.1f}s - {c['end']:.1f}s ({c['duration']:.0f}s)")

if len(result) > 1 or len(result2) > 1:
    print("SUCCESS")
else:
    print("FAILED")
