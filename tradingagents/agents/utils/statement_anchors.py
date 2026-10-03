"""Structural boundaries for application-owned complete fact sentences.

This prevents a model from attaching another unit/subject/negation to an owned
statement. It is not a general semantic entailment or translation validator.
"""

import re


def non_standalone_anchors(text, anchors):
    failures = []
    for anchor in anchors:
        for occurrence in re.finditer(re.escape(anchor), text):
            before, after = text[:occurrence.start()], text[occurrence.end():]
            if ((before.strip() and not re.search(r"(?:[.!?]\s*|\n[ \t]*)$", before))
                    or (after.strip() and not after.startswith((".", "\n")))):
                failures.append(anchor)
                break
    return failures
