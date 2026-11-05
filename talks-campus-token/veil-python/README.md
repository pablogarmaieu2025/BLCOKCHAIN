# Veil Campus Access (Python prototype)

Your face opens the door. Nobody gets to keep it.

This is the Python version of the Veil pitch prototype. It follows one student from enrolment to the gate, revokes their face key, and runs a breach test. It's a pitch prototype only. Don't use it with real people's biometric data.

## Run it

```bash
pip install -r requirements.txt
python demo.py              # command-line walkthrough
pytest                      # 10 tests
```

Optional extras:

```bash
pip install streamlit
streamlit run app.py        # clickable web version with a live ledger

pip install face_recognition
python demo.py --photo me.jpg   # enrol from a real photo
```

`face_recognition` needs `dlib`, which can be slow to install. Everything else runs without it, using simulated face templates.

## How it works

| Step | What happens | Code |
| --- | --- | --- |
| 1. Capture | The camera takes one photo. | `templates.template_from_image` |
| 2. Template | The face becomes 128 numbers. The photo is discarded. | `templates.py` |
| 3. Protect | A salted one-way projection turns 128 numbers into 64. A new salt makes every old copy useless. | `templates.protect` |
| 4. Encrypt | AES-256-GCM. The key is split 2-of-3: phone, campus HSM, recovery vault. | `crypto.py` |
| 5. Anchor | The ledger stores a pseudonymous ID and a commitment hash, never a face or a name. Three validators approve each block (2 of 3 needed). | `ledger.py` |
| 6. Gate | The phone releases the salt and its key share. The gate checks the wallet copy against the ledger, then compares the live scan by **distance**. | `Veil.verify` |
| 7. Revoke | New salt, new template, old commitment revoked. Same face, no re-scan. | `Veil.revoke_and_reissue` |

Faces are matched by the distance between vectors, never by a hash. Two scans of the same face are never identical. The commitment hash only proves the wallet copy wasn't swapped.

## Plugging into the talks. token door

`veil/matcher.py` implements the interface the token team's door expects:

```python
from veil import TeammateFaceMatcher

matcher = TeammateFaceMatcher()
matcher.enroll("sara", "sara.jpg")       # or a template vector
matcher.identify("door_capture.jpg")     # -> "sara" or None

Door(chain, matcher, registry)           # the one-line swap in their code
```

## Files

```
veil/
  templates.py   face templates, cancellable protection, matching
  crypto.py      AES-GCM encryption and the 2-of-3 key split
  ledger.py      hash-linked permissioned chain with 3 validators
  system.py      the Veil flow: enrol, verify, revoke, breach report
  matcher.py     adapter for the talks. token door
demo.py          command-line walkthrough
app.py           Streamlit web version
tests/           pytest suite
```
