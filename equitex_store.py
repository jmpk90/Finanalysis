# ═══════════════════════════════════════════════════════════════════
# EQUITEX STORE — Real accounts (Profile Name + Password)
#
# Replaces the earlier cookie/device-ID approach entirely. That system
# went through several iterations (browser localStorage, then cookies,
# then a URL-based fallback) and each had a real failure mode — data
# loss on refresh, a URL that could leak identity if shared, and a
# separate shared-file bug in the Wealth module. This version uses
# Supabase Auth for real password-based login, which doesn't depend on
# browser storage tricks at all.
#
# No real email required: signup only asks for a Profile Name and
# Password. Internally, the profile name is converted into a synthetic
# address (e.g. "rahul@equitex.internal") purely because Supabase's
# auth API expects an email-shaped string — nothing is ever sent there,
# and the person never sees or types an email anywhere.
#
# Isolation is enforced by the DATABASE itself via Row Level Security
# (see supabase_setup.sql) — each row is only ever visible to the
# logged-in user it belongs to, checked by Postgres on every query, not
# just by app-level logic.
# ═══════════════════════════════════════════════════════════════════
import hashlib
import json
import logging
import re
import time
import unicodedata
import streamlit as st

_log = logging.getLogger("equitex.store")

_BACKUP_VERSION = 1
_MIN_PASSWORD_LEN = 8
_MAX_FAILED_LOGINS = 5
_LOCKOUT_SECONDS = 60
_TABLES = ("portfolios", "profiles", "mf_store")

# Session keys that belong to the *person*, not the browser tab. Everything
# else in session_state is wiped on login/logout so one user can never see
# another user's data (or API key) in a shared browser session.
_KEEP_ON_RESET = {"theme", "main_nav"}


def _get_client():
    """One Supabase client per session, with the authenticated session
    (if any) re-applied on every rerun."""
    if "_sb_client" not in st.session_state:
        from supabase import create_client
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        st.session_state._sb_client = create_client(url, key)

    client = st.session_state._sb_client
    sess = st.session_state.get("_sb_session")
    if sess:
        try:
            client.auth.set_session(sess["access_token"], sess["refresh_token"])
        except Exception:
            _log.warning("Could not re-apply Supabase session", exc_info=True)
    return client


def _normalise_name(profile_name):
    """Case-fold, collapse whitespace, Unicode-normalise."""
    n = unicodedata.normalize("NFKC", profile_name or "")
    return re.sub(r"\s+", " ", n).strip().casefold()


def _synth_email(profile_name):
    """Turn a profile name into a synthetic, never-contacted address —
    just to satisfy Supabase Auth's email-shaped requirement.

    Uses a hash of the normalised name, so names that differ only in
    punctuation ("Rahul S" vs "rahul_s!") can no longer collide, and
    non-Latin names (e.g. Devanagari) work."""
    digest = hashlib.sha256(_normalise_name(profile_name).encode("utf-8")).hexdigest()[:24]
    return f"u_{digest}@equitex.internal"


def _legacy_synth_email(profile_name):
    """The pre-hash scheme, kept ONLY so existing accounts can still log in."""
    clean = re.sub(r'[^a-z0-9_]', '', profile_name.strip().lower().replace(" ", "_"))
    return f"{clean}@equitex.internal" if clean else None


def _reset_user_state(keep_client=False):
    """Wipe all per-user session data."""
    client = st.session_state.get("_sb_client") if keep_client else None
    for k in list(st.session_state.keys()):
        if k not in _KEEP_ON_RESET:
            st.session_state.pop(k, None)
    if client is not None:
        st.session_state._sb_client = client


# ═══════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════
def is_logged_in():
    return bool(st.session_state.get("_sb_user_id"))


def current_profile_name():
    return st.session_state.get("_sb_profile_name", "")


def _lockout_remaining():
    until = st.session_state.get("_login_locked_until", 0)
    return max(0, int(until - time.time()))


def _register_failed_login():
    n = st.session_state.get("_login_failures", 0) + 1
    st.session_state._login_failures = n
    if n >= _MAX_FAILED_LOGINS:
        st.session_state._login_locked_until = time.time() + _LOCKOUT_SECONDS
        st.session_state._login_failures = 0


