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
import json
import re
import streamlit as st

_BACKUP_VERSION = 1


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
            pass
    return client


def _synth_email(profile_name):
    """Turn a profile name into a synthetic, never-contacted address —
    just to satisfy Supabase Auth's email-shaped requirement."""
    clean = re.sub(r'[^a-z0-9_]', '', profile_name.strip().lower().replace(" ", "_"))
    return f"{clean}@equitex.internal"


# ═══════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════
def is_logged_in():
    return bool(st.session_state.get("_sb_user_id"))


def current_profile_name():
    return st.session_state.get("_sb_profile_name", "")


def sign_up(profile_name, password):
    if not profile_name or not profile_name.strip():
        return False, "Enter a profile name."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    client = _get_client()
    email = _synth_email(profile_name)
    try:
        resp = client.auth.sign_up({"email": email, "password": password})
        if resp.session:
            st.session_state._sb_session = {
                "access_token": resp.session.access_token,
                "refresh_token": resp.session.refresh_token,
            }
            st.session_state._sb_user_id = resp.user.id
            st.session_state._sb_profile_name = profile_name.strip()
            return True, "Profile created!"
        return False, "Signup didn't return a session — check that 'Confirm email' is turned OFF in Supabase → Authentication → Providers → Email."
    except Exception as e:
        msg = str(e)
        if "already registered" in msg.lower() or "already exists" in msg.lower() or "already been registered" in msg.lower():
            return False, "That profile name is already taken — try logging in instead, or pick a different name."
        return False, f"Could not create profile: {msg[:200]}"


def sign_in(profile_name, password):
    if not profile_name or not password:
        return False, "Enter both profile name and password."
    client = _get_client()
    email = _synth_email(profile_name)
    try:
        resp = client.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state._sb_session = {
            "access_token": resp.session.access_token,
            "refresh_token": resp.session.refresh_token,
        }
        st.session_state._sb_user_id = resp.user.id
        st.session_state._sb_profile_name = profile_name.strip()
        return True, "Logged in!"
    except Exception:
        return False, "Incorrect profile name or password."


def sign_out():
    try:
        _get_client().auth.sign_out()
    except Exception:
        pass
    for k in ["_sb_session", "_sb_user_id", "_sb_profile_name", "_sb_client",
              "portfolios", "fa_profile", "fa_loaded", "mf_store", "_restored"]:
        st.session_state.pop(k, None)


def render_login_gate():
    """Call at the very top of the app. Returns True if the person is
    logged in and the rest of the app should render; otherwise shows
    the login/signup screen and returns False."""
    if is_logged_in():
        return True

    st.markdown("""<div style="text-align:center;padding:40px 0 20px;">
        <div style="font-size:28px;font-weight:700;">📘 EQUITEX PRO</div>
        <div style="font-size:13px;color:#8b948c;margin-top:4px;">Sign in with a profile name and password — no email needed</div>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "✨ Create Profile"])

        with tab1:
            name = st.text_input("Profile Name", key="login_name")
            pw = st.text_input("Password", type="password", key="login_pw")
            if st.button("Login", type="primary", width='stretch', key="login_btn"):
                ok, msg = sign_in(name, pw)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)

        with tab2:
            name2 = st.text_input("Choose a Profile Name", key="signup_name")
            pw2 = st.text_input("Choose a Password (min 6 characters)", type="password", key="signup_pw")
            if st.button("Create Profile", type="primary", width='stretch', key="signup_btn"):
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
        if resp.data:
            return json.loads(resp.data[0]["data"])
        return default
    except Exception as e:
        st.warning(f"Could not load data: {e}")
        return default


def _table_save(table, value):
    uid = st.session_state.get("_sb_user_id")
    if not uid:
        return
    try:
        client = _get_client()
        payload = {"user_id": uid, "data": json.dumps(value, default=str)}
        client.table(table).upsert(payload, on_conflict="user_id").execute()
    except Exception as e:
        st.warning(f"Could not save — please use Download Backup as a safeguard. ({e})")


def get_portfolios():
    return _table_get("portfolios", [])

def save_portfolios(portfolios):
    _table_save("portfolios", portfolios)


def get_finance_profile():
    return _table_get("profiles", {})

def save_finance_profile(profile):
    _table_save("profiles", profile)


def get_mf_store():
    return _table_get("mf_store", {})

def save_mf_store(store):
    _table_save("mf_store", store)


def delete_all_data():
    """Wipe this account's data (all 3 tables) — the account itself
    still exists, only the saved data is cleared."""
    uid = st.session_state.get("_sb_user_id")
    if not uid:
        return
    client = _get_client()
    for table in ("portfolios", "profiles", "mf_store"):
        try:
            client.table(table).delete().eq("user_id", uid).execute()
        except Exception:
            pass


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
