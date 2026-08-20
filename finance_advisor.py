# ═══════════════════════════════════════════════════════════════════
# EQUITEX PRO — FINANCE ADVISOR MODULE  v2.0
# Monthly budgets · Dual contributor · Asset ownership · Family dashboard
# ═══════════════════════════════════════════════════════════════════
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json, math, os as _os
from datetime import datetime

# ── Benchmark returns (% p.a.) ───────────────────────────────────
BENCHMARKS = {
    "stocks": 12.0, "mf": 11.0, "epf": 8.1, "nps": 9.5,
    "fd": 6.5, "gold": 8.0, "realty": 7.0, "savings": 3.5,
}
INFLATION = 6.0

# ── Expense categories with icons ────────────────────────────────
FIXED_EXPENSES = [
    ("🏠", "Rent"),
    ("🏦", "Home Loan EMI"),
    ("🚗", "Car Loan EMI"),
    ("🏫", "School / College Fees"),
    ("🛡", "Life Insurance Premium"),
    ("🏥", "Health Insurance Premium"),
    ("🚘", "Vehicle Insurance"),
    ("📺", "OTT / Subscriptions"),
]
VARIABLE_EXPENSES = [
    ("🛒", "Groceries"),
    ("⛽", "Fuel & Transport"),
    ("🍽", "Dining Out"),
    ("🎬", "Entertainment"),
    ("👕", "Clothing & Shopping"),
    ("💊", "Medical & Health"),
    ("✈️", "Travel & Vacation"),
    ("🎁", "Gifts & Personal Care"),
    ("👨‍👩‍👧", "Parents / Dependants"),
]
SAVINGS_TYPES = [
    ("🏛", "PPF"),
    ("🎯", "NPS"),
    ("📊", "Mutual Fund SIP"),
    ("📈", "Stock SIP"),
    ("🥇", "Gold SIP"),
    ("🏦", "FD / RD"),
    ("💵", "Emergency Fund"),
    ("🏠", "Property EMI (Investment)"),
]
ASSET_TYPES = ["Stocks", "Mutual Fund", "PPF", "NPS", "EPF", "FD / RD",
               "Gold", "Real Estate", "Savings Account", "Other"]
GOAL_TYPES = ["Retirement", "Home Purchase", "Child Education",
              "Child Marriage", "Emergency Fund", "Vehicle", "Travel", "Other"]

OWNER_COLORS = {
    "self":   {"bg": "#E6F1FB", "text": "#185FA5", "border": "#B5D4F4"},
    "spouse": {"bg": "#FBEAF0", "text": "#993556", "border": "#F4C0D1"},
    "joint":  {"bg": "#E1F5EE", "text": "#0F6E56",  "border": "#9FE1CB"},
}

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════
def fv(pv, rate_pct, years):
    if years <= 0: return pv
    return pv * ((1 + rate_pct / 100) ** years)

def fv_annuity(monthly, rate_pct_pa, years):
    if monthly <= 0 or years <= 0: return 0
    r = rate_pct_pa / 100 / 12
    n = years * 12
    if r == 0: return monthly * n
    return monthly * (((1 + r) ** n - 1) / r) * (1 + r)

def fmt(n):
    if n is None: return "₹0"
    n = float(n)
    if abs(n) >= 1e7:  return f"₹{n/1e7:.2f} Cr"
    if abs(n) >= 1e5:  return f"₹{n/1e5:.2f} L"
    return f"₹{n:,.0f}"

def _int(val, default=0, lo=None, hi=None):
    try: v = int(float(str(val))) if val is not None else default
    except: v = default
    if lo is not None: v = max(lo, v)
    if hi is not None: v = min(hi, v)
    return v

def _flt(val, default=0.0, lo=None, hi=None):
    try: v = float(str(val)) if val is not None else default
    except: v = default
    if lo is not None: v = max(lo, v)
    if hi is not None: v = min(hi, v)
    return v

def _str(val, default="", allowed=None):
    v = str(val).strip() if val is not None else default
    if allowed and v not in allowed: return default
    return v

# ─── Month key helpers ────────────────────────────────────────────
def month_key(year, month):
    return f"{year}-{month:02d}"

def month_label(key):
    try:
        y, m = key.split("-")
        return datetime(int(y), int(m), 1).strftime("%B %Y")
    except: return key

def current_month_key():
    n = datetime.now()
    return month_key(n.year, n.month)

def month_options(n=12):
    """Return last n months as (key, label) pairs, most recent first."""
    from datetime import date
    from calendar import month_name
    today = date.today()
    result = []
    y, m = today.year, today.month
    for _ in range(n):
        result.append((month_key(y, m), f"{month_name[m]} {y}"))
        m -= 1
        if m == 0: m = 12; y -= 1
    return result

# ─── Owner tag HTML ───────────────────────────────────────────────
def owner_tag_html(owner, self_name="Self", spouse_name="Spouse"):
    label = {"self": self_name, "spouse": spouse_name, "joint": "Joint"}.get(owner, owner)
    c = OWNER_COLORS.get(owner, OWNER_COLORS["joint"])
    return (f'<span style="font-size:10px;font-weight:600;padding:2px 9px;border-radius:20px;'
            f'background:{c["bg"]};color:{c["text"]};border:1px solid {c["border"]};">{label}</span>')

# ═══════════════════════════════════════════════════════════════════
# PERSISTENCE
# ═══════════════════════════════════════════════════════════════════
def _profile_path():
    here = _os.path.dirname(_os.path.abspath(__file__))
    return _os.path.join(here, "equitex_profile.json")

def fa_save():
    profile = st.session_state.get("fa_profile", {})
    if not profile: return
    path = _profile_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, default=str)
        st.session_state["fa_save_path"] = path
    except Exception as e:
        st.warning(f"⚠️ Could not save: {e}")

def fa_load():
    if st.session_state.get("fa_loaded"): return
    path = _profile_path()
    if not _os.path.exists(path): return
    try:
        with open(path, "r", encoding="utf-8") as f:
            profile = json.load(f)
        if isinstance(profile, dict) and profile.get("self_name"):
            st.session_state.fa_profile = profile
            st.session_state.fa_loaded  = True
            st.session_state["fa_save_path"] = path
    except Exception as e:
        st.warning(f"⚠️ Could not load profile: {e}")

def get_profile():
    return st.session_state.get("fa_profile", {})

def set_profile(key, value):
    if "fa_profile" not in st.session_state:
        st.session_state.fa_profile = {}
    st.session_state.fa_profile[key] = value

def pget(key, default=None):
    return get_profile().get(key, default)

# ─── Budget month helpers ─────────────────────────────────────────
def get_month_budget(mk):
    budgets = pget("monthly_budgets", {})
    return budgets.get(mk, {"income": [], "fixed": [], "variable": [], "savings": []})

def save_month_budget(mk, data):
    p = get_profile()
    if "monthly_budgets" not in p: p["monthly_budgets"] = {}
    p["monthly_budgets"][mk] = data
    st.session_state.fa_profile = p
    fa_save()

def get_assets():
    return pget("asset_registry", [])

def save_assets(assets):
    p = get_profile()
    p["asset_registry"] = assets
    st.session_state.fa_profile = p
    fa_save()

# ═══════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ═══════════════════════════════════════════════════════════════════
def sec_header(title, subtitle=""):
    st.markdown(f"""
    <div style="margin:24px 0 14px;padding-bottom:8px;border-bottom:2px solid var(--accent-gold);">
        <div style="font-family:'Fraunces',serif;font-size:20px;font-weight:600;
            color:var(--text-primary);">{title}</div>
        {f'<div style="font-family:var(--font-mono,DM Mono,monospace);font-size:10px;color:var(--text-muted);margin-top:2px;">{subtitle}</div>' if subtitle else ''}
    </div>""", unsafe_allow_html=True)

def metric_card(label, value, sub="", color="blue"):
    color_map = {
        "blue":   "var(--accent-blue)",   "green": "var(--accent-green)",
        "red":    "var(--accent-red)",    "gold":  "var(--accent-gold)",
        "cyan":   "var(--accent-cyan)",   "purple":"var(--accent-purple)",
    }
    c = color_map.get(color, "var(--accent-blue)")
    st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
        border-top:3px solid {c};border-radius:8px;padding:14px 16px;margin-bottom:8px;">
        <div style="font-family:var(--font-mono,DM Mono,monospace);font-size:9px;
            letter-spacing:1.5px;color:var(--text-muted);">{label}</div>
        <div style="font-size:20px;font-weight:700;color:{c};margin:4px 0;">{value}</div>
        <div style="font-size:10px;color:var(--text-secondary);">{sub}</div>
    </div>""", unsafe_allow_html=True)

def card_row(icon_bg, icon, name, sub, tag_html, amount, amount_color, key_del=None):
    """Render a single budget/asset row with delete button."""
    del_btn = ""
    col_html = f"""<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;
        border-bottom:1px solid var(--border);background:var(--bg-card);">
        <div style="width:28px;height:28px;border-radius:7px;background:{icon_bg};
            display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0;">{icon}</div>
        <div style="flex:1;">
            <div style="font-size:13px;color:var(--text-primary);">{name}</div>
            <div style="font-size:11px;color:var(--text-muted);">{sub}</div>
        </div>
        {tag_html}
        <div style="font-size:14px;font-weight:600;color:{amount_color};min-width:90px;text-align:right;">{amount}</div>
    </div>"""
    return col_html

def progress_bar(label, val, total, color="var(--accent-blue)"):
    pct = min(100, round(val / total * 100, 1)) if total > 0 else 0
    st.markdown(f"""<div style="margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;font-size:12px;
            color:var(--text-secondary);margin-bottom:4px;">
            <span>{label}</span><span style="color:var(--text-primary);font-weight:600;">{pct}%</span>
        </div>
        <div style="height:5px;background:var(--border);border-radius:3px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:{color};border-radius:3px;"></div>
        </div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SECTION: FAMILY PROFILE
# ═══════════════════════════════════════════════════════════════════
def render_profile_section():
    sec_header("👤 Family Profile", "YOUR FINANCIAL IDENTITY")

    p = get_profile()
    with st.expander("Self", expanded=True):
        c1,c2,c3,c4 = st.columns(4)
        with c1: name     = st.text_input("Your Name", value=_str(pget("self_name")), key="fa_self_name")
        with c2: age      = st.number_input("Age", 18, 80, value=_int(pget("self_age",30),30,18,80), key="fa_self_age")
        with c3: ret      = st.number_input("Retire at Age", 45, 80, value=_int(pget("self_retire",60),60,45,80), key="fa_self_retire")
        with c4:
            RISK_OPTS = ["Conservative","Moderate","Aggressive"]
            risk = st.selectbox("Risk Appetite", RISK_OPTS,
                index=RISK_OPTS.index(_str(pget("self_risk","Moderate"),"Moderate",RISK_OPTS)), key="fa_self_risk")
        c5,c6,c7 = st.columns(3)
        with c5:
            INC = ["Salaried","Business","Freelance","Other"]
            inc_type = st.selectbox("Income Type", INC,
                index=INC.index(_str(pget("self_inc_type","Salaried"),"Salaried",INC)), key="fa_self_inc_type")
        with c6: monthly_inc = st.number_input("Monthly Income (₹)", 0, 10000000, value=_int(pget("self_monthly_inc",0),0,0,10000000), step=1000, key="fa_self_inc")
        with c7: bonus       = st.number_input("Annual Bonus (₹)", 0, 10000000, value=_int(pget("self_bonus",0),0,0,10000000), step=10000, key="fa_self_bonus")

    include_spouse = st.checkbox("Include Spouse / Partner", value=bool(pget("include_spouse",False)), key="fa_include_spouse")
    if include_spouse:
        with st.expander("Spouse / Partner", expanded=True):
            s1,s2,s3 = st.columns(3)
            with s1: sp_name = st.text_input("Spouse Name", value=_str(pget("spouse_name")), key="fa_sp_name")
            with s2: sp_age  = st.number_input("Age", 18, 80, value=_int(pget("spouse_age",28),28,18,80), key="fa_sp_age")
            with s3: sp_ret  = st.number_input("Retire at Age", 45, 80, value=_int(pget("spouse_retire",58),58,45,80), key="fa_sp_ret")
            s4,s5,s6 = st.columns(3)
            with s4:
                SP_INC = ["Salaried","Business","Freelance","Other","Homemaker"]
                sp_inc_type = st.selectbox("Income Type", SP_INC,
                    index=SP_INC.index(_str(pget("spouse_inc_type","Salaried"),"Salaried",SP_INC)), key="fa_sp_inc_type")
            with s5: sp_inc   = st.number_input("Monthly Income (₹)", 0, 10000000, value=_int(pget("spouse_monthly_inc",0),0,0,10000000), step=1000, key="fa_sp_inc")
            with s6: sp_bonus = st.number_input("Annual Bonus (₹)", 0, 10000000, value=_int(pget("spouse_bonus",0),0,0,10000000), step=10000, key="fa_sp_bonus")

    sc1, sc2 = st.columns([1,3])
    with sc1:
        save_clicked = st.button("💾 Save Profile", key="fa_save_profile", type="primary", use_container_width=True)
    with sc2:
        import datetime as _dt
        save_path = st.session_state.get("fa_save_path","")
        if save_path and _os.path.exists(save_path):
            mtime = _os.path.getmtime(save_path)
            saved_at = _dt.datetime.fromtimestamp(mtime).strftime("%d %b %Y %H:%M")
            st.markdown(f'<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">💾 Last saved: <b style="color:var(--accent-green);">{saved_at}</b></div>', unsafe_allow_html=True)

    if save_clicked:
        p = get_profile()
        p.update({
            "self_name": st.session_state.fa_self_name,
            "self_age":  st.session_state.fa_self_age,
            "self_retire": st.session_state.fa_self_retire,
            "self_risk": st.session_state.fa_self_risk,
            "self_inc_type": st.session_state.fa_self_inc_type,
            "self_monthly_inc": st.session_state.fa_self_inc,
            "self_bonus": st.session_state.fa_self_bonus,
            "include_spouse": st.session_state.fa_include_spouse,
        })
        if include_spouse:
            p.update({
                "spouse_name": st.session_state.fa_sp_name,
                "spouse_age":  st.session_state.fa_sp_age,
                "spouse_retire": st.session_state.fa_sp_ret,
                "spouse_inc_type": st.session_state.fa_sp_inc_type,
                "spouse_monthly_inc": st.session_state.fa_sp_inc,
                "spouse_bonus": st.session_state.fa_sp_bonus,
            })
        st.session_state.fa_profile = p
        fa_save()
        st.success("✅ Profile saved!")
        st.rerun()


