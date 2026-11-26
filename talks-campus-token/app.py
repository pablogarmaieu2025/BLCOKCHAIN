"""Unified classroom UI. Synthetic identities and ephemeral local EVM only."""
import streamlit as st
from gateway.demo_campus import DemoCampus
from gateway import to_id

st.set_page_config(page_title="Veil × talks. | V2", page_icon="🎓", layout="wide")
st.title("Veil × talks.")
st.caption("Verified participation · programmable rewards · synthetic demo")
st.warning("Classroom simulation. No real faces, funds, campus integration or production security.")
if "campus" not in st.session_state:
    st.session_state.campus = DemoCampus()
    st.session_state.history = []
c = st.session_state.campus
chain = c.chain
st.sidebar.markdown("### Try the demo\n1. Scan Sara at SG debate.\n2. Repeat the scan (0 extra TALK).\n3. Scan at Climate talk.\n4. Redeem a priority ticket in Student.\n5. Inspect Evidence.\n6. Revoke Sara in Administrator and try another scan.")
if st.sidebar.button("Reset local demonstration"):
    del st.session_state.campus
    del st.session_state.history
    st.session_state.pop("feedback", None)
    st.rerun()

def attempt(action, label):
    try:
        receipt = action()
        st.session_state.history.append((label, receipt.transactionHash.hex()))
        st.session_state.feedback = ("success", label)
    except Exception as e:
        st.session_state.feedback = ("error", f"Rejected or unavailable ({type(e).__name__})")

student_tab, gate_tab, admin_tab, ledger_tab = st.tabs(["Student", "Event scanner", "Administrator", "Evidence"])
with gate_tab:
    student = st.selectbox("Synthetic scan", [*c.raw, "unknown"], key="scan_sid")
    event = st.selectbox("Event", ["Door only", *c.events])
    if st.button("Authenticate and check in", type="primary"):
        result = c.scan(student, None if event == "Door only" else event)
        if result.tx_hash:
            st.session_state.history.append(("Check-in", result.tx_hash))
        (st.success if result.granted else st.error)(result.reason)
        st.write(f"Reward: {result.tokens_earned} TALK")
        if result.tx_hash: st.code(result.tx_hash)
with admin_tab:
    st.caption("All roles are simulated by this trusted local process; tabs are not access control.")
    target = st.selectbox("Credential to revoke", list(c.raw))
    if st.button("Revoke credential and pass"):
        try:
            c.revoke(target)
            st.success("Revoked in both demo stores")
        except Exception as e:
            st.error(f"Revocation incomplete; reconcile state ({type(e).__name__})")
    with st.form("event"):
        name = st.text_input("Unique event name")
        reward = st.number_input("Reward", 1, 1000, 100)
        capacity = st.number_input("Capacity", 1, 1000, 100)
        if st.form_submit_button("Create event"):
            if not name.strip(): st.error("Name required")
            else:
                try:
                    chain.create_event(name.strip(), int(reward), int(capacity))
                    c.events.append(name.strip())
                    st.success("Event created and demo gate authorized")
                except Exception as e: st.error(type(e).__name__)
    with st.form("perk"):
        name = st.text_input("Unique perk name")
        price = st.number_input("Price in TALK", 1, 1000000, 200)
        supply = st.number_input("Inventory", 1, 1000, 50)
        if st.form_submit_button("Create perk"):
            if not name.strip(): st.error("Name required")
            else:
                try:
                    chain.create_perk(name.strip(), int(price), int(supply))
                    c.perks.append(name.strip())
                    st.success("Perk created")
                except Exception as e: st.error(type(e).__name__)
with student_tab:
    sid = st.selectbox("Synthetic student", list(c.raw))
    wallet = c.registry.wallet_of(sid)
    a,b,d = st.columns(3)
    a.metric("TALK balance", chain.balance(wallet))
    b.metric("Reputation", chain.reputation(wallet))
    d.metric("Student Pass", "Valid" if chain.is_valid(wallet) else "Revoked")
    st.write("Wallet:", wallet)
    if "feedback" in st.session_state:
        kind, message = st.session_state.pop("feedback")
        (st.success if kind == "success" else st.error)(message)
    st.subheader("Available perks")
    for perk in c.perks:
        data = chain.perks.functions.perks(to_id(perk)).call()
        st.write(f"**{perk}** — {data[0]} TALK · {chain.perk_remaining(perk)} remaining")
        owned = chain.has_perk(perk, wallet)
        affordable = chain.balance(wallet) >= data[0]
        remaining = chain.perk_remaining(perk)
        if not owned and not affordable:
            st.caption(f"Earn {data[0] - chain.balance(wallet)} more TALK to redeem.")
        if st.button("Redeem " + perk, disabled=owned or not chain.is_valid(wallet) or not data[3] or not affordable or remaining == 0, key="redeem_"+perk):
            attempt(lambda: chain.unlock_perk(perk, wallet), "Perk redeemed")
            st.rerun()
        if owned: st.success("Claimed")
with ledger_tab:
    minted = chain.token.functions.lifetimeMinted().call()
    outstanding = chain.total_supply()
    a,b,d = st.columns(3)
    a.metric("Lifetime minted", minted)
    b.metric("Burned", minted-outstanding)
    d.metric("Outstanding", outstanding)
    st.json(chain.addresses())
    st.write("Local transaction evidence (not public explorer links)")
    for label, tx in reversed(st.session_state.history):
        st.write(label, tx)
    st.write("Veil simulated ledger integrity:", c.matcher.veil.ledger.verify_chain())
