import re
import json
from collections import defaultdict

def parse_prescription_with_granite(raw_text: str):
    """
    Fake Granite parser using regex + collections.
    Extracts drug, dosage, frequency, and duration.
    """

    dosage_pattern = r"(\d+\s?(mg|mcg|g))"
    freq_pattern = r"(once daily|twice daily|every \d+ (hours|hrs)|od|bid|tid|qid)"
    duration_pattern = r"(\d+\s?(days?|weeks?|months?))"

    drugs = []
    tokens = raw_text.split("+")  # split on '+', common in prescriptions

    for token in tokens:
        entry = defaultdict(str)
        text = token.strip()

        # drug name (first word)
        words = text.split()
        if words:
            entry["drug"] = words[0].capitalize()

        # dosage
        match = re.search(dosage_pattern, text, re.IGNORECASE)
        if match:
            entry["dosage"] = match.group(1)

        # frequency
        match = re.search(freq_pattern, text, re.IGNORECASE)
        if match:
            entry["frequency"] = match.group(1)

        # duration
        match = re.search(duration_pattern, text, re.IGNORECASE)
        if match:
            entry["duration"] = match.group(1)

        drugs.append(entry)

    return {"parsed": drugs, "raw_text": raw_text}