def _start_session(resp, profile_name):
    # Clear anything left over from a previous user BEFORE storing the new one.
    _reset_user_state(keep_client=True)
    st.session_state._sb_session = {
        "access_token": resp.session.access_token,
        "refresh_token": resp.session.refresh_token,
    }
    st.session_state._sb_user_id = resp.user.id
    st.session_state._sb_profile_name = profile_name.strip()


def sign_up(profile_name, password):
    if not profile_name or not profile_name.strip():
        return False, "Enter a profile name."
    if len(profile_name.strip()) > 40:
        return False, "Profile name must be 40 characters or fewer."
    if len(password) < _MIN_PASSWORD_LEN:
        return False, f"Password must be at least {_MIN_PASSWORD_LEN} characters."
    if _normalise_name(password) == _normalise_name(profile_name):
        return False, "Password must be different from your profile name."
    client = _get_client()
    email = _synth_email(profile_name)
    try:
        resp = client.auth.sign_up({"email": email, "password": password})
        if resp.session:
            _start_session(resp, profile_name)
            return True, "Profile created!"
        _log.error("Signup returned no session — is 'Confirm email' still ON in Supabase?")
        return False, "Signup is not available right now. Please contact the app owner."
    except Exception as e:
        msg = str(e).lower()
        if "already registered" in msg or "already exists" in msg or "already been registered" in msg:
            return False, "That profile name is already taken — try logging in instead, or pick a different name."
        _log.error("Signup failed: %s", e)
        return False, "Could not create profile. Please try again in a moment."


def sign_in(profile_name, password):
    if not profile_name or not password:
        return False, "Enter both profile name and password."
    wait = _lockout_remaining()
    if wait:
        return False, f"Too many failed attempts. Please wait {wait}s and try again."
    client = _get_client()
    candidates = [_synth_email(profile_name)]
    legacy = _legacy_synth_email(profile_name)
    if legacy and legacy not in candidates:
        candidates.append(legacy)          # accounts created before the hash scheme
    for email in candidates:
        try:
            resp = client.auth.sign_in_with_password({"email": email, "password": password})
            if resp and resp.session:
                _start_session(resp, profile_name)
                st.session_state._login_failures = 0
                return True, "Logged in!"
        except Exception:
            continue
    _register_failed_login()
    return False, "Incorrect profile name or password."


def sign_out():
    try:
        _get_client().auth.sign_out()
    except Exception:
        _log.warning("Supabase sign_out failed", exc_info=True)
    # Wipe EVERYTHING per-user: profile, portfolios, MF store, Groq key, widget state.
    _reset_user_state(keep_client=False)