# ═══════════════════════════════════════════════════════════════════
# SECTION: MONTHLY BUDGET (New feature)
# ═══════════════════════════════════════════════════════════════════
def _budget_summary(budget):
    """Compute totals from a monthly budget dict."""
    income  = sum(e["amount"] for e in budget.get("income", []))
    fixed   = sum(e["amount"] for e in budget.get("fixed", []))
    variable= sum(e["amount"] for e in budget.get("variable", []))
    savings = sum(e["amount"] for e in budget.get("savings", []))
    expenses= fixed + variable
    surplus = income - expenses - savings
    return income, expenses, savings, surplus, fixed, variable

def _owner_split(entries, self_name, spouse_name):
    """Return totals split by owner."""
    totals = {"self": 0, "spouse": 0, "joint": 0}
    for e in entries:
        owner = e.get("owner", "self")
        totals[owner] = totals.get(owner, 0) + e.get("amount", 0)
    return totals

def render_add_entry_form(section_key, mk, label_options=None, label_prefix=""):
    """Inline add-entry form. Returns True if an entry was added."""
    p = get_profile()
    self_name   = p.get("self_name", "Self")
    spouse_name = p.get("spouse_name", "Spouse") if p.get("include_spouse") else None
    has_spouse  = bool(p.get("include_spouse"))

    form_key = f"add_form_{section_key}_{mk}"
    if not st.session_state.get(f"show_{form_key}"):
        if st.button(f"＋ Add {label_prefix}", key=f"btn_{form_key}", use_container_width=False):
            st.session_state[f"show_{form_key}"] = True
            st.rerun()
        return False

    with st.container():
        st.markdown('<div style="background:var(--bg-secondary);border:1px dashed var(--border-bright);border-radius:8px;padding:14px;margin-top:6px;">', unsafe_allow_html=True)
        fc1, fc2 = st.columns([3,2])
        with fc1:
            if label_options:
                preset = st.selectbox("Preset or type custom →", ["— Custom —"] + [f"{i} {n}" for i,n in label_options], key=f"preset_{form_key}")
                if preset == "— Custom —":
                    entry_label = st.text_input("Label", key=f"lbl_{form_key}", placeholder="e.g. Club membership")
                else:
                    entry_label = preset.split(" ",1)[1] if " " in preset else preset
                    st.caption(f"Selected: **{entry_label}**")
            else:
                entry_label = st.text_input("Label", key=f"lbl_{form_key}", placeholder="Describe this entry")
        with fc2:
            entry_amt = st.number_input("Amount (₹)", min_value=0, max_value=10000000, value=0, step=500, key=f"amt_{form_key}")

        OWNER_OPTS = {self_name: "self"}
        if has_spouse: OWNER_OPTS[spouse_name] = "spouse"
        OWNER_OPTS["Joint / Shared"] = "joint"
        owner_display = st.radio("Paid by / Belongs to", list(OWNER_OPTS.keys()),
                                  horizontal=True, key=f"owner_{form_key}")
        owner_val = OWNER_OPTS[owner_display]

        sa, sb, _ = st.columns([1,1,4])
        saved = False
        with sa:
            if st.button("✅ Save", key=f"save_{form_key}", type="primary", use_container_width=True):
                if entry_label and entry_amt > 0:
                    budget = get_month_budget(mk)
                    budget.setdefault(section_key, [])
                    budget[section_key].append({"label": entry_label, "amount": int(entry_amt), "owner": owner_val})
                    save_month_budget(mk, budget)
                    st.session_state[f"show_{form_key}"] = False
                    saved = True
                    st.rerun()
        with sb:
            if st.button("✕ Cancel", key=f"cancel_{form_key}", use_container_width=True):
                st.session_state[f"show_{form_key}"] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    return saved


