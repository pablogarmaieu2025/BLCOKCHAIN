"""Veil Campus Access: clickable web version of the pitch prototype.

Run:  pip install streamlit
      streamlit run app.py
"""

from __future__ import annotations

import numpy as np
import streamlit as st

from veil import Veil, templates
from veil.ledger import short

STUDENTS = {"Sofía M.": ("IE-24-0142", 11), "Kenji T.": ("IE-24-0387", 29), "Amara O.": ("IE-23-1120", 47)}
GATES = ["Tower lobby turnstile", "Library entrance", "Residence hall door", "Exam room 3.07"]

st.set_page_config(page_title="Veil Campus Access", layout="wide")

if "veil" not in st.session_state:
    st.session_state.veil = Veil()
    st.session_state.wallet = None
    st.session_state.raw = None
    st.session_state.name = None
veil: Veil = st.session_state.veil

st.title("Veil Campus Access")
st.caption("Your face opens the door. Nobody gets to keep it. Pitch prototype, simulated end to end.")

flow, ledger_col = st.columns([2, 1])

with flow:
    st.subheader("1 · Enrol")
    name = st.selectbox("Who is enrolling?", list(STUDENTS))
    photo = st.file_uploader("…or upload a photo (needs face_recognition)", type=["jpg", "jpeg", "png"])
    if st.button("Enrol: extract, protect, anchor", type="primary"):
        try:
            if photo is not None:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".jpg") as f:
                    f.write(photo.getvalue()); f.flush()
                    raw = templates.template_from_image(f.name)
                name, sid = "You", "IE-UPLOAD"
            else:
                sid, seed = STUDENTS[name]
                raw = templates.simulated_template(seed)
            st.session_state.raw = raw
            st.session_state.name = name
            st.session_state.wallet = veil.enroll(sid, raw)
        except Exception as e:  # shown to the user, e.g. no face found
            st.error(str(e))

    wallet = st.session_state.wallet
    if wallet:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Raw template · 128 numbers** (photo already wiped)")
            st.bar_chart(st.session_state.raw, height=140)
        with c2:
            st.markdown("**Protected template · 64 numbers** (one-way, revocable)")
            st.bar_chart(templates.protect(st.session_state.raw, wallet.salt), height=140)
        st.code(
            f"Pseudonymous ID  {wallet.did}\n"
            f"Salt             {wallet.salt.hex()}\n"
            f"Ciphertext       {wallet.ciphertext.hex_preview(40)} (AES-256-GCM, in the wallet app)\n"
            f"Key shares       phone · campus HSM · recovery vault (any 2 of 3)",
            language=None,
        )

        st.subheader("2 · At the gate")
        gate = st.selectbox("Gate", GATES)
        a, b = st.columns(2)
        rng = np.random.default_rng()
        if a.button(f"{st.session_state.name} walks up"):
            r = veil.verify(wallet, templates.live_capture(st.session_state.raw, rng=rng), gate)
            (st.success if r.granted else st.error)(f"{'ACCESS GRANTED' if r.granted else 'ACCESS DENIED'} · similarity {r.similarity:.1f}%")
        if b.button("Someone else walks up"):
            r = veil.verify(wallet, templates.live_capture(templates.simulated_template(999), rng=rng), gate)
            (st.success if r.granted else st.error)(f"{'ACCESS GRANTED' if r.granted else 'ACCESS DENIED'} · similarity {r.similarity:.1f}%")

        st.subheader("3 · Phone stolen or template leaked?")
        if st.button("Revoke and re-issue my face key"):
            old = wallet
            st.session_state.wallet, gap = veil.revoke_and_reissue(wallet, st.session_state.raw)
            thief = veil.verify(old, templates.live_capture(st.session_state.raw, rng=rng), "Thief test")
            st.info(f"Old vs new template distance {gap:.2f} (a match needs ≤ {templates.MATCH_THRESHOLD}). "
                    f"Thief with the old wallet: {'granted' if thief.granted else 'denied'}. Same face, no re-scan.")

    st.subheader("Stress test · breach the campus server")
    if st.button("Run the breach"):
        x, y = st.columns(2)
        x.markdown("**Typical face-entry system**")
        x.code("\n".join([f"× {sid}_face.jpg · {n}" for n, (sid, _) in STUDENTS.items()]
                         + ["× face_templates.db · plaintext"]), language=None)
        y.markdown("**Veil**")
        y.code("\n".join(f"+ {line}" for line in veil.breach_report()), language=None)

with ledger_col:
    st.subheader("Campus chain")
    st.caption(f"Validators: Registrar · IT Security · Student Council · chain valid: {veil.ledger.verify_chain()}")
    for blk in reversed(veil.ledger.blocks):
        with st.container(border=True):
            st.markdown(f"**#{blk.index} {blk.kind}** · {blk.timestamp[11:19]}")
            for k, v in blk.fields.items():
                st.caption(f"{k}: {short(v) if isinstance(v, str) and len(v) == 64 else v}")
            st.caption(f"hash: {short(blk.hash)}")
