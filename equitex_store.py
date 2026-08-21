# ═══════════════════════════════════════════════════════════════════
# EQUITEX STORE — Cookie/query-param-keyed per-browser storage
#
# History: first version used a third-party localStorage component
# (unreliable — lost data on refresh). Second version used a native
# cookie set via a JS-triggered page reload (caused a blank-page
# failure when the reload didn't complete cleanly). This version
# never halts or reloads the page — it determines a per-browser ID
# synchronously in one pass (cookie, then URL ?uid= param, then a
# freshly minted one written straight into the URL) and keeps
# rendering normally either way.
#
# Data is stored server-side in a small JSON file per device ID — a
# plain, boring, synchronous file read/write.
#
# Residual trade-off: Streamlit Cloud's free-tier filesystem is
# ephemeral, so a redeploy or long sleep/wake cycle can wipe these
# files — ordinary refreshes and normal usage are NOT affected, only
# redeploys. The Backup & Restore download button on the Dashboard
# remains the safety net for that rarer case.
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
    """Determine a stable per-browser ID, without ever halting or
    reloading the page (that reload-based approach caused a blank-page
    failure — too fragile). Priority:
      1. Existing cookie (native st.context.cookies — reliable, no JS).
      2. Existing ?uid= query param (also native, zero JS needed).
      3. Freshly minted ID — written into the URL's query param
         immediately (so this exact visit is already persistent via the
         URL) and also attempted as a cookie for future bare-URL visits,
         but WITHOUT blocking or reloading — the app keeps rendering
         normally in this same run either way.
    """
    if "_device_id" in st.session_state:
        return st.session_state["_device_id"]

    try:
        existing_cookie = st.context.cookies.get(_COOKIE_NAME)
    except Exception:
        existing_cookie = None

    if existing_cookie:
        st.session_state["_device_id"] = existing_cookie
        return existing_cookie

    try:
        existing_qp = st.query_params.get("uid")
    except Exception:
        existing_qp = None

    if existing_qp:
        st.session_state["_device_id"] = existing_qp
        # try to also set a cookie so future bare-URL visits still work
        _try_set_cookie(existing_qp)
        return existing_qp

    new_id = str(uuid.uuid4())
    st.session_state["_device_id"] = new_id
    try:
        st.query_params["uid"] = new_id
    except Exception:
        pass
    _try_set_cookie(new_id)
    return new_id


def _try_set_cookie(device_id):
    """Fire-and-forget cookie set — no reload, no st.stop(). If it works,
    great (future bare-URL visits pick it up). If it silently fails,
    the URL's ?uid= param (already set) still carries the ID, so nothing
    breaks either way."""
    if st.session_state.get(f"_cookie_tried_{device_id}"):
        return
    st.session_state[f"_cookie_tried_{device_id}"] = True
    try:
        components.html(f"""
            <script>
            document.cookie = "{_COOKIE_NAME}={device_id}; max-age=31536000; path=/; SameSite=Lax";
            </script>
        """, height=0)
    except Exception:
        pass


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
