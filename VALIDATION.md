# Validation

Acceptance contract: Synthetic Latin/accent fonts cover ABé🙂 in a stable two-step plan; missing characters are explicit. Format4 delta/array and format12 non-BMP mappings, offsets, malformed tables and preferred unsupported encodings are tested. Two installed real TTF/OTF files match FontTools4.61.1 on65617 queried code points each.

The behavior suite has 16 test methods; this includes meaningful malformed-input cases. CI executes unit tests, Python compilation, wheel build and a new-environment installed-console-command check on Linux/Python 3.10, 3.12 and 3.14. A configured workflow is not proof it passed: inspect this repository's current Actions run before making a health claim.

Preparation: all behavior tests passed on Python 3.12.14. Clean wheel/CLI evidence is recorded in `PREPARATION.json` after execution. Future security advisories, all possible inputs and Windows/macOS behavior are not certified by these checks. No performance benchmark or production-use evidence is claimed.

Independent mapping reference: FontTools 4.61.1 versus this parser on DejaVuSans TTF (format12) and NimbusSans-Regular OTF (format4), 65,617 code points per font, zero mismatches. SHA256 identities and environment are in [the reference record](FONT_REFERENCE_VALIDATION.json). Fonts were read from the validation environment and are not redistributed. This does not validate shaping, outlines or every font.
