"""Veil Campus Access: command-line walkthrough of the pitch prototype.

Run:  python demo.py
      python demo.py --photo me.jpg     (needs the optional face_recognition package)

Follows one student through the same five steps as the web prototype, then
revokes their face key and runs the breach test.
"""

from __future__ import annotations

import argparse

import numpy as np

from veil import Veil
from veil import templates
from veil.ledger import short

STUDENTS = {
    "Sofía M.": ("IE-24-0142", 11),
    "Kenji T.": ("IE-24-0387", 29),
    "Amara O.": ("IE-23-1120", 47),
}


def heading(n: int, text: str) -> None:
    print(f"\n[{n}] {text}\n" + "-" * (len(text) + 4))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--student", default="Sofía M.", choices=STUDENTS)
    parser.add_argument("--photo", help="enrol from a real photo instead of a sample student")
    parser.add_argument("--gate", default="Tower lobby turnstile")
    args = parser.parse_args()

    veil = Veil()
    rng = np.random.default_rng()

    # 1 · Capture
    heading(1, "Capture")
    if args.photo:
        raw = templates.template_from_image(args.photo)
        name, student_id = "You", "IE-UPLOAD"
        print(f"    Read {args.photo}. The photo is discarded after this step.")
    else:
        name = args.student
        student_id, seed = STUDENTS[name]
        raw = templates.simulated_template(seed)
        print(f"    {name} ({student_id}) stands at the enrolment camera.")

    # 2 · Template
    heading(2, "Turn the face into numbers, then delete the photo")
    print(f"    Raw template: {raw.size} numbers, e.g. {np.round(raw[:4], 3).tolist()} …")
    print("    Photo wiped. The raw template is still sensitive, so it is protected next.")

    # 3 + 4 · Protect and anchor (enroll does both)
    heading(3, "Scramble with a revocable key, encrypt, split the key 2-of-3")
    wallet = veil.enroll(student_id, raw)
    print(f"    Salt:        {wallet.salt.hex()}")
    print(f"    Ciphertext:  {wallet.ciphertext.hex_preview(48)} ({len(wallet.ciphertext.data)} bytes, AES-256-GCM)")
    print(f"    Key shares:  phone {wallet.phone_share.preview()} · "
          f"campus HSM {veil.campus_hsm[wallet.did].preview()} · "
          f"vault {veil.recovery_vault[wallet.did].preview()}")

    heading(4, "Anchor on the campus ledger")
    print(f"    Pseudonymous ID: {wallet.did}")
    veil.ledger.print_tail(1)
    print("    Never written anywhere central: the photo, the raw template, the name, the full key.")

    # 5 · Gate
    heading(5, f"At the gate: {args.gate}")
    same = veil.verify(wallet, templates.live_capture(raw, rng=rng), args.gate)
    print(f"    {name} walks up:      {'ACCESS GRANTED' if same.granted else 'ACCESS DENIED'}"
          f"  (similarity {same.similarity:.1f}%, distance {same.distance:.3f})")
    other_seed = next(s for n, (_, s) in STUDENTS.items() if n != name) + 3
    other = veil.verify(wallet, templates.live_capture(templates.simulated_template(other_seed), rng=rng), args.gate)
    print(f"    Someone else walks up: {'ACCESS GRANTED' if other.granted else 'ACCESS DENIED'}"
          f"  (similarity {other.similarity:.1f}%)")
    print("    The gate learned only 'valid student' or 'no match'.")
    veil.ledger.print_tail(2)

    # Revoke
    heading(6, "Phone stolen? Revoke and re-issue the face key")
    old_wallet = wallet
    wallet, gap = veil.revoke_and_reissue(wallet, raw)
    stolen = veil.verify(old_wallet, templates.live_capture(raw, rng=rng), args.gate)
    fresh = veil.verify(wallet, templates.live_capture(raw, rng=rng), args.gate)
    print(f"    Old vs new protected template distance: {gap:.2f} (match needs ≤ {templates.MATCH_THRESHOLD})")
    print(f"    Thief with the old wallet: {'GRANTED' if stolen.granted else 'DENIED'} ({stolen.reason})")
    print(f"    {name} with the new wallet: {'GRANTED' if fresh.granted else 'DENIED'}. Same face, no re-scan.")

    # Breach
    heading(7, "Stress test: someone steals the whole campus server")
    print("    Typical face-entry system today:")
    for n, (sid, _) in STUDENTS.items():
        print(f"      × {sid}_face.jpg · {n}")
    print("      × face_templates.db · plaintext · faces exposed for life")
    print("    Veil:")
    for line in veil.breach_report():
        print(f"      + {line}")

    print(f"\nLedger: {len(veil.ledger.blocks)} blocks, chain valid = {veil.ledger.verify_chain()}")


if __name__ == "__main__":
    main()
