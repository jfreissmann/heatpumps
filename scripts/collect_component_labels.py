"""
Collect all unique base component labels from heat pump model source files.

Parses the model source files with regex to find all Component('...') string
arguments, strips known suffixes and trailing numbers, and prints a deduplicated
sorted list of base labels ready to use as translation keys in translations.json.

Usage:
    python scripts/collect_component_labels.py
"""
import os
import re
from pathlib import Path


MODELS_DIR = Path(__file__).parent.parent / 'src' / 'heatpumps' / 'models'

# Suffixes stripped before deduplication
STRIP_SUFFIXES = [' (hot)', ' (cold)', ' Motor']
TRAILING_NUM = re.compile(r'^(.*?) \d+$')

LABEL_PATTERN = re.compile(
    r"self\.comps\[.+?\] = \w+\('([^']+)'\)"
)


def base_label(label: str) -> str:
    for suffix in STRIP_SUFFIXES:
        if label.endswith(suffix):
            label = label[: -len(suffix)]
    m = TRAILING_NUM.match(label)
    if m:
        label = m.group(1)
    return label


def main():
    all_labels: set[str] = set()
    raw_labels: set[str] = set()

    for path in sorted(MODELS_DIR.glob('HeatPump*.py')):
        text = path.read_text(encoding='utf-8')
        for match in LABEL_PATTERN.finditer(text):
            raw_labels.add(match.group(1))
            all_labels.add(base_label(match.group(1)))

    print('=== All raw labels ===')
    for lbl in sorted(raw_labels):
        print(f'  {lbl!r}')

    print()
    print('=== Unique base labels (translation keys) ===')
    for lbl in sorted(all_labels):
        key = 'comp_label_' + lbl.replace(' ', '_')
        print(f'    {key!r}: {{"ENG": {lbl!r}, "GER": "TODO"}},')


if __name__ == '__main__':
    main()