def render_entry_list(section_key, mk, entries, icon_map, amount_color, self_name, spouse_name):
    """Render list of budget entries with delete buttons."""
    if not entries:
        st.markdown(f'<div style="font-size:12px;color:var(--text-muted);padding:10px 0;">No entries yet — click ＋ Add to get started.</div>', unsafe_allow_html=True)
        return
    for i, e in enumerate(entries):
        label  = e.get("label","")
        amount = e.get("amount", 0)
        owner  = e.get("owner","self")
        # Find icon
        icon, icon_bg = "📌", "#E6F1FB"
        for bg_colors in [("#EAF3DE","🛒"),("#FAECE7","🏠"),("#FAEEDA","⛽"),("#FBEAF0","🍽"),
                           ("#E1F5EE","💊"),("#EEEDFE","🏛"),("#E6F1FB","📊"),("#FAEEDA","🪙")]:
            pass
        # Simple color cycling
        bg_cycle = ["#E6F1FB","#FAECE7","#EAF3DE","#FAEEDA","#FBEAF0","#EEEDFE","#E1F5EE","#FAEEDA"]
        icon_bg = bg_cycle[i % len(bg_cycle)]
        tag = owner_tag_html(owner, self_name, spouse_name)
        c_row, c_del = st.columns([10,1])
        with c_row:
            amt_str = f"₹{amount:,}"
            st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;padding:9px 14px;
                background:var(--bg-card);border:1px solid var(--border);border-radius:6px;margin-bottom:4px;">
                <div style="width:26px;height:26px;border-radius:6px;background:{icon_bg};
                    display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0;">💰</div>
                <div style="flex:1;font-size:13px;color:var(--text-primary);">{label}</div>
                {tag}
                <div style="font-size:14px;font-weight:600;color:{amount_color};min-width:80px;text-align:right;">{amt_str}</div>
            </div>""", unsafe_allow_html=True)
        with c_del:
            if st.button("🗑", key=f"del_{section_key}_{mk}_{i}", help="Delete"):
                budget = get_month_budget(mk)
                budget[section_key].pop(i)
                save_month_budget(mk, budget)
                st.rerun()


def render_budget_section():
    sec_header("📊 Monthly Budget", "MONTH-BY-MONTH BUDGET TRACKER")
    p = get_profile()
    self_name   = p.get("self_name") or "Self"
    spouse_name = p.get("spouse_name") or "Spouse"
    has_spouse  = bool(p.get("include_spouse"))

    if not p.get("self_name"):
        st.info("👤 Fill in your Profile & Income tab first.")
        return

    # ── Month + Year picker (free selection) ──────────────────
    from calendar import month_name as _month_name
    now = datetime.now()

    saved_mk = st.session_state.get("fa_budget_month", current_month_key())
    try:
        saved_y, saved_m = int(saved_mk.split("-")[0]), int(saved_mk.split("-")[1])
    except:
        saved_y, saved_m = now.year, now.month

    MONTH_NAMES = [_month_name[i] for i in range(1, 13)]

    hc1, hc2, hc3 = st.columns([2, 1, 3])
    with hc1:
        sel_month_name = st.selectbox(
            "Month", MONTH_NAMES,
            index=saved_m - 1,
            key="fa_budget_month_name"
        )
        sel_month = MONTH_NAMES.index(sel_month_name) + 1
    with hc2:
        sel_year = st.number_input(
            "Year", min_value=2000, max_value=2100,
            value=saved_y, step=1,
            key="fa_budget_year"
        )
    mk = month_key(int(sel_year), sel_month)
    st.session_state["fa_budget_month"] = mk

    # Copy from previous month button
    with hc3:
        # Compute previous month key
        prev_m = sel_month - 1 if sel_month > 1 else 12
        prev_y = int(sel_year) if sel_month > 1 else int(sel_year) - 1
        prev_mk  = month_key(prev_y, prev_m)
        prev_lbl = f"{MONTH_NAMES[prev_m-1]} {prev_y}"
        if True:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"📋 Copy from {prev_lbl}", key=f"copy_{mk}"):
                prev_budget = get_month_budget(prev_mk)
                curr_budget = get_month_budget(mk)
                # Only copy if current month is empty
                is_empty = all(len(curr_budget.get(k,[])) == 0 for k in ["income","fixed","variable","savings"])
                if is_empty:
                    save_month_budget(mk, dict(prev_budget))
                    st.success(f"✅ Copied from {prev_lbl}")
                    st.rerun()
                else:
                    st.warning("Current month already has entries. Delete them first to copy.")

    budget = get_month_budget(mk)
    income_e   = budget.get("income",   [])
    fixed_e    = budget.get("fixed",    [])
    variable_e = budget.get("variable", [])
    savings_e  = budget.get("savings",  [])

    total_income, total_exp, total_savings, surplus, total_fixed, total_variable = _budget_summary(budget)

    # ── Summary cards ─────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    sc1,sc2,sc3,sc4 = st.columns(4)
    with sc1:
        st.markdown(f"""<div style="background:var(--bg-secondary);border-radius:8px;padding:13px 15px;">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">TOTAL INCOME</div>
            <div style="font-size:22px;font-weight:700;color:var(--accent-green);">{fmt(total_income)}</div>
        </div>""", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""<div style="background:var(--bg-secondary);border-radius:8px;padding:13px 15px;">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">TOTAL EXPENSES</div>
            <div style="font-size:22px;font-weight:700;color:var(--accent-red);">{fmt(total_exp)}</div>
            <div style="font-size:10px;color:var(--text-muted);">Fixed {fmt(total_fixed)} · Var {fmt(total_variable)}</div>
        </div>""", unsafe_allow_html=True)
    with sc3:
        st.markdown(f"""<div style="background:var(--bg-secondary);border-radius:8px;padding:13px 15px;">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">SAVINGS / INVEST</div>
            <div style="font-size:22px;font-weight:700;color:var(--accent-blue);">{fmt(total_savings)}</div>
        </div>""", unsafe_allow_html=True)
    with sc4:
        surp_color = "var(--accent-green)" if surplus >= 0 else "var(--accent-red)"
        st.markdown(f"""<div style="background:var(--bg-secondary);border-radius:8px;padding:13px 15px;">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">SURPLUS</div>
            <div style="font-size:22px;font-weight:700;color:{surp_color};">{fmt(surplus)}</div>
            <div style="font-size:10px;color:var(--text-muted);">{'Investable' if surplus>=0 else '⚠️ Deficit'}</div>
        </div>""", unsafe_allow_html=True)

    # Progress bars
    st.markdown("<br>", unsafe_allow_html=True)
    if total_income > 0:
        progress_bar("Expense ratio", total_exp, total_income,
                     "var(--accent-red)" if total_exp/total_income > 0.7 else "var(--accent-blue)")
        progress_bar("Savings rate", total_savings, total_income, "var(--accent-green)")

    # ── Per-person summary (if spouse) ───────────────────────
    if has_spouse:
        all_entries = income_e + fixed_e + variable_e + savings_e
        self_total   = sum(e["amount"] for e in all_entries if e.get("owner","self") == "self")
        spouse_total = sum(e["amount"] for e in all_entries if e.get("owner") == "spouse")
        joint_total  = sum(e["amount"] for e in all_entries if e.get("owner") == "joint")
        oc = OWNER_COLORS
        st.markdown(f"""<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:16px;">
            <div style="background:{oc['self']['bg']};border:1px solid {oc['self']['border']};
                border-radius:8px;padding:12px 14px;">
                <div style="font-size:11px;color:{oc['self']['text']};font-weight:600;margin-bottom:4px;">{self_name}</div>
                <div style="font-size:18px;font-weight:700;color:{oc['self']['text']};">{fmt(self_total)}</div>
                <div style="font-size:10px;color:{oc['self']['text']};opacity:0.7;">Personal entries</div>
            </div>
            <div style="background:{oc['spouse']['bg']};border:1px solid {oc['spouse']['border']};
                border-radius:8px;padding:12px 14px;">
                <div style="font-size:11px;color:{oc['spouse']['text']};font-weight:600;margin-bottom:4px;">{spouse_name}</div>
                <div style="font-size:18px;font-weight:700;color:{oc['spouse']['text']};">{fmt(spouse_total)}</div>
                <div style="font-size:10px;color:{oc['spouse']['text']};opacity:0.7;">Personal entries</div>
            </div>
            <div style="background:{oc['joint']['bg']};border:1px solid {oc['joint']['border']};
                border-radius:8px;padding:12px 14px;">
                <div style="font-size:11px;color:{oc['joint']['text']};font-weight:600;margin-bottom:4px;">Joint / Shared</div>
                <div style="font-size:18px;font-weight:700;color:{oc['joint']['text']};">{fmt(joint_total)}</div>
                <div style="font-size:10px;color:{oc['joint']['text']};opacity:0.7;">Shared entries</div>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── 4 Sections: Income, Fixed, Variable, Savings ─────────
    t1, t2, t3, t4 = st.tabs(["💰 Income", "🏠 Fixed Expenses", "🛒 Variable Expenses", "💼 Savings & Investments"])

    with t1:
        st.markdown('<div style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">Salary, freelance, rental, side income — tag who earns what.</div>', unsafe_allow_html=True)
        render_entry_list("income", mk, income_e, {}, "var(--accent-green)", self_name, spouse_name)
        render_add_entry_form("income", mk, label_prefix="Income")

        # Total per person
        if income_e and has_spouse:
            st.markdown("---")
            self_inc_total = sum(e["amount"] for e in income_e if e.get("owner","self")=="self")
            sp_inc_total   = sum(e["amount"] for e in income_e if e.get("owner")=="spouse")
            ic1, ic2 = st.columns(2)
            with ic1:
                st.markdown(f'<div style="font-size:12px;color:var(--text-secondary);">{self_name} earns: <b style="color:var(--accent-green);">{fmt(self_inc_total)}/mo</b></div>', unsafe_allow_html=True)
            with ic2:
                st.markdown(f'<div style="font-size:12px;color:var(--text-secondary);">{spouse_name} earns: <b style="color:var(--accent-green);">{fmt(sp_inc_total)}/mo</b></div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">Rent, EMIs, insurance, school fees — recurring fixed monthly outflows.</div>', unsafe_allow_html=True)
        render_entry_list("fixed", mk, fixed_e, {}, "var(--accent-red)", self_name, spouse_name)
        render_add_entry_form("fixed", mk, label_options=FIXED_EXPENSES, label_prefix="Fixed Expense")

    with t3:
        st.markdown('<div style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">Groceries, fuel, dining, shopping — variable monthly spends.</div>', unsafe_allow_html=True)
        render_entry_list("variable", mk, variable_e, {}, "var(--accent-red)", self_name, spouse_name)
        render_add_entry_form("variable", mk, label_options=VARIABLE_EXPENSES, label_prefix="Variable Expense")

    with t4:
        st.markdown('<div style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">SIPs, PPF, NPS, FD — savings tagged to each person flow into their assets.</div>', unsafe_allow_html=True)
        render_entry_list("savings", mk, savings_e, {}, "var(--accent-blue)", self_name, spouse_name)
        render_add_entry_form("savings", mk, label_options=SAVINGS_TYPES, label_prefix="Savings / Investment")

        # Note about asset linking
        if savings_e:
            st.markdown(f"""<div style="background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.2);
                border-radius:6px;padding:10px 14px;margin-top:10px;font-size:12px;color:var(--text-secondary);">
                ℹ️ These savings are reflected in the <b>Assets & Net Worth</b> tab — tagged to each person's profile.
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SECTION: ASSETS & NET WORTH (with owner tagging)
# ═══════════════════════════════════════════════════════════════════
def render_assets_section():
    sec_header("🏦 Assets & Net Worth", "ALL ASSETS — TAGGED BY OWNER")
    p = get_profile()
    self_name   = p.get("self_name","Self")
    spouse_name = p.get("spouse_name","Spouse") if p.get("include_spouse") else None
    has_spouse  = bool(p.get("include_spouse"))

    assets = get_assets()

    # ── Add asset form ─────────────────────────────────────────
    with st.expander("➕ Add Asset", expanded=not assets):
        ac1,ac2,ac3 = st.columns(3)
        with ac1: a_name = st.text_input("Asset name", placeholder="e.g. SBI FD, PPF Account", key="fa_a_name")
        with ac2: a_type = st.selectbox("Type", ASSET_TYPES, key="fa_a_type")
        with ac3: a_val  = st.number_input("Current Value (₹)", 0, 1000000000, 0, 10000, key="fa_a_val")
        ac4,ac5,ac6 = st.columns(3)
        with ac4: a_inv  = st.number_input("Amount Invested (₹)", 0, 1000000000, 0, 10000, key="fa_a_inv")
        with ac5: a_mo   = st.number_input("Monthly Addition (₹)", 0, 1000000, 0, 500, key="fa_a_mo",
                                            help="Monthly SIP/contribution — used for projections")
        with ac6:
            OWNER_OPTS = {self_name: "self"}
            if has_spouse: OWNER_OPTS[spouse_name] = "spouse"
            OWNER_OPTS["Joint"] = "joint"
            a_owner_lbl = st.selectbox("Belongs to", list(OWNER_OPTS.keys()), key="fa_a_owner")
            a_owner_val = OWNER_OPTS[a_owner_lbl]
        if st.button("Add Asset", key="fa_a_add", type="primary"):
            if a_name and a_val > 0:
                assets.append({"name": a_name, "type": a_type, "value": a_val,
                                "invested": a_inv, "monthly": a_mo, "owner": a_owner_val})
                save_assets(assets)
                st.success(f"✅ Added {a_name}")
                st.rerun()

    # ── Also import assets from existing module (Stocks/MF/EPF/NPS) ──
    legacy_assets = _build_legacy_assets(p)

    all_display = legacy_assets + assets
    if not all_display:
        st.info("No assets yet. Use the form above to add your first asset.")
        return

    # ── Totals ─────────────────────────────────────────────────
    total_val = sum(a.get("value",0) for a in all_display)
    self_val  = sum(a.get("value",0) for a in all_display if a.get("owner","self") == "self")
    sp_val    = sum(a.get("value",0) for a in all_display if a.get("owner") == "spouse")
    joint_val = sum(a.get("value",0) for a in all_display if a.get("owner") == "joint")

    vc1,vc2,vc3,vc4 = st.columns(4)
    with vc1:
        st.markdown(f"""<div style="background:var(--bg-secondary);border-radius:8px;padding:13px 15px;margin-bottom:12px;">
            <div style="font-size:10px;color:var(--text-muted);">TOTAL ASSETS</div>
            <div style="font-size:20px;font-weight:700;color:var(--accent-gold);">{fmt(total_val)}</div>
        </div>""", unsafe_allow_html=True)
    with vc2:
        c = OWNER_COLORS["self"]
        st.markdown(f"""<div style="background:{c['bg']};border:1px solid {c['border']};border-radius:8px;padding:13px 15px;margin-bottom:12px;">
            <div style="font-size:10px;color:{c['text']};font-weight:600;">{self_name}</div>
            <div style="font-size:20px;font-weight:700;color:{c['text']};">{fmt(self_val)}</div>
        </div>""", unsafe_allow_html=True)
    if has_spouse:
        with vc3:
            c = OWNER_COLORS["spouse"]
            st.markdown(f"""<div style="background:{c['bg']};border:1px solid {c['border']};border-radius:8px;padding:13px 15px;margin-bottom:12px;">
                <div style="font-size:10px;color:{c['text']};font-weight:600;">{spouse_name}</div>
                <div style="font-size:20px;font-weight:700;color:{c['text']};">{fmt(sp_val)}</div>
            </div>""", unsafe_allow_html=True)
    with vc4:
        c = OWNER_COLORS["joint"]
        st.markdown(f"""<div style="background:{c['bg']};border:1px solid {c['border']};border-radius:8px;padding:13px 15px;margin-bottom:12px;">
            <div style="font-size:10px;color:{c['text']};font-weight:600;">Joint</div>
            <div style="font-size:20px;font-weight:700;color:{c['text']};">{fmt(joint_val)}</div>
        </div>""", unsafe_allow_html=True)

    # ── Asset list ─────────────────────────────────────────────
    st.markdown('<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:8px;overflow:hidden;">', unsafe_allow_html=True)
    # Header
    st.markdown("""<div style="display:flex;padding:8px 14px;background:var(--bg-secondary);
        border-bottom:1px solid var(--border);font-size:10px;font-weight:600;
        color:var(--text-muted);letter-spacing:1px;text-transform:uppercase;gap:10px;">
        <div style="flex:2;">Asset</div><div style="flex:1;">Type</div>
        <div style="width:80px;">Owner</div>
        <div style="width:110px;text-align:right;">Invested</div>
        <div style="width:110px;text-align:right;">Current Value</div>
        <div style="width:80px;text-align:right;">P&L</div>
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    for i, a in enumerate(all_display):
        val  = _flt(a.get("value",0))
        inv  = _flt(a.get("invested",0))
        gain = val - inv if inv > 0 else 0
        gc   = "var(--accent-green)" if gain >= 0 else "var(--accent-red)"
        owner = a.get("owner","self")
        oc    = OWNER_COLORS.get(owner, OWNER_COLORS["self"])
        owner_label = {"self": self_name, "spouse": spouse_name or "Spouse", "joint":"Joint"}.get(owner, owner)
        is_legacy = a.get("_legacy", False)
        c_row, c_del = st.columns([10,1])
        with c_row:
            gain_str = (f'<span style="color:{gc};font-size:11px;">{fmt(gain)}</span>' if inv > 0 else '<span style="color:var(--text-muted);font-size:11px;">—</span>')
            st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;padding:9px 14px;
                background:var(--bg-card);border:1px solid var(--border);border-radius:6px;margin-bottom:4px;">
                <div style="flex:2;font-size:13px;color:var(--text-primary);">
                    {a.get('name','Asset')}
                    {'<span style="font-size:9px;color:var(--text-muted);margin-left:6px;">AUTO</span>' if is_legacy else ''}
                </div>
                <div style="flex:1;font-size:11px;color:var(--text-muted);">{a.get('type','—')}</div>
                <div style="width:80px;">
                    <span style="font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px;
                        background:{oc['bg']};color:{oc['text']};border:1px solid {oc['border']};">{owner_label}</span>
                </div>
                <div style="width:110px;text-align:right;font-size:12px;color:var(--text-secondary);">{fmt(inv) if inv>0 else "—"}</div>
                <div style="width:110px;text-align:right;font-size:13px;font-weight:600;color:var(--accent-gold);">{fmt(val)}</div>
                <div style="width:80px;text-align:right;">{gain_str}</div>
            </div>""", unsafe_allow_html=True)
        with c_del:
            if not is_legacy:
                if st.button("🗑", key=f"del_asset_{i}", help="Delete"):
                    assets.pop(i - len(legacy_assets))
                    save_assets(assets)
                    st.rerun()
            else:
                st.markdown('<div style="height:36px;"></div>', unsafe_allow_html=True)

    # ── Asset allocation chart ─────────────────────────────────
    if all_display:
        st.markdown("<br>", unsafe_allow_html=True)
        by_type = {}
        for a in all_display:
            t = a.get("type","Other")
            by_type[t] = by_type.get(t,0) + _flt(a.get("value",0))
        labels = [k for k,v in by_type.items() if v>0]
        values = [v for v in by_type.values() if v>0]
        if labels:
            fig = go.Figure(go.Pie(
                labels=labels, values=values, hole=0.52,
                textinfo="label+percent",
                textfont=dict(size=10, color="#e2e8f0"),
                marker=dict(colors=["#4a9eff","#3ecf8e","#c9a84c","#a78bfa","#2dd4bf",
                                     "#f59e0b","#e05252","#64748b","#34d399","#f87171"]),
                hovertemplate="%{label}<br>%{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Mono", size=9, color="var(--text-secondary)"),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9), orientation="h"),
                height=300, margin=dict(l=10,r=10,t=10,b=10),
                annotations=[dict(text=fmt(total_val), x=0.5, y=0.5,
                    font=dict(size=11, color="#e2e8f0", family="DM Mono"), showarrow=False)]
            )
            st.plotly_chart(fig, use_container_width=True)


def _build_legacy_assets(p):
    """Build auto-detected assets from existing profile data."""
    assets = []
    # Stocks
    try:
        from equitex_store import get_portfolios
        sv = sum(_flt(s.get("ltp",0))*_flt(s.get("qty",0)) for pf in get_portfolios() for s in pf.get("stocks",[]))
        si = sum(_flt(s.get("avg_price",0))*_flt(s.get("qty",0)) for pf in get_portfolios() for s in pf.get("stocks",[]))
        if sv > 0:
            assets.append({"name":"Equity Portfolio (Stocks)", "type":"Stocks",
                           "value":sv, "invested":si, "monthly":0,
                           "owner": p.get("stock_owner","self"), "_legacy":True})
    except: pass
    # MF
    try:
        from mf_module import all_funds, get_store as _mgs
        mff = all_funds(_mgs())
        if mff:
            mv = sum(_flt(m.get("current_value",0)) or _flt(m.get("invested",0)) for m in mff)
            mi = sum(_flt(m.get("invested",0)) for m in mff)
            ms = sum(_flt(m.get("sip",0)) for m in mff)
            if mv > 0:
                assets.append({"name":"Mutual Fund Portfolio", "type":"Mutual Fund",
                               "value":mv, "invested":mi, "monthly":ms,
                               "owner": p.get("mf_owner","self"), "_legacy":True})
    except: pass
    # EPF
    epf = _flt(p.get("epf_balance",0))
    if epf > 0:
        assets.append({"name":"EPF / PF", "type":"EPF",
                       "value":epf, "invested":epf, "monthly":_flt(p.get("epf_monthly",0)),
                       "owner": p.get("epf_owner","self"), "_legacy":True})
    # NPS
    nps = _flt(p.get("nps_balance",0))
    if nps > 0:
        assets.append({"name":"NPS", "type":"NPS",
                       "value":nps, "invested":nps, "monthly":_flt(p.get("nps_monthly",0)),
                       "owner": p.get("nps_owner","self"), "_legacy":True})
    # FD
    for fd in p.get("fd_list",[]):
        if _flt(fd.get("amount",0)) > 0:
            assets.append({"name":f"FD — {fd.get('bank','Bank')}", "type":"FD / RD",
                           "value":_flt(fd.get("amount",0)), "invested":_flt(fd.get("amount",0)),
                           "monthly":0, "owner": fd.get("owner","self"), "_legacy":True})
    # Gold
    for g in p.get("gold_list",[]):
        gv = _flt(g.get("grams",0)) * max(1,_flt(g.get("rate",7500)))
        if gv > 0:
            assets.append({"name":f"Gold — {g.get('type','Physical')}", "type":"Gold",
                           "value":gv, "invested":_flt(g.get("invested",0)),
                           "monthly":0, "owner": g.get("owner","self"), "_legacy":True})
    # Real estate
    for r in p.get("re_list",[]):
        rv = _flt(r.get("current",r.get("current_value",0)))
        if rv > 0:
            assets.append({"name":r.get("name","Property"), "type":"Real Estate",
                           "value":rv, "invested":_flt(r.get("purchased",0)),
                           "monthly":0, "owner": r.get("owner","joint"), "_legacy":True})
    return assets


