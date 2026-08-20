# ═══════════════════════════════════════════════════════════════════
# EQUITEX STORE — Cloud-aware storage
# Supabase (cloud) with local JSON fallback for development
# ═══════════════════════════════════════════════════════════════════
import json
import os
import streamlit as st

# ── Local fallback path ──────────────────────────────────────────
_HERE      = os.path.dirname(os.path.abspath(__file__))
_DATA_FILE = os.path.join(_HERE, "equitex_data.json")

# ── Detect environment ───────────────────────────────────────────
def _supabase_client():
    """Return a Supabase client if credentials are configured, else None."""
    try:
        url = st.secrets.get("SUPABASE_URL", "") or os.environ.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            return None
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None

def _is_cloud():
    """True when Supabase credentials are present."""
    return _supabase_client() is not None

# ── User ID ──────────────────────────────────────────────────────
def _user_id():
    """
    A stable identifier for the current user's data.
    In production you'd replace this with real auth (Supabase Auth).
    For now we use a value from st.secrets or a default.
    """
    return st.secrets.get("USER_ID", "default_user")

# ═══════════════════════════════════════════════════════════════════
# PORTFOLIO STORAGE
# ═══════════════════════════════════════════════════════════════════
_PORTFOLIO_TABLE = "portfolios"

def get_portfolios():
    """Load portfolios from Supabase or local JSON."""
    sb = _supabase_client()
    if sb:
        try:
            resp = sb.table(_PORTFOLIO_TABLE)\
                     .select("data")\
                     .eq("user_id", _user_id())\
                     .limit(1)\
                     .execute()
            if resp.data:
                return json.loads(resp.data[0]["data"])
            return []
        except Exception as e:
            st.warning(f"Cloud load failed, using local: {e}")

    # Local fallback
    if not os.path.exists(_DATA_FILE):
        return []
    try:
        with open(_DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            return d.get("portfolios", [])
    except Exception:
        return []


def save_portfolios(portfolios):
    """Save portfolios to Supabase or local JSON."""
    sb = _supabase_client()
    if sb:
        try:
            payload = {
                "user_id": _user_id(),
                "data": json.dumps(portfolios, default=str),
            }
            # Upsert — insert or update if user_id already exists
            sb.table(_PORTFOLIO_TABLE).upsert(payload, on_conflict="user_id").execute()
            return
        except Exception as e:
            st.warning(f"Cloud save failed, saving locally: {e}")

    # Local fallback
    try:
        existing = {}
        if os.path.exists(_DATA_FILE):
            with open(_DATA_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing["portfolios"] = portfolios
        with open(_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, default=str)
    except Exception as e:
        st.warning(f"Local save failed: {e}")


# ═══════════════════════════════════════════════════════════════════
# FINANCE PROFILE STORAGE
# ═══════════════════════════════════════════════════════════════════
_PROFILE_TABLE = "profiles"

def get_finance_profile():
    """Load finance profile from Supabase or local JSON."""
    sb = _supabase_client()
    if sb:
        try:
            resp = sb.table(_PROFILE_TABLE)\
                     .select("data")\
                     .eq("user_id", _user_id())\
                     .limit(1)\
                     .execute()
            if resp.data:
                return json.loads(resp.data[0]["data"])
            return {}
        except Exception as e:
            st.warning(f"Profile cloud load failed: {e}")

    # Local fallback
    profile_path = os.path.join(_HERE, "equitex_profile.json")
    if not os.path.exists(profile_path):
        return {}
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_finance_profile(profile):
    """Save finance profile to Supabase or local JSON."""
    sb = _supabase_client()
    if sb:
        try:
            payload = {
                "user_id": _user_id(),
                "data": json.dumps(profile, default=str),
            }
            sb.table(_PROFILE_TABLE).upsert(payload, on_conflict="user_id").execute()
            return
        except Exception as e:
            st.warning(f"Profile cloud save failed: {e}")

    # Local fallback
    profile_path = os.path.join(_HERE, "equitex_profile.json")
    try:
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, default=str)
    except Exception as e:
        st.warning(f"Profile local save failed: {e}")


# ═══════════════════════════════════════════════════════════════════
# MF STORE
# ═══════════════════════════════════════════════════════════════════
_MF_TABLE = "mf_store"

def get_mf_store():
    """Load MF store from Supabase or local JSON."""
    sb = _supabase_client()
    if sb:
        try:
            resp = sb.table(_MF_TABLE)\
                     .select("data")\
                     .eq("user_id", _user_id())\
                     .limit(1)\
                     .execute()
            if resp.data:
                return json.loads(resp.data[0]["data"])
            return {}
        except Exception as e:
            st.warning(f"MF cloud load failed: {e}")

    # Local fallback
    mf_path = os.path.join(_HERE, "equitex_mf.json")
    if not os.path.exists(mf_path):
        return {}
    try:
        with open(mf_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_mf_store(store):
    """Save MF store to Supabase or local JSON."""
    sb = _supabase_client()
    if sb:
        try:
            payload = {
                "user_id": _user_id(),
                "data": json.dumps(store, default=str),
            }
            sb.table(_MF_TABLE).upsert(payload, on_conflict="user_id").execute()
            return
        except Exception as e:
            st.warning(f"MF cloud save failed: {e}")

    # Local fallback
    mf_path = os.path.join(_HERE, "equitex_mf.json")
    try:
        with open(mf_path, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, default=str)
    except Exception as e:
        st.warning(f"MF local save failed: {e}")
