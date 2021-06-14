import re

import mrz.generator._transliterations as dictionaries
from mrz.base.functions import transliterate

# Compile universal transliteration dictionary
TRANSLITERATION = {
    **dictionaries.latin_based(),
    **dictionaries.arabic(),
    **dictionaries.greek(),
    **dictionaries.cyrillic(),
}


def normalize_name(n):
    encoded = transliterate(n, dictionary=TRANSLITERATION)
    encoded = encoded.upper()
    encoded = re.sub(r"[^A-Z<]+", "", encoded)
    return encoded