# ═══════════════════════════════════════════════════════════════════
# SECTION: FAMILY DASHBOARD
# ═══════════════════════════════════════════════════════════════════
def render_family_dashboard():
    sec_header("👨‍👩‍👧 Family Dashboard", "COMBINED WEALTH · INDIVIDUAL SNAPSHOT")
    p = get_profile()
    self_name   = p.get("self_name","Self")
    spouse_name = p.get("spouse_name","Spouse") if p.get("include_spouse") else None
    has_spouse  = bool(p.get("include_spouse"))

    if not p.get("self_name"):
        st.info("👤 Fill in your Profile & Income tab first.")
        return

    mk = st.session_state.get("fa_budget_month", current_month_key())
    budget = get_month_budget(mk)
    legacy = _build_legacy_assets(p)
    user_assets = get_assets()
    all_assets = legacy + user_assets

    # Compute asset totals per owner
    self_assets   = [a for a in all_assets if a.get("owner","self") == "self"]
    spouse_assets = [a for a in all_assets if a.get("owner") == "spouse"]
    joint_assets  = [a for a in all_assets if a.get("owner") == "joint"]
    self_nw   = sum(_flt(a.get("value",0)) for a in self_assets)
    spouse_nw = sum(_flt(a.get("value",0)) for a in spouse_assets)
    joint_val = sum(_flt(a.get("value",0)) for a in joint_assets)
    total_nw  = self_nw + spouse_nw + joint_val

    # Budget totals for current month
    _, total_exp, total_sav, _, _, _ = _budget_summary(budget)
    self_inc   = sum(e["amount"] for e in budget.get("income",[]) if e.get("owner","self") == "self")
    spouse_inc = sum(e["amount"] for e in budget.get("income",[]) if e.get("owner") == "spouse")
    self_exp   = sum(e["amount"] for e in (budget.get("fixed",[])+budget.get("variable",[])) if e.get("owner","self") == "self")
    spouse_exp = sum(e["amount"] for e in (budget.get("fixed",[])+budget.get("variable",[])) if e.get("owner") == "spouse")
    self_sav   = sum(e["amount"] for e in budget.get("savings",[]) if e.get("owner","self") == "self")
    spouse_sav = sum(e["amount"] for e in budget.get("savings",[]) if e.get("owner") == "spouse")
    total_inc  = self_inc + spouse_inc

    # ── Family net worth banner ───────────────────────────────
    st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
        border-left:4px solid var(--accent-gold);border-radius:10px;
        padding:20px 24px;margin-bottom:20px;display:flex;
        justify-content:space-between;align-items:center;">
        <div>
            <div style="font-size:20px;font-weight:700;color:var(--text-primary);">
                {self_name}{"  +  " + spouse_name if has_spouse else ""} — Family Wealth</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:3px;">
                {month_label(mk)} · {len(all_assets)} assets tracked</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:10px;color:var(--text-muted);letter-spacing:2px;">FAMILY NET WORTH</div>
            <div style="font-size:32px;font-weight:800;color:var(--accent-gold);">{fmt(total_nw)}</div>
            <div style="font-size:11px;color:var(--text-muted);">
                +{fmt(total_sav)}/mo savings this month</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── 3-tab dashboard ───────────────────────────────────────
    dt1, dt2, dt3 = st.tabs(["📊 Overview", "👤 Individual", "🏦 Asset Breakdown"])

    with dt1:
        # Monthly cashflow cards
        cc1,cc2,cc3,cc4 = st.columns(4)
        with cc1: metric_card("COMBINED INCOME",   fmt(total_inc),  f"{month_label(mk)}", "green")
        with cc2: metric_card("COMBINED EXPENSES", fmt(total_exp),  "Fixed + Variable", "red")
        with cc3: metric_card("COMBINED SAVINGS",  fmt(total_sav),  "Invested this month", "blue")
        with cc4:
            sr = round(total_sav/total_inc*100,1) if total_inc>0 else 0
            metric_card("SAVINGS RATE", f"{sr}%", "Target: 20%+", "green" if sr>=20 else "gold")

        # Net worth composition
        st.markdown("<br>", unsafe_allow_html=True)
        if has_spouse:
            self_pct   = round(self_nw / total_nw * 100, 1) if total_nw > 0 else 0
            spouse_pct = round(spouse_nw / total_nw * 100, 1) if total_nw > 0 else 0
            joint_pct  = round(joint_val / total_nw * 100, 1) if total_nw > 0 else 0
            oc = OWNER_COLORS
            # Stacked bar
            st.markdown(f'<div style="font-size:11px;color:var(--text-muted);margin-bottom:6px;font-weight:600;">WEALTH OWNERSHIP DISTRIBUTION</div>', unsafe_allow_html=True)
            bar_html = f"""<div style="height:24px;border-radius:4px;overflow:hidden;display:flex;margin-bottom:8px;">
                <div style="width:{self_pct}%;background:{oc['self']['text']};display:flex;align-items:center;
                    justify-content:center;font-size:10px;color:#fff;font-weight:600;
                    {"min-width:40px;" if self_pct>8 else ""}">{self_pct if self_pct>5 else ""}{"%" if self_pct>5 else ""}</div>
                <div style="width:{spouse_pct}%;background:{oc['spouse']['text']};display:flex;align-items:center;
                    justify-content:center;font-size:10px;color:#fff;font-weight:600;
                    {"min-width:40px;" if spouse_pct>8 else ""}">{spouse_pct if spouse_pct>5 else ""}{"%" if spouse_pct>5 else ""}</div>
                <div style="width:{joint_pct}%;background:{oc['joint']['text']};display:flex;align-items:center;
                    justify-content:center;font-size:10px;color:#fff;font-weight:600;
                    {"min-width:40px;" if joint_pct>8 else ""}">{joint_pct if joint_pct>5 else ""}{"%" if joint_pct>5 else ""}</div>
            </div>
            <div style="display:flex;gap:16px;font-size:11px;margin-bottom:16px;">
                <span style="color:{oc['self']['text']};"><span style="width:10px;height:10px;border-radius:2px;background:{oc['self']['text']};display:inline-block;margin-right:4px;"></span>{self_name}: {fmt(self_nw)}</span>
                {"<span style='color:" + oc['spouse']['text'] + ";'><span style='width:10px;height:10px;border-radius:2px;background:" + oc['spouse']['text'] + ";display:inline-block;margin-right:4px;'></span>" + spouse_name + ": " + fmt(spouse_nw) + "</span>" if has_spouse else ""}
                <span style="color:{oc['joint']['text']};"><span style="width:10px;height:10px;border-radius:2px;background:{oc['joint']['text']};display:inline-block;margin-right:4px;"></span>Joint: {fmt(joint_val)}</span>
            </div>"""
            st.markdown(bar_html, unsafe_allow_html=True)

        # Loans
        loans = p.get("loan_list",[])
        total_debt = sum(_flt(l.get("outstanding",0)) for l in loans)
        total_emi  = sum(_flt(l.get("emi",0)) for l in loans)
        if total_debt > 0:
            mc1,mc2 = st.columns(2)
            with mc1: metric_card("TOTAL DEBT",   fmt(total_debt), f"{len(loans)} loan(s)", "red")
            with mc2: metric_card("MONTHLY EMI",  fmt(total_emi),  "Total committed", "red")

    with dt2:
        # Individual toggle
        persons = [self_name]
        if has_spouse: persons.append(spouse_name)
        sel_person = st.radio("View profile for", persons, horizontal=True, key="fam_person_sel")
        is_self = (sel_person == self_name)
        owner_key = "self" if is_self else "spouse"
        oc = OWNER_COLORS[owner_key]

        p_income  = self_inc   if is_self else spouse_inc
        p_expense = self_exp   if is_self else spouse_exp
        p_savings = self_sav   if is_self else spouse_sav
        p_surplus = p_income - p_expense - p_savings
        p_nw      = self_nw   if is_self else spouse_nw
        p_assets  = self_assets if is_self else spouse_assets
        # Add half of joint
        p_nw_with_joint = p_nw + joint_val / 2

        # Profile card
        initials = sel_person[:1].upper()
        st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
            border-radius:10px;padding:18px;margin-bottom:16px;
            display:flex;align-items:center;gap:16px;">
            <div style="width:50px;height:50px;border-radius:50%;background:{oc['bg']};
                border:2px solid {oc['border']};display:flex;align-items:center;
                justify-content:center;font-size:20px;font-weight:700;color:{oc['text']};
                flex-shrink:0;">{initials}</div>
            <div style="flex:1;">
                <div style="font-size:18px;font-weight:700;color:var(--text-primary);">{sel_person}</div>
                <div style="font-size:11px;color:var(--text-muted);">{month_label(mk)} snapshot</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:10px;color:var(--text-muted);">Personal net worth</div>
                <div style="font-size:22px;font-weight:700;color:{oc['text']};">{fmt(p_nw_with_joint)}</div>
                <div style="font-size:10px;color:var(--text-muted);">incl. ½ joint assets</div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Stats
        ic1,ic2,ic3,ic4 = st.columns(4)
        with ic1: metric_card("INCOME",   fmt(p_income),  "This month",   "green")
        with ic2: metric_card("EXPENSES", fmt(p_expense), "Pays for",     "red")
        with ic3: metric_card("SAVINGS",  fmt(p_savings), "Investing",    "blue")
        with ic4:
            metric_card("SURPLUS", fmt(p_surplus),
                        "Remaining" if p_surplus>=0 else "⚠️ Overspent",
                        "green" if p_surplus>=0 else "red")

        # Their assets
        if p_assets:
            st.markdown('<div style="font-size:11px;font-weight:600;color:var(--text-muted);margin:14px 0 8px;letter-spacing:1px;">PERSONAL ASSETS</div>', unsafe_allow_html=True)
            for a in p_assets:
                val = _flt(a.get("value",0))
                inv = _flt(a.get("invested",0))
                gain = val - inv if inv > 0 else 0
                gc = "var(--accent-green)" if gain>=0 else "var(--accent-red)"
                st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;
                    background:var(--bg-secondary);border-radius:6px;margin-bottom:4px;">
                    <div style="flex:2;font-size:13px;color:var(--text-primary);">{a.get('name','—')}</div>
                    <div style="flex:1;font-size:11px;color:var(--text-muted);">{a.get('type','—')}</div>
                    <div style="font-size:13px;font-weight:600;color:var(--accent-gold);">{fmt(val)}</div>
                    {"<div style='font-size:11px;color:" + gc + ";margin-left:8px;'>" + fmt(gain) + "</div>" if inv>0 else ""}
                </div>""", unsafe_allow_html=True)
        # Joint assets
        if joint_assets:
            st.markdown('<div style="font-size:11px;font-weight:600;color:var(--text-muted);margin:14px 0 8px;letter-spacing:1px;">JOINT ASSETS (50% SHARE)</div>', unsafe_allow_html=True)
            for a in joint_assets:
                val = _flt(a.get("value",0)) / 2
                st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;
                    background:var(--bg-secondary);border-radius:6px;margin-bottom:4px;">
                    <div style="flex:2;font-size:13px;color:var(--text-primary);">{a.get('name','—')}</div>
                    <div style="flex:1;font-size:11px;color:var(--text-muted);">{a.get('type','—')} · Joint</div>
                    <div style="font-size:13px;font-weight:600;color:var(--accent-cyan);">{fmt(val)}</div>
                </div>""", unsafe_allow_html=True)

    with dt3:
        # By asset type stacked bar
        if all_assets:
            type_self   = {}
            type_spouse = {}
            type_joint  = {}
            for a in all_assets:
                t = a.get("type","Other")
                v = _flt(a.get("value",0))
                if a.get("owner","self") == "self":   type_self[t]   = type_self.get(t,0)   + v
                elif a.get("owner") == "spouse":      type_spouse[t] = type_spouse.get(t,0) + v
                else:                                 type_joint[t]  = type_joint.get(t,0)  + v

            all_types = sorted(set(list(type_self)+list(type_spouse)+list(type_joint)))
            oc = OWNER_COLORS
            fig = go.Figure()
            fig.add_trace(go.Bar(name=self_name,
                x=all_types, y=[type_self.get(t,0)/1e5 for t in all_types],
                marker_color=oc["self"]["text"]))
            if has_spouse:
                fig.add_trace(go.Bar(name=spouse_name,
                    x=all_types, y=[type_spouse.get(t,0)/1e5 for t in all_types],
                    marker_color=oc["spouse"]["text"]))
            fig.add_trace(go.Bar(name="Joint",
                x=all_types, y=[type_joint.get(t,0)/1e5 for t in all_types],
                marker_color=oc["joint"]["text"]))
            fig.update_layout(
                barmode="stack", height=340,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Mono", size=9, color="#a8b8cc"),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9), orientation="h", y=-0.2),
                xaxis=dict(gridcolor="#1e2d46"),
                yaxis=dict(gridcolor="#1e2d46", title="₹ Lakhs"),
                margin=dict(l=30,r=10,t=10,b=60),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add assets to see the breakdown chart.")


# ═══════════════════════════════════════════════════════════════════
# SECTION: LIABILITIES (preserved from original)
# ═══════════════════════════════════════════════════════════════════
def render_liabilities_section():
    sec_header("💳 Liabilities", "LOANS, EMIs & DEBT MANAGEMENT")
    p = get_profile()
    loan_list = pget("loan_list", [])

    with st.expander("➕ Add Loan / EMI", expanded=not loan_list):
        lc1,lc2,lc3 = st.columns(3)
        with lc1: l_type = st.selectbox("Loan Type", ["Home Loan","Car Loan","Personal Loan","Education Loan","Credit Card","Other"], key="fa_l_type")
        with lc2: l_bank = st.text_input("Lender / Bank", key="fa_l_bank")
        with lc3: l_os   = st.number_input("Outstanding Amount (₹)", 0, 500000000, 0, 10000, key="fa_l_os")
        lc4,lc5,lc6 = st.columns(3)
        with lc4: l_emi   = st.number_input("Monthly EMI (₹)", 0, 500000, 0, 1000, key="fa_l_emi")
        with lc5: l_rate  = st.number_input("Interest Rate %", 0.0, 30.0, 8.0, 0.1, key="fa_l_rate")
        with lc6: l_months= st.number_input("Remaining Months", 0, 600, 60, 1, key="fa_l_months")
        # Owner tag
        has_sp = bool(p.get("include_spouse"))
        sn     = p.get("self_name","Self")
        spn    = p.get("spouse_name","Spouse")
        OWNER_OPTS = {sn:"self"}
        if has_sp: OWNER_OPTS[spn] = "spouse"
        OWNER_OPTS["Joint"] = "joint"
        l_owner_lbl = st.radio("Loan taken by", list(OWNER_OPTS.keys()), horizontal=True, key="fa_l_owner")
        l_owner_val = OWNER_OPTS[l_owner_lbl]

        if st.button("Add Loan", key="fa_l_add", type="primary"):
            loan_list.append({"type":l_type,"bank":l_bank,"outstanding":l_os,
                               "emi":l_emi,"rate":l_rate,"months":l_months,"owner":l_owner_val,
                               "name": f"{l_type} — {l_bank}" if l_bank else l_type})
            set_profile("loan_list", loan_list); fa_save(); st.rerun()

    if loan_list:
        total_os  = sum(_flt(l.get("outstanding",0)) for l in loan_list)
        total_emi = sum(_flt(l.get("emi",0)) for l in loan_list)
        mc1, mc2 = st.columns(2)
        with mc1: metric_card("TOTAL OUTSTANDING", fmt(total_os), f"{len(loan_list)} loan(s)", "red")
        with mc2: metric_card("TOTAL MONTHLY EMI", fmt(total_emi), "Committed outflow", "red")
        st.markdown("<br>", unsafe_allow_html=True)
        for i, l in enumerate(loan_list):
            os = _flt(l.get("outstanding",0))
            emi= _flt(l.get("emi",0))
            rate=_flt(l.get("rate",0))
            mos= _int(l.get("months",0))
            owner= l.get("owner","self")
            tag = owner_tag_html(owner, p.get("self_name","Self"), p.get("spouse_name","Spouse"))
            c1, c2 = st.columns([6,1])
            with c1:
                st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;
                    background:var(--bg-card);border:1px solid var(--border);border-radius:6px;margin-bottom:4px;">
                    <div style="flex:2;font-size:13px;color:var(--text-primary);">{l.get('name',l.get('type','Loan'))}</div>
                    <div style="flex:1;font-size:12px;color:var(--accent-red);font-weight:600;">{fmt(os)}</div>
                    <div style="font-size:11px;color:var(--text-secondary);">{fmt(emi)}/mo · {rate}% · {mos}mo left</div>
                    {tag}
                </div>""", unsafe_allow_html=True)
            with c2:
                if st.button("🗑", key=f"del_loan_{i}"):
                    loan_list.pop(i); set_profile("loan_list", loan_list); fa_save(); st.rerun()
        if st.button("💾 Save Changes", key="fa_loans_save"):
            set_profile("loan_list", loan_list); fa_save(); st.success("✅ Saved")
    else:
        st.info("No loans added. Use the form above to add your first loan.")


# ═══════════════════════════════════════════════════════════════════
# SECTION: GOALS (preserved + enhanced)
# ═══════════════════════════════════════════════════════════════════
def render_goals_section():
    sec_header("🎯 Financial Goals", "PLAN · TRACK · ACHIEVE")
    p = get_profile()
    goal_list = pget("goal_list", [])

    with st.expander("➕ Add Goal", expanded=not goal_list):
        gc1,gc2,gc3 = st.columns(3)
        with gc1: g_type = st.selectbox("Goal Type", GOAL_TYPES, key="fa_g_type")
        with gc2: g_name = st.text_input("Goal Name", placeholder="e.g. Retire at 55", key="fa_g_name")
        with gc3: g_target= st.number_input("Target Amount (₹)", 0, 1000000000, 0, 50000, key="fa_g_target")
        gc4,gc5 = st.columns(2)
        with gc4: g_saved = st.number_input("Already Saved (₹)", 0, 1000000000, 0, 10000, key="fa_g_saved")
        with gc5: g_years = st.number_input("Years to Goal", 1, 40, 10, 1, key="fa_g_years")
        if st.button("Add Goal", key="fa_g_add", type="primary"):
            name = g_name or g_type
            goal_list.append({"type":g_type,"name":name,"target":g_target,"saved":g_saved,"years":g_years})
            set_profile("goal_list", goal_list); fa_save(); st.rerun()

    if goal_list:
        gcols = st.columns(min(len(goal_list), 3))
        for i, g in enumerate(goal_list):
            target = _flt(g.get("target",0))
            saved  = _flt(g.get("saved",0))
            pct_done = min(round(saved/target*100,1) if target>0 else 0, 100)
            needed = max(0, target - saved)
            years  = _int(g.get("years",10))
            monthly_needed = needed/years/12 if years > 0 else needed
            g_color = "var(--accent-green)" if pct_done>=100 else ("var(--accent-gold)" if pct_done>=50 else "var(--accent-red)")
            with gcols[i % 3]:
                st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:8px;padding:14px 16px;margin-bottom:8px;">
                    <div style="font-size:12px;font-weight:600;color:var(--text-primary);">{g.get('name','Goal')}</div>
                    <div style="font-size:10px;color:var(--text-muted);margin:2px 0 8px;">
                        {g.get('type','—')} · Target: {fmt(target)} · {years}y</div>
                    <div style="height:6px;background:var(--border);border-radius:3px;margin-bottom:6px;">
                        <div style="height:6px;width:{pct_done}%;background:{g_color};border-radius:3px;"></div>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:11px;">
                        <span style="color:{g_color};">{pct_done}% funded</span>
                        <span style="color:var(--text-muted);">{fmt(monthly_needed)}/mo needed</span>
                    </div>
                </div>""", unsafe_allow_html=True)
                if st.button("🗑 Remove", key=f"del_goal_{i}", use_container_width=True):
                    goal_list.pop(i); set_profile("goal_list", goal_list); fa_save(); st.rerun()
    else:
        st.info("No goals set yet. Add your first financial goal above.")