def render_login_gate():
    """Call at the very top of the app. Returns True if the person is
    logged in and the rest of the app should render; otherwise shows
    the login/signup screen and returns False."""
    if is_logged_in():
        return True

    st.markdown("""
    <style>
    .eq-login-brand{text-align:center;padding:48px 0 22px;}
    .eq-login-mark{display:inline-flex;align-items:center;justify-content:center;width:52px;height:52px;
        border-radius:14px;background:var(--bg-card);border:1px solid var(--border);font-size:26px;
        box-shadow:0 1px 2px rgba(25,38,35,.06);margin-bottom:14px;}
    .eq-login-title{font-family:var(--font-serif,'Fraunces',serif);font-size:30px;font-weight:600;
        color:var(--text-primary);letter-spacing:.5px;}
    .eq-login-sub{font-size:13px;color:var(--text-muted);margin-top:6px;}
    .eq-login-note{font-size:11px;color:var(--text-muted);text-align:center;margin-top:14px;line-height:1.6;}
    </style>
    <div class="eq-login-brand">
        <div class="eq-login-mark">📘</div>
        <div class="eq-login-title">EQUITEX PRO</div>
        <div class="eq-login-sub">Sign in with a profile name and password — no email needed</div>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "✨ Create Profile"])

        with tab1:
            with st.form("login_form", clear_on_submit=False):
                name = st.text_input("Profile Name", key="login_name")
                pw = st.text_input("Password", type="password", key="login_pw")
                submitted = st.form_submit_button("Login", type="primary", width='stretch')
            if submitted:
                ok, msg = sign_in(name, pw)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)

        with tab2:
            with st.form("signup_form", clear_on_submit=False):
                name2 = st.text_input("Choose a Profile Name", key="signup_name")
                pw2 = st.text_input(f"Choose a Password (min {_MIN_PASSWORD_LEN} characters)",
                                    type="password", key="signup_pw")
                submitted2 = st.form_submit_button("Create Profile", type="primary", width='stretch')
            st.markdown('<div class="eq-login-note">⚠️ There is <b>no password recovery</b> because no email is stored. '
                        'Keep your password safe and download a backup from the Dashboard now and then.</div>',
                        unsafe_allow_html=True)
            if submitted2:
                ok, msg = sign_up(name2, pw2)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)

    return False


# ═══════════════════════════════════════════════════════════════════
# STORAGE — each function only ever touches the logged-in user's own
# row, enforced both here (via user_id) and at the database level
# (Row Level Security policies in supabase_setup.sql).
# ═══════════════════════════════════════════════════════════════════
def _table_get(table, default):
    uid = st.session_state.get("_sb_user_id")
    if not uid:
        return default
    try:
        client = _get_client()
        resp = client.table(table).select("data").eq("user_id", uid).limit(1).execute()
        st.session_state[f"_load_failed_{table}"] = False
        if resp.data:
            return json.loads(resp.data[0]["data"])
        return default
    except Exception:
        # Remember the failure: _table_save will REFUSE to write to this table
        # until a load succeeds, so a flaky network can never turn into
        # "empty default overwrites the real data".
        st.session_state[f"_load_failed_{table}"] = True
        _log.error("Load failed for table %s", table, exc_info=True)
        st.warning("Could not load your saved data right now. Saving is paused to protect it — please refresh in a moment.")
        return default


def load_failed(table):
    return bool(st.session_state.get(f"_load_failed_{table}"))


def _table_save(table, value):
    uid = st.session_state.get("_sb_user_id")
    if not uid:
        return False
    if load_failed(table):
        st.warning("Your saved data could not be loaded, so this change was NOT saved (to avoid overwriting it). Refresh and try again.")
        return False
    try:
        client = _get_client()
        payload = {"user_id": uid, "data": json.dumps(value, default=str)}
        client.table(table).upsert(payload, on_conflict="user_id").execute()
        return True
    except Exception:
        _log.error("Save failed for table %s", table, exc_info=True)
        st.warning("Could not save — please use Download Backup as a safeguard.")
        return False


def get_portfolios():
    return _table_get("portfolios", [])

def save_portfolios(portfolios):
    return _table_save("portfolios", portfolios)


def get_finance_profile():
    return _table_get("profiles", {})

def save_finance_profile(profile):
    return _table_save("profiles", profile)


def get_mf_store():
    return _table_get("mf_store", {})

def save_mf_store(store):
    return _table_save("mf_store", store)


def delete_all_data():
    """Wipe this account's data (all 3 tables) — the account itself
    still exists, only the saved data is cleared."""
    uid = st.session_state.get("_sb_user_id")
    if not uid:
        return
    client = _get_client()
    for table in _TABLES:
        try:
            client.table(table).delete().eq("user_id", uid).execute()
        except Exception:
            _log.error("Delete failed for table %s", table, exc_info=True)
        st.session_state.pop(f"_load_failed_{table}", None)
    for k in ("portfolios", "fa_profile", "fa_loaded", "fa_hydrated", "mf_store"):
        st.session_state.pop(k, None)


# ═══════════════════════════════════════════════════════════════════
# FULL BACKUP — export everything to one downloadable file, and restore
# from it.
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
    if len(json_text) > 5_000_000:
        return False, "Backup file is too large."
    if not isinstance(payload.get("portfolios", []), list) \
            or not isinstance(payload.get("profile", {}), dict) \
            or not isinstance(payload.get("mf_store", {}), dict):
        return False, "Backup file has an unexpected structure."

    restored = []
    if "portfolios" in payload and save_portfolios(payload["portfolios"]):
        restored.append("portfolios")
    if "profile" in payload and save_finance_profile(payload["profile"]):
        restored.append("wealth/budget profile")
    if "mf_store" in payload and save_mf_store(payload["mf_store"]):
        restored.append("mutual funds")

    if not restored:
        return False, "Backup file was valid but contained no recognizable data."
    return True, f"Restored: {', '.join(restored)}."
