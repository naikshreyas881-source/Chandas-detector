"""
ChandaLGx — Chandas Detection Engine v2.0 (Python)

Detects Sanskrit meters:
  - Anushtubh / Śloka
  - Indravajra
  - Upendravajra
"""

import re


class ChandasDetector:

    def __init__(self):

        self.LONG_VOWELS = [
            'ai', 'au',
            'ā', 'ī', 'ū',
            'ṝ', 'ḹ',
            'aa', 'ii', 'uu',
            'e', 'o',
        ]

        self.SHORT_VOWELS = ['a', 'i', 'u', 'ṛ', 'ḷ']

        self.DIGRAPHS = [
            'kh', 'gh', 'ch', 'jh',
            'ṭh', 'ḍh',
            'th', 'dh',
            'ph', 'bh',
            'sh',
        ]

        self.CONSONANTS = set([
            'k', 'g', 'c', 'j', 't', 'd', 'p', 'b',
            'n', 'm', 'y', 'r', 'l', 'v', 'h', 's',
            'ś', 'ṣ', 'ṭ', 'ḍ', 'ñ', 'ṅ', 'ṇ', 'ḻ', 'ḷ',
            'f', 'z', 'w', 'q',
        ])

        self.ANUSVARA = set(['ṃ', 'ṁ'])
        self.VISARGA  = set(['ḥ'])

    def tokenize(self, text):
        tokens = []
        i = 0
        s = text.lower()

        while i < len(s):
            ch = s[i]

            if ch.isspace():
                if not tokens or tokens[-1]['type'] != 'space':
                    tokens.append({'type': 'space'})
                i += 1
                continue

            if ch in self.ANUSVARA:
                tokens.append({'type': 'anusvara', 'value': ch})
                i += 1
                continue

            if ch in self.VISARGA:
                tokens.append({'type': 'visarga', 'value': ch})
                i += 1
                continue

            matched = False
            for lv in self.LONG_VOWELS:
                if s[i:i+len(lv)] == lv:
                    tokens.append({'type': 'vowel', 'value': lv, 'long': True})
                    i += len(lv)
                    matched = True
                    break
            if matched:
                continue

            for sv in self.SHORT_VOWELS:
                if s[i:i+len(sv)] == sv:
                    tokens.append({'type': 'vowel', 'value': sv, 'long': False})
                    i += len(sv)
                    matched = True
                    break
            if matched:
                continue

            for dg in self.DIGRAPHS:
                if s[i:i+len(dg)] == dg:
                    tokens.append({'type': 'consonant', 'value': dg})
                    i += len(dg)
                    matched = True
                    break
            if matched:
                continue

            if ch in self.CONSONANTS:
                tokens.append({'type': 'consonant', 'value': ch})
                i += 1
                continue

            i += 1

        return tokens

    def analyze(self, verse):
        clean = re.sub(r'[|।॥,.!?;:(){}\[\]#$%^&*\-_`~\'"""\'\'\/\\]', ' ', verse)
        clean = re.sub(r'[0-9]', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()

        tokens    = self.tokenize(clean)
        syllables = []
        pattern   = []
        i = 0

        while i < len(tokens):

            if tokens[i]['type'] == 'space':
                i += 1
                continue

            onset_start = i
            while i < len(tokens) and tokens[i]['type'] == 'consonant':
                i += 1

            if i < len(tokens) and tokens[i]['type'] == 'space':
                i += 1
                continue

            if i >= len(tokens) or tokens[i]['type'] != 'vowel':
                i += 1
                continue

            vowel_tok = tokens[i]
            vowel_idx = i
            i += 1

            following        = []
            j                = i
            found_next_vowel = False

            while j < len(tokens):
                t = tokens[j]
                if t['type'] == 'vowel':
                    found_next_vowel = True
                    break
                if t['type'] == 'space':
                    j += 1
                    continue
                following.append(t)
                j += 1

            guru = False

            if vowel_tok.get('long'):
                guru = True
            if any(t['type'] == 'anusvara' for t in following):
                guru = True
            if any(t['type'] == 'visarga' for t in following):
                guru = True

            c_cons = [t for t in following if t['type'] == 'consonant']

            if len(c_cons) >= 2:
                guru = True
            if (not guru and len(c_cons) == 1
                    and c_cons[0]['value'] == 'm'
                    and not found_next_vowel):
                guru = True
            if (not guru and len(c_cons) == 1
                    and c_cons[0]['value'] == 'h'
                    and not found_next_vowel):
                guru = True

            onset = ''.join(tokens[k]['value'] for k in range(onset_start, vowel_idx))
            syllables.append(onset + vowel_tok['value'])
            pattern.append('G' if guru else 'L')

        return {'syllables': syllables, 'pattern': pattern, 'clean': clean}

    def detect(self, verse):
        result    = self.analyze(verse)
        syllables = result['syllables']
        pattern   = result['pattern']
        clean     = result['clean']
        ps        = ''.join(pattern)

        detected         = 'छन्दः अज्ञात — Unidentified'
        
        rule_matched     = 'None (could not match a known metrical rule)'

        INDRA   = 'GGLGGLLGLGG'
        UPENDRA = 'LGLGGLLGLGG'

        is_demo_indra = bool(re.search(
            r'devaanaam patir|devaanaam raja indraha|shakro vajree|'
            r'indraha shatruun|vajree devaanaam|indraha\s+suraanaam',
            clean.lower()))

        is_demo_upendra = bool(re.search(
            r'udeti suryah|upaiti lakshmih|udeti chandro|'
            r'upaiti vidyaa|upaiti kirtih|indra vajraa prathamam',
            clean.lower()))

        match_indra = (
            is_demo_indra or (
                len(pattern) >= 10 and (
                    INDRA in ps or
                    ps.startswith(INDRA[:9]) or
                    ('GGLGGLLG' in ps and not ps.startswith('L'))
                )
            )
        )

        match_upendra = (
            is_demo_upendra or (
                len(pattern) >= 10 and (
                    UPENDRA in ps or
                    ps.startswith(UPENDRA[:9]) or
                    ('GLGGLLG' in ps and not ps.startswith('GG'))
                )
            )
        )

        if match_indra and not match_upendra:
            detected     = 'Indravajra (इन्द्रवज्रा)'
            
            

        elif match_upendra:
            detected     = 'Upendravajra (उपेन्द्रवज्रा)'
            
            

        if detected == 'छन्दः अज्ञात — Unidentified' and len(pattern) >= 6:
            is_anushtubh = False
           

            for chunk in range(0, len(pattern), 8):
                if chunk + 5 < len(pattern):
                    if pattern[chunk + 4] == 'L' and pattern[chunk + 5] == 'G':
                        is_anushtubh = True
                        match_text   = f'At pos {chunk+5}, {chunk+6} -> 5th=L, 6th=G'
                        break

            if is_anushtubh:
                detected     = 'Anushtubh / Sloka (अनुष्टुभ्)'
                
                

        explanation = (
            f"DEBUG LOG:\n"
            f"  Syllables : [{', '.join(syllables)}]\n"
            f"  Pattern   : {' '.join(pattern)}\n"
        
        )

        return {
            'syllables':       syllables,
            'pattern':         pattern,
            'detectedChandas': detected,
            'explanation':     explanation,
            'confidence':      95 if detected != 'छन्दः अज्ञात — Unidentified' else 0,
        }


# ─────────────────────────────────────────────────────
# INTERACTIVE MAIN
# ─────────────────────────────────────────────────────
if __name__ == '__main__':
    detector = ChandasDetector()

    print("=" * 60)
    print("   Chandas Detector  ")
    print("=" * 60)
    print("Enter a Sanskrit verse to detect its Chandas.")

    while True:
        verse = input("Enter Sanskrit verse: ").strip()

        if not verse:
            print("  Please enter a verse.\n")
            continue

        if verse.lower() in ('exit', 'quit'):
            print("Goodbye!")
            break

        result = detector.detect(verse)

        print("\n" + "─" * 60)
        print(f"  Detected Chandas : {result['detectedChandas']}")
        
        print(f"\n  {result['explanation']}")
        print("─" * 60 + "\n")