# ═══════════════════════════════════════════════════════════════════
# SECTION: PROJECTIONS (preserved from original)
# ═══════════════════════════════════════════════════════════════════
def compute_net_worth(p, rates, years):
    """Compute projected net worth at a given horizon."""
    # Stocks
    try:
        from equitex_store import get_portfolios
        sv = sum(_flt(s.get("ltp",0))*_flt(s.get("qty",0)) or _flt(s.get("avg_price",0))*_flt(s.get("qty",0))
                 for pf in get_portfolios() for s in pf.get("stocks",[]))
        ssip = 0
    except:
        sv = _flt(p.get("stock_value",0)); ssip = 0
    stocks = fv(sv, rates["stocks"], years)

    # MF
    try:
        from mf_module import all_funds, get_store as _mgs
        mff    = all_funds(_mgs())
        mf_val = sum(_flt(m.get("current_value",0)) or _flt(m.get("invested",0)) for m in mff)
        mf_sip = sum(_flt(m.get("sip",0)) for m in mff)
    except:
        mf_val = sum(_flt(m.get("value",_flt(m.get("current_value",0)))) for m in p.get("mf_list",[]))
        mf_sip = sum(_flt(m.get("sip",0)) for m in p.get("mf_list",[]))
    mf_val_proj = fv(mf_val, rates["mf"], years) + fv_annuity(mf_sip, rates["mf"], years)

    epf_self = fv(p.get("epf_balance",0), rates["epf"], years) + \
               fv_annuity(p.get("epf_monthly",0)+p.get("epf_employer",0), rates["epf"], years)
    epf_sp   = fv(p.get("spouse_epf",0), rates["epf"], years) if p.get("include_spouse") else 0
    nps_self = fv(p.get("nps_balance",0), rates["nps"], years) + \
               fv_annuity(p.get("nps_monthly",0), rates["nps"], years)
    nps_sp   = fv(p.get("spouse_nps",0), rates["nps"], years) if p.get("include_spouse") else 0
    fd_val   = sum(fv(f["amount"], rates["fd"], years) for f in p.get("fd_list",[]))

    if p.get("gold_list"):
        gold_val = sum(fv(_flt(x.get("grams",0))*max(1,_flt(x.get("rate",7500))),
                       rates["gold"], years) for x in p["gold_list"] if x)
    else:
        gold_val = fv(p.get("gold_value",0), rates["gold"], years)

    re_val  = sum(fv(r.get("current",r.get("current_value",0)), rates["realty"], years) for r in p.get("re_list",[]))
    ins_mat = sum(i.get("maturity",0) for i in p.get("ins_list",[]))
    ins_pay = sum(i.get("monthly_payout",0)*12*years for i in p.get("ins_list",[]) if i.get("monthly_payout",0)>0)

    # Also include user-added assets
    for a in p.get("asset_registry",[]):
        atype = a.get("type","").lower()
        rate_key = "stocks" if "stock" in atype else ("mf" if "mutual" in atype else
                   "epf" if "epf" in atype else "nps" if "nps" in atype else
                   "fd" if "fd" in atype or "savings" in atype else
                   "gold" if "gold" in atype else "realty" if "real" in atype else "savings")
        aval = fv(_flt(a.get("value",0)), rates.get(rate_key, rates["savings"]), years) + \
               fv_annuity(_flt(a.get("monthly",0)), rates.get(rate_key, rates["savings"]), years)
        # Distribute into breakdown by category
        if "stock" in atype:   stocks    += aval
        elif "mutual" in atype: mf_val_proj += aval
        elif "gold" in atype:  gold_val  += aval
        elif "real" in atype:  re_val    += aval
        else:                  fd_val    += aval

    breakdown = {
        "Stocks": stocks, "Mutual Funds": mf_val_proj,
        "EPF / PF": epf_self+epf_sp, "NPS": nps_self+nps_sp,
        "FD / Savings": fd_val, "Gold": gold_val,
        "Real Estate": re_val, "Insurance": ins_mat+ins_pay,
    }
    gross = sum(breakdown.values())
    debt  = sum(max(0, l["outstanding"] - l["emi"]*min(years*12, l.get("months",0)))
                for l in p.get("loan_list",[]))
    return gross-debt, gross, debt, breakdown


