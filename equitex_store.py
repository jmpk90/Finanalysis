# ═══════════════════════════════════════════════════════════════════
# EQUITEX STORE — Cookie-keyed per-browser storage
#
# Why this replaced the localStorage approach: that relied on a
# third-party component (streamlit-local-storage) bridging JS and
# Python through an iframe, which proved unreliable in practice — data
# was getting lost on ordinary page refresh, not just slow to load.
#
# This version uses st.context.cookies — a NATIVE Streamlit feature
# (1.38+) that reads real HTTP cookies sent with the request. No JS
# bridge, no iframe, no race condition: cookies are either present in
# the request or they aren't, checked synchronously every time.
#
# Each browser gets a random ID (set once, via a real cookie, on first
# visit). Data is stored server-side in a small JSON file per ID — a
# plain, boring, synchronous file read/write, so refreshing the page
# can no longer lose data the way the old async component could.
#
# Residual trade-off (smaller than before, but real): Streamlit Cloud's
# free-tier filesystem is ephemeral, so a redeploy or a long sleep/wake
# cycle can wipe these files — ordinary refreshes and normal usage are
# NOT affected, only redeploys. The Backup & Restore download button
# on the Dashboard remains the safety net for that rarer case.
# ═══════════════════════════════════════════════════════════════════
import json
import os
import uuid
import streamlit as st
import streamlit.components.v1 as components

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_HERE, "equitex_user_data")
os.makedirs(_DATA_DIR, exist_ok=True)

_COOKIE_NAME = "equitex_device_id"
_BACKUP_VERSION = 1


def _get_device_id():
    """Read the browser's device-id cookie (native, reliable). If this
    browser has never visited before, mint a new ID, set it as a real
    cookie via a tiny one-time JS snippet, and reload so the very next
    request has it — after that, every read is a plain cookie check,
    no async waiting involved."""
    if "_device_id" in st.session_state:
        return st.session_state["_device_id"]

    try:
        existing = st.context.cookies.get(_COOKIE_NAME)
    except Exception:
        existing = None

    if existing:
        st.session_state["_device_id"] = existing
        return existing

    # First-ever visit from this browser — mint and persist an ID once.
    if st.session_state.get("_cookie_set_attempted"):
        # We already tried setting it and reloaded, but it's still not
        # showing up (browser is blocking cookies entirely). Fall back
        # to a session-only ID so the app still works, just without
        # persistence across refreshes for this browser.
        fallback_id = str(uuid.uuid4())
        st.session_state["_device_id"] = fallback_id
        st.warning("This browser appears to be blocking cookies, so your data won't persist across page refreshes here. Please use Download Backup regularly.")
        return fallback_id

    new_id = str(uuid.uuid4())
    st.session_state["_cookie_set_attempted"] = True
    components.html(f"""
        <script>
        document.cookie = "{_COOKIE_NAME}={new_id}; max-age=31536000; path=/; SameSite=Lax";
        window.location.reload();
        </script>
    """, height=0)
    st.stop()  # halt this run — the reload above will restart with the cookie present


def _paths(device_id, item):
    return os.path.join(_DATA_DIR, f"{device_id}__{item}.json")


def _read(item, default):
    device_id = _get_device_id()
    path = _paths(device_id, item)
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write(item, value):
    device_id = _get_device_id()
    path = _paths(device_id, item)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(value, f, default=str)
    except Exception as e:
        st.warning(f"Could not save — please use Download Backup as a safeguard. ({e})")


# ═══════════════════════════════════════════════════════════════════
# PORTFOLIO STORAGE
# ═══════════════════════════════════════════════════════════════════
def get_portfolios():
    return _read("portfolios", [])

def save_portfolios(portfolios):
    _write("portfolios", portfolios)


# ═══════════════════════════════════════════════════════════════════
# FINANCE PROFILE STORAGE
# ═══════════════════════════════════════════════════════════════════
def get_finance_profile():
    return _read("profile", {})

def save_finance_profile(profile):
    _write("profile", profile)


# ═══════════════════════════════════════════════════════════════════
# MF STORE
# ═══════════════════════════════════════════════════════════════════
def get_mf_store():
    return _read("mf_store", {})

def save_mf_store(store):
    _write("mf_store", store)


# ═══════════════════════════════════════════════════════════════════
# FULL BACKUP — export everything to one downloadable file, and restore
# from it. Safety net for the redeploy/sleep-wake ephemeral-disk case.
# ═══════════════════════════════════════════════════════════════════
def export_full_backup():
    payload = {
        "_equitex_backup_version": _BACKUP_VERSION,
        "portfolios": get_portfolios(),
        "profile":    get_finance_profile(),
        "mf_store":   get_mf_store(),
    }
    return json.dumps(payload, indent=2, default=str)


def restore_full_backup(json_text):
    try:
        payload = json.loads(json_text)
    except Exception as e:
        return False, f"That doesn't look like a valid backup file: {e}"

    if not isinstance(payload, dict) or "_equitex_backup_version" not in payload:
        return False, "This file doesn't look like an EQUITEX PRO backup."

    restored = []
    if "portfolios" in payload:
        save_portfolios(payload["portfolios"]); restored.append("portfolios")
    if "profile" in payload:
        save_finance_profile(payload["profile"]); restored.append("wealth/budget profile")
    if "mf_store" in payload:
        save_mf_store(payload["mf_store"]); restored.append("mutual funds")

    if not restored:
        return False, "Backup file was valid but contained no recognizable data."
    return True, f"Restored: {', '.join(restored)}."
