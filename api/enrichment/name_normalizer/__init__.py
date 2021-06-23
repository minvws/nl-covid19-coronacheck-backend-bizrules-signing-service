# Copyright (c) 2020-2021 De Staat der Nederlanden, Ministerie van Volksgezondheid, Welzijn en Sport.
#
# Licensed under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
#
# SPDX-License-Identifier: EUPL-1.2
#
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


def normalize_name(name):
    encoded = transliterate(name, dictionary=TRANSLITERATION)
    encoded = encoded.upper()
    encoded = re.sub(r"[^A-Z<]+", "", encoded)
    return encoded