def render_projections_section():
    sec_header("📈 Projections", "5 / 10 / 15 / 20 YEAR NET WORTH OUTLOOK")
    p = get_profile()

    with st.expander("⚙ Growth Rate Assumptions", expanded=False):
        rate_cols = st.columns(4)
        rate_keys = list(BENCHMARKS.keys())
        rate_labels = {"stocks":"Stocks","mf":"MF","epf":"EPF","nps":"NPS",
                       "fd":"FD","gold":"Gold","realty":"Realty","savings":"Savings"}
        custom_rates = pget("custom_rates", {})
        new_rates = {}
        for i, k in enumerate(rate_keys):
            with rate_cols[i % 4]:
                new_rates[k] = st.slider(f"{rate_labels[k]} %", 1.0, 25.0,
                    value=_flt(custom_rates.get(k, BENCHMARKS[k]), BENCHMARKS[k], 1.0, 25.0),
                    step=0.5, key=f"fa_rate_{k}")
        inflation_rate = st.slider("Inflation %", 3.0, 12.0,
            _flt(pget("inflation_rate", INFLATION), INFLATION, 3.0, 12.0), 0.5, key="fa_inflation")
        if st.button("Save Assumptions", key="fa_rates_save"):
            set_profile("custom_rates", new_rates)
            set_profile("inflation_rate", inflation_rate)
            fa_save(); st.success("Saved!")

    rates = pget("custom_rates", BENCHMARKS)
    for k,v in BENCHMARKS.items():
        if k not in rates: rates[k] = v

    horizon = st.radio("Projection Horizon", [5,10,15,20], index=1,
                        horizontal=True, key="fa_horizon",
                        format_func=lambda x: f"{x} Years")

    years_list = [1,2,3,4,5,7,10,15,20]
    nw_data    = {}
    breakdowns = {}
    for y in years_list:
        net, gross, debt, bd = compute_net_worth(p, rates, y)
        nw_data[y] = {"net":net,"gross":gross,"debt":debt}
        breakdowns[y] = bd

    cur_net, cur_gross, cur_debt, cur_bd = compute_net_worth(p, rates, 0)
    proj_net  = nw_data.get(horizon,{}).get("net",0)
    proj_debt = nw_data.get(horizon,{}).get("debt",0)

    sc1,sc2,sc3,sc4 = st.columns(4)
    with sc1: metric_card("CURRENT NET WORTH", fmt(cur_gross-cur_debt), "gross − debt", "blue")
    with sc2: metric_card(f"NET WORTH IN {horizon}Y", fmt(proj_net), "at current rate", "green")
    with sc3: metric_card("REMAINING DEBT", fmt(proj_debt), f"in {horizon} years", "red")
    with sc4:
        growth = ((proj_net/max(1,cur_gross-cur_debt))-1)*100 if (cur_gross-cur_debt)>0 else 0
        metric_card(f"{horizon}Y GROWTH", f"{growth:.0f}%", "total growth", "gold")

    st.markdown("<br>", unsafe_allow_html=True)
    COLORS = {"Stocks":"#4a9eff","Mutual Funds":"#3ecf8e","EPF / PF":"#c9a84c",
               "NPS":"#a78bfa","FD / Savings":"#2dd4bf","Gold":"#f59e0b",
               "Real Estate":"#e05252","Insurance":"#64748b"}

    col_pie, col_bar = st.columns(2)
    with col_pie:
        pie_labels = [k for k,v in cur_bd.items() if v>0]
        pie_values = [v for v in cur_bd.values() if v>0]
        if pie_values:
            fig_pie = go.Figure(go.Pie(
                labels=pie_labels, values=pie_values,
                marker=dict(colors=[COLORS.get(l,"#888") for l in pie_labels]),
                hole=0.52, textinfo="label+percent",
                textfont=dict(size=9, color="#e2e8f0"),
            ))
            fig_pie.update_layout(
                title=dict(text="Current Asset Allocation", font=dict(size=12,color="#e2e8f0")),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Mono",size=9,color="#a8b8cc"),
                legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=8),orientation="v"),
                height=320, margin=dict(l=10,r=10,t=40,b=10),
                annotations=[dict(text=fmt(cur_gross-cur_debt),x=0.5,y=0.5,
                    font=dict(size=11,color="#e2e8f0",family="DM Mono"),showarrow=False)]
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        plot_years = [y for y in years_list if y<=horizon]
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="Gross Assets", x=[f"Y{y}" for y in plot_years],
            y=[nw_data[y]["gross"]/1e5 for y in plot_years], marker_color="#3ecf8e"))
        fig_bar.add_trace(go.Bar(name="Liabilities", x=[f"Y{y}" for y in plot_years],
            y=[nw_data[y]["debt"]/1e5 for y in plot_years], marker_color="#e05252"))
        fig_bar.add_trace(go.Scatter(name="Net Worth", x=[f"Y{y}" for y in plot_years],
            y=[nw_data[y]["net"]/1e5 for y in plot_years],
            mode="lines+markers", line=dict(color="#c9a84c",width=2,dash="dot")))
        fig_bar.update_layout(barmode="group",
            title=dict(text="Assets vs Liabilities (₹ Lakhs)",font=dict(size=12,color="#e2e8f0")),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Mono",size=9,color="#a8b8cc"),
            legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=8),orientation="h",y=-0.2),
            xaxis=dict(gridcolor="#1e2d46"), yaxis=dict(gridcolor="#1e2d46",title="₹ Lakhs"),
            height=320, margin=dict(l=30,r=10,t=40,b=30))
        st.plotly_chart(fig_bar, use_container_width=True)

    # Retirement readiness
    self_age      = p.get("self_age", 30)
    retire_age    = p.get("self_retire", 60)
    yrs_to_ret    = max(0, retire_age - self_age)
    monthly_exp   = sum(p.get("expenses",{}).values()) or sum(
        e["amount"] for mk_tmp,bgt in pget("monthly_budgets",{}).items()
        for section in ["fixed","variable"] for e in bgt.get(section,[])
    ) / max(1, len(pget("monthly_budgets",{})))
    monthly_inc   = p.get("self_monthly_inc",0) + (p.get("spouse_monthly_inc",0) if p.get("include_spouse") else 0)
    ann_exp_ret   = (monthly_exp*12) * ((1+(pget("inflation_rate",INFLATION))/100)**yrs_to_ret)
    target_corpus = ann_exp_ret * 25
    net_at_ret,*_ = compute_net_worth(p, rates, yrs_to_ret)
    readiness     = min(100, int(net_at_ret/max(1,target_corpus)*100))
    r_color = "var(--accent-green)" if readiness>=80 else ("var(--accent-gold)" if readiness>=50 else "var(--accent-red)")
    r_label = "ON TRACK ✅" if readiness>=80 else ("NEEDS ATTENTION ⚠️" if readiness>=50 else "CRITICAL 🚨")

    st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
        border-radius:10px;padding:20px 24px;margin:16px 0;">
        <div style="font-family:DM Mono,monospace;font-size:10px;color:var(--text-muted);margin-bottom:8px;">RETIREMENT READINESS</div>
        <div style="display:flex;align-items:center;gap:24px;">
            <div style="font-size:48px;font-weight:700;color:{r_color};">{readiness}<span style="font-size:20px;">/100</span></div>
            <div>
                <div style="font-size:14px;font-weight:600;color:{r_color};margin-bottom:4px;">{r_label}</div>
                <div style="font-size:11px;color:var(--text-secondary);">Retire at {retire_age} · {yrs_to_ret} years away</div>
                <div style="font-size:11px;color:var(--text-secondary);">Target: <b style="color:var(--accent-gold);">{fmt(target_corpus)}</b> · Projected: <b style="color:{r_color};">{fmt(net_at_ret)}</b></div>
            </div>
        </div>
        <div style="height:8px;background:var(--border);border-radius:4px;margin-top:12px;">
            <div style="width:{readiness}%;height:100%;background:{r_color};border-radius:4px;"></div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Tax snapshot
    sec_header("🧾 Tax Optimisation", "80C / 80D / NPS")
    epf_yr      = p.get("epf_monthly",0)*12
    nps_yr      = p.get("nps_monthly",0)*12
    ins_prem    = sum(i["premium"] for i in p.get("ins_list",[]) if i["type"] not in ["Health","Vehicle"])
    health_prem = sum(i["premium"] for i in p.get("ins_list",[]) if i["type"]=="Health")
    total_80c   = min(epf_yr+nps_yr+ins_prem, 150000)
    nps_80ccd   = min(nps_yr, 50000)
    tc1,tc2,tc3 = st.columns(3)
    with tc1: metric_card("80C UTILISED", fmt(total_80c), f"Limit ₹1.5L · {'✅ Maxed' if total_80c>=150000 else f'Room: {fmt(150000-total_80c)}'}", "green" if total_80c>=150000 else "gold")
    with tc2: metric_card("80CCD(1B) NPS", fmt(nps_80ccd), f"₹50K limit · {'✅ Maxed' if nps_80ccd>=50000 else f'Room: {fmt(50000-nps_80ccd)}'}", "green" if nps_80ccd>=50000 else "gold")
    with tc3: metric_card("80D HEALTH", fmt(health_prem), f"{'✅ Covered' if health_prem>0 else '⚠️ No health cover'}", "green" if health_prem>0 else "red")


# ═══════════════════════════════════════════════════════════════════
# SECTION: AI ADVISOR (preserved from original)
# ═══════════════════════════════════════════════════════════════════
def build_financial_context(p):
    monthly_inc = p.get("self_monthly_inc",0) + (p.get("spouse_monthly_inc",0) if p.get("include_spouse") else 0)
    # Get average monthly expenses from budget history
    budgets = pget("monthly_budgets", {})
    if budgets:
        all_exp = [sum(e["amount"] for section in ["fixed","variable"] for e in bgt.get(section,[]))
                   for bgt in budgets.values()]
        expenses = sum(all_exp)/len(all_exp) if all_exp else 0
    else:
        expenses = sum(p.get("expenses",{}).values())

    # Assets
    legacy = _build_legacy_assets(p)
    user_assets = p.get("asset_registry",[])
    all_assets = legacy + user_assets
    gross_assets = sum(_flt(a.get("value",0)) for a in all_assets)
    loan_os  = sum(_flt(l.get("outstanding",0)) for l in p.get("loan_list",[]))
    loan_emi = sum(_flt(l.get("emi",0)) for l in p.get("loan_list",[]))
    mf_sip   = sum(_flt(m.get("sip",0)) for m in p.get("mf_list",[]))
    epf_m    = _flt(p.get("epf_monthly",0))+_flt(p.get("epf_employer",0))
    nps_m    = _flt(p.get("nps_monthly",0))
    ins_prem = sum(_flt(i.get("premium",0)) for i in p.get("ins_list",[]))/12
    net_worth= gross_assets - loan_os
    surplus  = monthly_inc - expenses - loan_emi - mf_sip - epf_m - nps_m - ins_prem

    goals_str = "".join(f"\n  - {g['name']} ({g['type']}): ₹{g.get('target',0):,} in {g.get('years','?')} years" for g in p.get("goal_list",[]))
    self_name  = p.get("self_name","User")
    spouse_name= p.get("spouse_name","") if p.get("include_spouse") else ""

    return f"""You are a professional Indian financial advisor (CFP-level) integrated into EQUITEX PRO.

FAMILY PROFILE:
- Primary: {self_name}, Age: {p.get('self_age',30)}, Retire at: {p.get('self_retire',60)}, Risk: {p.get('self_risk','Moderate')}
- Spouse: {spouse_name + f", Age {p.get('spouse_age','—')}" if spouse_name else "None"}
- Combined monthly income: ₹{monthly_inc:,}

MONTHLY CASH FLOW:
- Living expenses: ₹{expenses:,.0f}/mo
- EMI: ₹{loan_emi:,}/mo | SIP: ₹{mf_sip:,}/mo | EPF: ₹{epf_m:,}/mo | NPS: ₹{nps_m:,}/mo
- Free surplus: ₹{surplus:,.0f}/mo

ASSETS (₹{gross_assets:,} gross): {" | ".join(f"{a.get('name','?')}: {fmt(a.get('value',0))}" for a in all_assets[:6])}
NET WORTH: ₹{net_worth:,} (after ₹{loan_os:,} debt)

GOALS:{goals_str if goals_str else " None set yet."}

GUIDELINES: India-specific advice. Reference 80C,80D,80CCD,LTCG,STCG,PPF,NPS,ELSS. 
Give specific actionable numbers. Be direct about gaps. Bullet points for actions.
Do NOT recommend specific stocks. Focus on allocation, planning, tax optimisation."""


GUIDED_QUESTIONS = [
    ("🏠 Can I buy a house?", "Based on my profile, can I afford to buy a house? What price range, EMI, and impact on retirement?"),
    ("📈 Retirement readiness?", "Analyse my retirement readiness. Am I saving enough? What should I change?"),
    ("👶 Child education plan", "Plan for child's higher education — corpus needed, how to invest, am I on track?"),
    ("🧾 Reduce my taxes?", "Suggest specific actions to optimise tax — 80C, 80D, NPS, ELSS and other deductions."),
    ("🛡 Insurance adequate?", "Analyse my insurance coverage — life, health. Where are the gaps?"),
    ("💰 Invest my surplus?", "Given my surplus, risk profile and goals, how should I invest? Specific action plan."),
    ("⚖️ Prepay loans?", "Should I prepay any loan vs invest? Give me the numbers and recommendation."),
    ("📊 Full health check", "Comprehensive assessment — strengths, weaknesses, top 5 actions to take now."),
]

GROQ_API_URL    = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL      = "llama-3.3-70b-versatile"
GROQ_SIGNUP_URL = "https://console.groq.com"

def _call_groq(api_key, system, messages, max_tokens=2000):
    import requests as _req
    payload = {
        "model": GROQ_MODEL, "max_tokens": max_tokens,
        "messages": [{"role":"system","content":system}] + messages,
        "temperature": 0.4,
    }
    resp = _req.post(GROQ_API_URL,
        headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
        json=payload, timeout=60)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    elif resp.status_code == 401: raise ValueError("invalid_key")
    elif resp.status_code == 429: raise ValueError("rate_limit")
    else:
        try:    err = resp.json().get("error",{}).get("message", resp.text[:200])
        except: err = resp.text[:200]
        raise ValueError(f"api_error:{resp.status_code}:{err}")


