# ═══════════════════════════════════════════════════════════════════
# EQUITEX STORE — Browser-only storage
# Every visitor's data lives in THEIR OWN browser's localStorage.
# There is no shared backend, so one visitor can never see another's
# data — isolation is guaranteed by the browser itself, not by app logic.
#
# Trade-off (by design, discussed with the user): data is tied to one
# browser on one device. Clearing browser data, switching browsers, or
# using a private/incognito tab means the data is gone unless the user
# has downloaded a backup (see export_full_backup / restore_full_backup
# below, wired into the Dashboard page's Backup & Restore section).
# ═══════════════════════════════════════════════════════════════════
import json
import time
import streamlit as st
from streamlit_local_storage import LocalStorage

_KEYS = {
    "portfolios": "equitex_portfolios",
    "profile":    "equitex_profile",
    "mf_store":   "equitex_mf_store",
}

_BACKUP_VERSION = 1


def _ls():
    """One LocalStorage component instance per session, reused across calls."""
    if "_ls_instance" not in st.session_state:
        st.session_state._ls_instance = LocalStorage()
    return st.session_state._ls_instance


def _read(item, default):
    """Read one item from the browser, with a session-level cache so we
    only ever touch the JS bridge once per item per session (not once per
    call — several modules call get_portfolios()/get_mf_store() etc. on
    the same page load).

    Known quirk: on the very first load of a fresh browser tab, the
    component's JS side hasn't reported its real value back to Python
    yet, so an immediate read can look empty even when data exists.
    We retry a few times with short real delays (not just an instant
    rerun) to give the browser round-trip a genuine chance to complete
    before trusting "empty" as real — otherwise we can permanently lock
    in "no data" for the whole session even though the data is still
    sitting safely in the browser.
    """
    cache_key = f"_ls_cache_{item}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    try:
        raw = _ls().getItem(_KEYS[item], key=f"get_{item}")
    except Exception:
        raw = None

    if raw:
        try:
            val = json.loads(raw)
        except Exception:
            val = default
        st.session_state[cache_key] = val
        return val

    attempt_key = f"_ls_attempts_{item}"
    attempts = st.session_state.get(attempt_key, 0)
    if attempts < 4:
        st.session_state[attempt_key] = attempts + 1
        time.sleep(0.35)  # give the browser round-trip real time to land
        st.rerun()

    st.session_state[cache_key] = default
    return default


def _write(item, value):
    cache_key = f"_ls_cache_{item}"
    st.session_state[cache_key] = value
    try:
        _ls().setItem(_KEYS[item], json.dumps(value, default=str), key=f"set_{item}")
    except Exception as e:
        st.warning(f"Could not save to browser storage — your changes will be lost on refresh unless you download a backup. ({e})")


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
# from it. This is the safety net for browser storage being wiped.
# ═══════════════════════════════════════════════════════════════════
def export_full_backup():
    """Return a single JSON string with everything, for st.download_button."""
    payload = {
        "_equitex_backup_version": _BACKUP_VERSION,
        "portfolios": get_portfolios(),
        "profile":    get_finance_profile(),
        "mf_store":   get_mf_store(),
    }
    return json.dumps(payload, indent=2, default=str)


def restore_full_backup(json_text):
    """Parse an uploaded backup file and write all three stores back into
    this browser's local storage. Returns (ok: bool, message: str)."""
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