def render_ai_advisor_section():
    sec_header("🤖 AI Financial Advisor", "POWERED BY LLAMA 3.3 VIA GROQ (FREE)")
    p = get_profile()
    if not p.get("self_name"):
        st.info("👤 Fill in your Profile tab first so the AI has your financial context.")
        return

    context   = build_financial_context(p)
    groq_key  = st.session_state.get("groq_api_key","")

    if not groq_key:
        st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
            border-radius:10px;padding:20px 24px;margin-bottom:16px;">
            <div style="font-size:15px;font-weight:600;color:var(--text-primary);margin-bottom:8px;">
                Connect your free Groq API key to activate AI Advisor</div>
            <div style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">
                <b>Step 1.</b> Visit <a href="{GROQ_SIGNUP_URL}" target="_blank"
                    style="color:var(--accent-blue);">console.groq.com</a> and create a free account<br>
                <b>Step 2.</b> Go to API Keys → Create new key<br>
                <b>Step 3.</b> Paste it below and click Save
            </div>
            <div style="font-size:11px;color:var(--text-muted);">
                ✅ Free: 14,400 req/day · 6,000 tokens/min · No billing required<br>
                🔒 Key stored in session only — never persisted to disk
            </div>
        </div>""", unsafe_allow_html=True)
        col_in, col_btn = st.columns([4,1])
        with col_in:
            entered = st.text_input("Paste Groq API key", type="password", key="fa_groq_key_input", placeholder="gsk_...")
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Save & Activate", key="fa_save_groq", type="primary", use_container_width=True):
                if entered.strip().startswith("gsk_"):
                    st.session_state.groq_api_key = entered.strip()
                    st.success("✅ Groq key saved!")
                    st.rerun()
                elif entered.strip():
                    st.error("Should start with gsk_ — check and retry.")
        return

    with st.expander(f"🔑 Groq API Key — ✅ Active ({groq_key[:8]}...)", expanded=False):
        new_k = st.text_input("New API key", type="password", key="fa_groq_key_change", placeholder="gsk_...")
        ca, cb = st.columns(2)
        with ca:
            if st.button("Update", key="fa_groq_update"):
                if new_k.strip(): st.session_state.groq_api_key = new_k.strip(); st.rerun()
        with cb:
            if st.button("Remove", key="fa_groq_remove"):
                del st.session_state["groq_api_key"]; st.rerun()

    st.markdown('''<div style="background:var(--bg-card);border:1px solid var(--border);
        border-radius:8px;padding:11px 16px;margin:0 0 14px;">
        <span style="font-size:11px;color:var(--text-secondary);">
        💡 AI Advisor has your <b>complete financial profile</b> — income, assets, loans, budget history & goals.
        &nbsp;·&nbsp; Model: <b style="color:var(--accent-blue);">Llama 3.3 70B</b> via Groq (free)
        </span></div>''', unsafe_allow_html=True)

    st.markdown('<div style="font-family:DM Mono,monospace;font-size:10px;color:var(--text-muted);margin-bottom:8px;">QUICK QUESTIONS</div>', unsafe_allow_html=True)
    q_cols = st.columns(4)
    for i, (label, prompt) in enumerate(GUIDED_QUESTIONS):
        with q_cols[i%4]:
            if st.button(label, key=f"fa_guided_{i}", use_container_width=True):
                st.session_state.fa_pending_q = prompt
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if "fa_chat_history" not in st.session_state:
        st.session_state.fa_chat_history = []

    for msg in st.session_state.fa_chat_history:
        is_user = msg["role"] == "user"
        bg  = "var(--bg-secondary)" if is_user else "var(--bg-card)"
        bdr = "var(--border)"       if is_user else "var(--accent-blue)"
        aln = "flex-end"            if is_user else "flex-start"
        lbl = "YOU" if is_user else "AI ADVISOR · LLAMA 3.3"
        lc  = "var(--text-muted)"   if is_user else "var(--accent-blue)"
        st.markdown(f'''<div style="display:flex;justify-content:{aln};margin-bottom:10px;">
            <div style="max-width:90%;background:{bg};border:1px solid {bdr};
                border-radius:10px;padding:13px 17px;">
                <div style="font-family:DM Mono,monospace;font-size:9px;color:{lc};
                    margin-bottom:6px;letter-spacing:1px;">{lbl}</div>
                <div style="font-size:13px;color:var(--text-primary);line-height:1.8;
                    white-space:pre-wrap;">{msg["content"]}</div>
            </div></div>''', unsafe_allow_html=True)

    pending = st.session_state.pop("fa_pending_q", "")
    if pending and "fa_user_question" in st.session_state:
        del st.session_state["fa_user_question"]

    user_q = st.text_area("Ask your AI Advisor...", value=pending, height=80,
        key="fa_user_question",
        placeholder="e.g. 'Am I on track for retirement?' · 'How to reduce my tax?'")

    c1, c2, _ = st.columns([1,1,4])
    with c1: send = st.button("📤 Ask", key="fa_send", type="primary", use_container_width=True)
    with c2:
        if st.button("🗑 Clear", key="fa_clear_chat", use_container_width=True):
            st.session_state.fa_chat_history = []; st.rerun()

    if send and user_q.strip():
        st.session_state.fa_chat_history.append({"role":"user","content":user_q.strip()})
        if "fa_user_question" in st.session_state:
            del st.session_state["fa_user_question"]
        with st.spinner("Llama 3.3 is analysing your financial profile..."):
            try:
                reply = _call_groq(groq_key, context,
                    [{"role":m["role"],"content":m["content"]} for m in st.session_state.fa_chat_history])
                st.session_state.fa_chat_history.append({"role":"assistant","content":reply})
                st.rerun()
            except ValueError as ve:
                st.session_state.fa_chat_history.pop()
                err = str(ve)
                if err=="invalid_key": st.error("🔑 Invalid Groq key — update it above.")
                elif err=="rate_limit": st.warning("⏳ Rate limited. Wait 10s and retry.")
                else: st.error(f"Groq error: {err}")
            except Exception as e:
                if st.session_state.fa_chat_history and st.session_state.fa_chat_history[-1]["role"]=="user":
                    st.session_state.fa_chat_history.pop()
                st.error(f"Connection error: {e}")


# ═══════════════════════════════════════════════════════════════════
# SECTION: OVERVIEW (enhanced with dual-contributor budget)
# ═══════════════════════════════════════════════════════════════════
def render_overview_section():
    p = get_profile()
    if not p.get("self_name"):
        st.info("👤 Fill in your Profile & Income tab first to see your overview.")
        return

    self_name   = p.get("self_name","Self")
    spouse_name = p.get("spouse_name","Spouse") if p.get("include_spouse") else None
    has_spouse  = bool(p.get("include_spouse"))

    # ── Get current month's budget ─────────────────────────────
    mk = st.session_state.get("fa_budget_month", current_month_key())
    budget   = get_month_budget(mk)
    total_income, total_exp, total_sav, surplus, total_fixed, total_variable = _budget_summary(budget)

    # ── Assets ─────────────────────────────────────────────────
    legacy = _build_legacy_assets(p)
    user_assets = get_assets()
    all_assets = legacy + user_assets
    total_nw = sum(_flt(a.get("value",0)) for a in all_assets)
    total_debt = sum(_flt(l.get("outstanding",0)) for l in p.get("loan_list",[]))
    net_worth = total_nw - total_debt

    # ── Header banner ──────────────────────────────────────────
    nw_color = "var(--accent-green)" if net_worth >= 0 else "var(--accent-red)"
    st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
        border-left:4px solid var(--accent-gold);border-radius:10px;
        padding:20px 24px;margin-bottom:20px;
        display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
        <div>
            <div style="font-size:22px;font-weight:700;color:var(--text-primary);">
                {self_name}{"  &  " + spouse_name if has_spouse else ""} — Financial Overview</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:3px;">
                Age {p.get('self_age','—')} · Retire at {p.get('self_retire','—')} · {p.get('self_risk','—')} Risk
                · {month_label(mk)}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:10px;color:var(--text-muted);letter-spacing:2px;">FAMILY NET WORTH</div>
            <div style="font-size:30px;font-weight:800;color:{nw_color};">{fmt(net_worth)}</div>
            <div style="font-size:10px;color:var(--text-secondary);">Assets {fmt(total_nw)} · Debt −{fmt(total_debt)}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── 4 top metrics ──────────────────────────────────────────
    mc1,mc2,mc3,mc4 = st.columns(4)
    with mc1: metric_card("MONTHLY INCOME",   fmt(total_income),  f"{month_label(mk)}", "green")
    with mc2: metric_card("MONTHLY EXPENSES", fmt(total_exp),     "Fixed + Variable", "red")
    with mc3: metric_card("SAVINGS THIS MONTH",fmt(total_sav),    "Invested", "blue")
    with mc4: metric_card("FREE SURPLUS",     fmt(surplus),
                          "Investable" if surplus>=0 else "⚠️ Deficit",
                          "green" if surplus>=0 else "red")

    # ── Asset breakdown ────────────────────────────────────────
    sec_header("🏦 Assets Breakdown")
    if all_assets:
        left, right = st.columns(2)
        with left:
            st.markdown('<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:16px;">', unsafe_allow_html=True)
            for a in all_assets:
                val = _flt(a.get("value",0))
                pct = round(val/total_nw*100,1) if total_nw>0 else 0
                owner = a.get("owner","self")
                oc = OWNER_COLORS.get(owner, OWNER_COLORS["self"])
                owner_label = {"self":self_name,"spouse":spouse_name or "Spouse","joint":"Joint"}.get(owner,owner)
                st.markdown(f"""<div style="display:flex;align-items:center;padding:7px 0;
                    border-bottom:1px solid var(--border);">
                    <div style="flex:2;font-size:12px;color:var(--text-secondary);">{a.get('name','—')}</div>
                    <div style="flex:1;height:4px;background:var(--border);border-radius:2px;margin:0 8px;">
                        <div style="width:{pct}%;height:100%;background:var(--accent-blue);border-radius:2px;"></div>
                    </div>
                    <span style="font-size:9px;padding:1px 6px;border-radius:10px;
                        background:{oc['bg']};color:{oc['text']};margin-right:8px;">{owner_label}</span>
                    <div style="font-size:12px;font-weight:600;color:var(--text-primary);min-width:80px;text-align:right;">{fmt(val)}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            # Budget donut for current month
            if total_exp > 0 or total_sav > 0:
                surplus_for_chart = max(0, surplus)
                chart_labels = ["Fixed Expenses","Variable Expenses","Savings","Surplus"]
                chart_values = [total_fixed, total_variable, total_sav, surplus_for_chart]
                chart_colors = ["#e05252","#f59e0b","#3ecf8e","#4a9eff"]
                fig = go.Figure(go.Pie(
                    labels=chart_labels, values=chart_values,
                    hole=0.52, textinfo="label+percent",
                    textfont=dict(size=9,color="#e2e8f0"),
                    marker=dict(colors=chart_colors),
                ))
                fig.update_layout(
                    title=dict(text=f"Budget — {month_label(mk)}", font=dict(size=11,color="#e2e8f0")),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="DM Mono",size=9,color="#a8b8cc"),
                    legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=8),orientation="h"),
                    height=300, margin=dict(l=10,r=10,t=40,b=10),
                    annotations=[dict(text=fmt(total_income),x=0.5,y=0.5,
                        font=dict(size=10,color="#e2e8f0",family="DM Mono"),showarrow=False)]
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add assets in the Assets tab to see your breakdown here.")

    # ── Goals summary ──────────────────────────────────────────
    goals = p.get("goal_list",[])
    if goals:
        sec_header("🎯 Goals")
        gcols = st.columns(min(len(goals),3))
        for gi, g in enumerate(goals[:6]):
            target = _flt(g.get("target",0))
            saved  = _flt(g.get("saved",0))
            pct_done = min(round(saved/target*100,1) if target>0 else 0,100)
            with gcols[gi%3]:
                g_color = "var(--accent-green)" if pct_done>=100 else ("var(--accent-gold)" if pct_done>=50 else "var(--accent-red)")
                st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:8px;padding:14px 16px;margin-bottom:8px;">
                    <div style="font-size:12px;font-weight:600;color:var(--text-primary);">{g.get('name','Goal')}</div>
                    <div style="font-size:10px;color:var(--text-muted);margin:2px 0 8px;">Target: {fmt(target)} · {g.get('years','?')}y</div>
                    <div style="height:5px;background:var(--border);border-radius:3px;margin-bottom:4px;">
                        <div style="height:5px;width:{pct_done}%;background:{g_color};border-radius:3px;"></div>
                    </div>
                    <div style="font-size:10px;color:{g_color};">{pct_done}% funded · {fmt(saved)} saved</div>
                </div>""", unsafe_allow_html=True)

    # ── Quick edit ─────────────────────────────────────────────
    sec_header("✏️ Quick Edit")
    st.caption("Edit values directly here without switching tabs.")
    with st.expander("👤 Income", expanded=False):
        qc1,qc2,qc3 = st.columns(3)
        with qc1: new_inc   = st.number_input("Monthly Income (₹)", 0, 10000000, _int(p.get("self_monthly_inc",0)), 5000, key="ov_inc")
        with qc2: new_bonus = st.number_input("Annual Bonus (₹)",   0, 10000000, _int(p.get("self_bonus",0)),       10000, key="ov_bonus")
        with qc3: new_age   = st.number_input("Your Age", 18, 80, _int(p.get("self_age",30),30,18,80), key="ov_age")
        if st.button("💾 Save", key="ov_save_inc"):
            p.update({"self_monthly_inc":new_inc,"self_bonus":new_bonus,"self_age":new_age})
            st.session_state.fa_profile = p; fa_save(); st.success("✅ Saved"); st.rerun()

    with st.expander("💳 Loans", expanded=False):
        loans_e = list(p.get("loan_list",[]))
        if loans_e:
            for li, loan in enumerate(loans_e):
                lc1,lc2,lc3,lc4 = st.columns([3,2,2,1])
                with lc1: loans_e[li]["name"]        = st.text_input("Name", value=loan.get("name",""), key=f"ov_ln{li}")
                with lc2: loans_e[li]["outstanding"]  = st.number_input("Outstanding", 0, 500000000, _int(loan.get("outstanding",0)), 10000, key=f"ov_lo{li}")
                with lc3: loans_e[li]["emi"]          = st.number_input("EMI", 0, 500000, _int(loan.get("emi",0)), 1000, key=f"ov_le{li}")
                with lc4:
                    if st.button("🗑", key=f"ov_ldel{li}"):
                        loans_e.pop(li); p["loan_list"] = loans_e
                        st.session_state.fa_profile = p; fa_save(); st.rerun()
            if st.button("💾 Save Loans", key="ov_save_loans"):
                p["loan_list"] = loans_e; st.session_state.fa_profile = p; fa_save(); st.success("✅ Saved"); st.rerun()
        else: st.info("No loans. Add them in the Liabilities tab.")


# ═══════════════════════════════════════════════════════════════════
# TEMPLATE IMPORT (preserved from original)
# ═══════════════════════════════════════════════════════════════════
def _safe_num(val, default=0):
    if val is None: return default
    try: return float(str(val).replace(",","").replace("₹","").replace("%","").strip())
    except: return default

def _safe_str_imp(val, default=""):
    return str(val).strip() if val is not None else default

def import_from_template(file_obj):
    try: from openpyxl import load_workbook
    except ImportError as e: return None, [f"Missing library: {e}. Run: pip install openpyxl"]
    warns = []
    try: wb = load_workbook(file_obj, data_only=True)
    except Exception as e: return None, [f"Could not open file: {e}"]
    required = ["01 Profile & Income","02 Assets","03 Realty & Insurance","04 Liabilities","05 Monthly Budget","06 Goals & Projections"]
    missing = [s for s in required if s not in wb.sheetnames]
    if missing: return None, [f"Not an EQUITEX Finance Template — missing: {missing}"]

    def c(sheet, row, col): return wb[sheet].cell(row=row, column=col).value
    p = {}
    p["self_name"]         = _safe_str_imp(c("01 Profile & Income",5,3))
    p["self_age"]          = max(18,min(80,int(_safe_num(c("01 Profile & Income",6,3),30))))
    p["self_retire"]       = max(45,min(80,int(_safe_num(c("01 Profile & Income",7,3),60))))
    p["self_risk"]         = _safe_str_imp(c("01 Profile & Income",8,3),"Moderate")
    p["self_inc_type"]     = _safe_str_imp(c("01 Profile & Income",9,3),"Salaried")
    p["self_monthly_inc"]  = int(_safe_num(c("01 Profile & Income",10,3),0))
    p["self_bonus"]        = int(_safe_num(c("01 Profile & Income",13,3),0))
    p["spouse_name"]       = _safe_str_imp(c("01 Profile & Income",21,3))
    p["spouse_age"]        = max(18,min(80,int(_safe_num(c("01 Profile & Income",22,3),28))))
    p["spouse_retire"]     = max(45,min(80,int(_safe_num(c("01 Profile & Income",23,3),58))))
    p["spouse_inc_type"]   = _safe_str_imp(c("01 Profile & Income",24,3),"Salaried")
    p["spouse_monthly_inc"]= int(_safe_num(c("01 Profile & Income",25,3),0))
    p["spouse_bonus"]      = int(_safe_num(c("01 Profile & Income",26,3),0))
    p["include_spouse"]    = bool(p["spouse_name"] or p["spouse_monthly_inc"]>0)

    p["epf_balance"]  = _safe_num(c("02 Assets",19,3),0)
    p["epf_monthly"]  = _safe_num(c("02 Assets",20,3),0)
    p["epf_employer"] = _safe_num(c("02 Assets",21,3),0)
    p["spouse_epf"]   = _safe_num(c("02 Assets",22,3),0)
    p["nps_balance"]  = _safe_num(c("02 Assets",27,3),0)
    p["nps_monthly"]  = _safe_num(c("02 Assets",28,3),0)
    p["spouse_nps"]   = _safe_num(c("02 Assets",29,3),0)
    p["gold_grams"]   = _safe_num(c("02 Assets",47,3),0)
    p["gold_rate"]    = max(1,_safe_num(c("02 Assets",48,3),7500))
    p["gold_type"]    = _safe_str_imp(c("02 Assets",46,3),"Physical Jewellery")
    p["gold_invested"]= _safe_num(c("02 Assets",49,3),0)
    p["gold_value"]   = p["gold_grams"]*p["gold_rate"]
    p["gold_list"]    = [{"type":p["gold_type"],"grams":p["gold_grams"],"rate":p["gold_rate"],
                          "invested":p["gold_invested"],"sgb_units":0,"sgb_issue_price":0}] if p["gold_grams"]>0 else []
    p["stock_value"]  = _safe_num(c("02 Assets",53,3),0)

    ws2 = wb["02 Assets"]
    mf_list = []
    for r in range(5,15):
        name=_safe_str_imp(ws2.cell(r,2).value); inv=_safe_num(ws2.cell(r,3).value); val=_safe_num(ws2.cell(r,4).value); sip=_safe_num(ws2.cell(r,5).value)
        if name or inv>0 or val>0: mf_list.append({"name":name or f"Fund {r-4}","invested":inv,"value":val,"current_value":val,"sip":sip})
    p["mf_list"] = mf_list
    fd_list = []
    for r in range(35,43):
        bank=_safe_str_imp(ws2.cell(r,2).value); ftype=_safe_str_imp(ws2.cell(r,3).value,"FD"); amt=_safe_num(ws2.cell(r,4).value); rate=_safe_num(ws2.cell(r,5).value,6.5); months=_safe_num(ws2.cell(r,6).value,12)
        if rate<1 and rate>0: rate=rate*100
        if amt>0: fd_list.append({"bank":bank,"type":ftype,"amount":amt,"rate":rate,"months":int(months)})
    p["fd_list"] = fd_list

    ws3 = wb["03 Realty & Insurance"]
    re_list = []
    for r in range(5,11):
        name=_safe_str_imp(ws3.cell(r,2).value); rtype=_safe_str_imp(ws3.cell(r,3).value,"Other"); buy=_safe_num(ws3.cell(r,4).value); cur=_safe_num(ws3.cell(r,5).value); rent=_safe_num(ws3.cell(r,6).value); loan=_safe_num(ws3.cell(r,7).value)
        if name or cur>0 or buy>0: re_list.append({"name":name or f"Property {r-4}","type":rtype,"purchased":buy,"current":cur,"rent":rent,"loan":loan})
    p["re_list"] = re_list
    ins_list = []
    for r in range(15,23):
        name=_safe_str_imp(ws3.cell(r,2).value); itype=_safe_str_imp(ws3.cell(r,3).value,"Other"); cover=_safe_num(ws3.cell(r,4).value); prem=_safe_num(ws3.cell(r,5).value); mat=_safe_num(ws3.cell(r,6).value)
        if name or cover>0 or prem>0: ins_list.append({"name":name or itype,"type":itype,"cover":cover,"premium":prem,"maturity":mat,"monthly_payout":0})
    p["ins_list"] = ins_list

    ws4 = wb["04 Liabilities"]
    loan_list = []
    for r in range(5,13):
        ltype=_safe_str_imp(ws4.cell(r,2).value); bank=_safe_str_imp(ws4.cell(r,3).value); os=_safe_num(ws4.cell(r,4).value); emi=_safe_num(ws4.cell(r,5).value); rate=_safe_num(ws4.cell(r,6).value,0); months=int(_safe_num(ws4.cell(r,7).value,0))
        if rate<1 and rate>0: rate=rate*100
        if os>0 or emi>0: loan_list.append({"type":ltype or "Other","bank":bank,"outstanding":os,"emi":emi,"rate":rate,"months":months,"name":f"{ltype} — {bank}" if bank else ltype or "Loan"})
    p["loan_list"] = loan_list

    ws5 = wb["05 Monthly Budget"]
    BUDGET_ROWS = {
        "Rent / Home Loan EMI":4,"Home Loan EMI":5,"Car Loan EMI":6,"School / College Fees":7,
        "Life Insurance Premium":8,"Health Insurance Premium":9,"Vehicle Insurance":10,"OTT / Subscriptions":11,"Other Fixed":12,
        "Groceries & Household":16,"Fuel & Transport":17,"Dining & Eating Out":18,"Entertainment & OTT":19,
        "Clothing & Shopping":20,"Medical & Health":21,"Travel & Vacation":22,"Gifts & Personal Care":23,"Parents / Dependants":24,"Other Variable":25,
    }
    expenses = {}
    for key,row in BUDGET_ROWS.items():
        val = _safe_num(ws5.cell(row,3).value,0)
        if val>0: expenses[key] = int(val)
    p["expenses"] = expenses

    ws6 = wb["06 Goals & Projections"]
    def pct_rate(row):
        raw = _safe_num(ws6.cell(row,3).value,0)
        return raw*100 if raw<=1 else raw
    custom_rates = {"stocks":pct_rate(4),"mf":pct_rate(5),"epf":pct_rate(6),"nps":pct_rate(7),"fd":pct_rate(8),"gold":pct_rate(9),"realty":pct_rate(10)}
    for k,v in custom_rates.items():
        if v==0: custom_rates[k] = BENCHMARKS.get(k,8.0)
    p["custom_rates"]   = custom_rates
    p["inflation_rate"] = pct_rate(11) or INFLATION

    goal_list = []
    for r in range(15,23):
        gtype=_safe_str_imp(ws6.cell(r,2).value); target=_safe_num(ws6.cell(r,3).value); saved=_safe_num(ws6.cell(r,5).value); years=int(_safe_num(ws6.cell(r,6).value,10))
        if gtype and (target>0 or saved>0 or years!=10): goal_list.append({"type":gtype,"name":gtype,"target":int(target),"saved":int(saved),"years":years})
    p["goal_list"] = goal_list

    if not mf_list:   warns.append("No MF data — fill rows 5–14 in '02 Assets'.")
    if not ins_list:  warns.append("No insurance — fill rows 15–22 in '03 Realty & Insurance'.")
    if not goal_list: warns.append("No goals — fill rows 15–22 in '06 Goals & Projections'.")
    return p, warns


# ═══════════════════════════════════════════════════════════════════
# MAIN PAGE ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
def render_template_import_inner():
    with st.expander("📥 Import from EQUITEX Finance Template (.xlsx)", expanded=not st.session_state.get("fa_profile")):
        st.markdown("""<div style="font-size:12px;color:var(--text-secondary);margin-bottom:10px;">
            Download the EQUITEX Finance Template, fill it in Excel, then upload here to auto-populate all fields.
        </div>""", unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload Template", type=["xlsx","xls"],
            key="fa_template_upload", label_visibility="collapsed")
        last_imported = st.session_state.get("fa_last_import_name","")
        if uploaded and uploaded.name != last_imported:
            with st.spinner("Importing..."):
                profile, warns = import_from_template(uploaded)
            if profile is None:
                for w in warns: st.error(w)
            else:
                st.session_state.fa_profile          = profile
                st.session_state.fa_loaded           = True
                st.session_state.fa_last_import_name = uploaded.name
                fa_save()
                st.success(f"✅ Imported {profile.get('self_name','your data')} successfully!")
                if warns:
                    for w in warns: st.warning(w)
                st.rerun()
        elif uploaded and uploaded.name == last_imported:
            st.info(f"✅ **{uploaded.name}** already imported.")


def page_finance():
    """Main entry point — called from FinAnalysis_Pro.py."""

    if not st.session_state.get("fa_loaded"):
        fa_load()
        if st.session_state.get("fa_loaded"): st.rerun()

    p = get_profile()

    # ── Header ────────────────────────────────────────────────
    hcol1, hcol2 = st.columns([3,2])
    with hcol1:
        st.markdown("""<div style="padding:8px 0 10px;">
            <div style="font-family:'Fraunces',serif;font-size:28px;font-weight:600;color:var(--text-primary);">
                💼 Finance Advisor</div>
            <div style="font-family:var(--font-mono,DM Mono,monospace);font-size:10px;color:var(--text-muted);margin-top:2px;">
                PERSONAL WEALTH INTELLIGENCE · POWERED BY EQUITEX PRO</div>
        </div>""", unsafe_allow_html=True)
    with hcol2:
        if p.get("self_name"):
            import datetime as _dt
            st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--accent-green);
                border-radius:8px;padding:8px 14px;margin-top:12px;font-size:11px;">
                <span style="color:var(--accent-green);font-weight:600;">✅ {p.get('self_name')}</span>
                {"  +  <span style='color:var(--accent-gold);font-weight:600;'>" + p.get('spouse_name','') + "</span>" if p.get('include_spouse') and p.get('spouse_name') else ""}
                <span style="color:var(--text-muted);margin-left:8px;">saved to <code style="font-size:10px;color:var(--accent-blue);">equitex_profile.json</code></span>
            </div>""", unsafe_allow_html=True)
            profile_json = json.dumps(p, indent=2, default=str)
            fname = f"equitex_{p.get('self_name','profile').replace(' ','_')}_{_dt.date.today()}.json"
            st.download_button("⬇️ Backup", data=profile_json, file_name=fname,
                mime="application/json", key="fa_dl_backup")

    # ── Backup/Import ─────────────────────────────────────────
    with st.expander("📂 Restore from backup / Import Excel", expanded=not p.get("self_name")):
        rtab1, rtab2 = st.tabs(["🔄 Restore JSON backup", "📥 Import Excel template"])
        with rtab1:
            bk = st.file_uploader("Upload JSON backup", type=["json"],
                key="fa_backup_upload", label_visibility="collapsed")
            if bk:
                try:
                    restored = json.loads(bk.read().decode("utf-8"))
                    if isinstance(restored, dict) and restored.get("self_name"):
                        st.session_state.fa_profile = restored
                        st.session_state.fa_loaded  = True
                        for k in [k for k in list(st.session_state.keys())
                                  if k.startswith("fa_") and k not in
                                  ("fa_profile","fa_loaded","fa_backup_upload","fa_chat_history")]:
                            del st.session_state[k]
                        fa_save()
                        st.success(f"✅ Restored {restored.get('self_name')}")
                        st.rerun()
                    else: st.error("Doesn't look like an EQUITEX backup.")
                except Exception as e: st.error(f"Could not read backup: {e}")
        with rtab2:
            render_template_import_inner()

    # ── Main tabs ─────────────────────────────────────────────
    tabs = st.tabs([
        "🏠 Overview",
        "👨‍👩‍👧 Family Dashboard",
        "👤 Profile & Income",
        "📊 Monthly Budget",
        "🏦 Assets",
        "💳 Liabilities",
        "🎯 Goals",
        "📈 Projections",
        "🤖 AI Advisor",
    ])

    with tabs[0]: render_overview_section()
    with tabs[1]: render_family_dashboard()
    with tabs[2]: render_profile_section()
    with tabs[3]: render_budget_section()
    with tabs[4]: render_assets_section()
    with tabs[5]: render_liabilities_section()
    with tabs[6]: render_goals_section()
    with tabs[7]: render_projections_section()
    with tabs[8]: render_ai_advisor_section()

