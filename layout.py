"""Customer website look: top bar, header, hero, store-info cards and footer.

Colours were checked for contrast: every text colour below passes WCAG AA
(4.5:1 or better) on the background it sits on.
"""
from __future__ import annotations

import base64
import html
import io
import urllib.parse
from datetime import date

import streamlit as st
from PIL import Image

import db
import ui

# ---------------------------------------------------------------- design tokens
NAVY_900 = "#00084D"   # top bar, footer
NAVY = "#001089"       # brand
NAVY_700 = "#000C66"   # hover
YELLOW = "#FFC93C"     # on navy: 11.6:1
ON_NAVY = "#E6E9FF"    # body text on navy: 15:1
ON_NAVY_MUTED = "#C2C9F2"  # secondary text on navy: 10.9:1
INK = "#0F172A"        # on white: 17:1
MUTED = "#475569"      # on white: 7.6:1
LINE = "#DDE1EC"
SURFACE = "#F5F7FC"
SOFT = "#EEF1FF"
WA = "#0B7A3E"         # white on it: 5.6:1

FONTS = ("https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800"
         "&family=DM+Serif+Display:ital@0;1&family=JetBrains+Mono:wght@500;700&display=swap")

ICON = {
    "truck": '<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>'
             '<circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 '
             '19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 '
             '2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 '
             '2.81.7A2 2 0 0 1 22 16.92z"/>',
    "chat": '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21'
            'l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 '
            '8 8v.5z"/>',
    "pin": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "mail": '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>'
            '<polyline points="22,6 12,13 2,6"/>',
    "store": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/>'
             '<path d="M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/>',
    "search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "box": '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73'
           'l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/>'
           '<line x1="12" y1="22.08" x2="12" y2="12"/>',
    "cash": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/>'
            '<path d="M6 12h.01M18 12h.01"/>',
}


def icon(name: str, size: int = 18, color: str = NAVY) -> str:
    """Icon as a tiny image (Streamlit strips inline <svg> from HTML)."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
           f'fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
           f'{ICON[name]}</svg>')
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img class="gcc-ic" src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" alt="">'



e = html.escape


@st.cache_data(show_spinner=False)
def _img_b64(path: str, crop: tuple | None = None, size: int | None = None) -> str:
    img = Image.open(path).convert("RGB")
    if crop:
        img = img.crop(crop)
        side = max(img.size) + 24
        sq = Image.new("RGB", (side, side), img.getpixel((2, 2)))
        sq.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
        img = sq
    if size:
        img.thumbnail((size, size))
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def logo_icon() -> str:   # just the cart, square, for the header
    return _img_b64(ui.LOGO, crop=(100, 160, 450, 395), size=128)


def logo_full() -> str:   # the full artwork with tagline, for the hero card
    return _img_b64(ui.LOGO, size=640)


def zones(sectors) -> list[dict]:
    """One row per delivery zone, in list order: fee, time and free-delivery limit."""
    out, seen = [], set()
    for _, r in sectors.iterrows():
        z = r.zone or r["name"]
        if z not in seen:
            seen.add(z)
            out.append({"zone": z, "fee": float(r.fee), "eta": r.eta, "free_over": float(r.free_over or 0)})
    return out


def digits(s: str) -> str:
    return "".join(ch for ch in str(s) if ch.isdigit() or ch == "+")


# ---------------------------------------------------------------- CSS
CSS = f"""
<style>
@import url('{FONTS}');
:root {{ --navy:{NAVY}; --navy9:{NAVY_900}; --ink:{INK}; --muted:{MUTED}; --line:{LINE}; --yellow:{YELLOW}; }}

/* ---------- page frame: full-width sections, no Streamlit sidebar/toolbar */
.stApp {{ background:#fff; }}
header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stDecoration"], [data-testid="stHeaderActionElements"] {{ display:none !important; }}
[data-testid="stMainBlockContainer"] {{ padding:0 !important; max-width:none !important; }}
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {{ gap:0 !important; }}
.gcc-wrap, .st-key-gcc-page, .st-key-gcc-nav, .st-key-gcc-footer {{
  padding-left:max(16px, calc((100% - 1320px) / 2)) !important;
  padding-right:max(16px, calc((100% - 1320px) / 2)) !important; }}
.st-key-gcc-page {{ padding-top:32px !important; padding-bottom:56px !important; gap:1rem; }}

/* ---------- readable text on white, whatever the visitor's light/dark setting */
.stApp {{ color-scheme:light; color:{INK}; }}
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li, .stApp [data-testid="stMarkdownContainer"] strong,
.stApp [data-testid="stText"], .stApp [data-testid="stMetricValue"] {{ color:{INK}; }}
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p {{ color:{MUTED} !important; }}
.stApp [data-testid="stPageLink-NavLink"] p, .stApp [data-testid="stPageLink-NavLink"] span {{ color:{NAVY}; font-weight:600; }}
.stApp [data-testid="stAlertContentSuccess"] p {{ color:#0B4A26 !important; }}
.stApp [data-testid="stAlertContentInfo"] p {{ color:#0B3A75 !important; }}
.stApp [data-testid="stAlertContentWarning"] p {{ color:#5C3D00 !important; }}
.stApp [data-testid="stAlertContentError"] p {{ color:#7A1010 !important; }}

/* ---------- type */
.stApp, .stApp *:not([data-testid="stIconMaterial"]):not(code):not(pre):not(.gcc-mono) {{
  font-family:'Outfit', system-ui, -apple-system, 'Segoe UI', sans-serif; }}
.gcc-mono, .gcc-mono * {{ font-family:'JetBrains Mono', ui-monospace, monospace !important; }}
.gcc-serif {{ font-family:'DM Serif Display', Georgia, serif !important; font-style:italic; }}
.stApp h1, .stApp h2, .stApp h3 {{ color:var(--ink); letter-spacing:-0.02em; }}
.gcc-ic {{ flex:none; vertical-align:-3px; }}

/* ---------- top bar */
.gcc-topbar {{ background:{NAVY_900}; color:{ON_NAVY}; font-size:.92rem; }}
.gcc-topbar-in {{ display:flex; align-items:center; justify-content:space-between; gap:12px;
  flex-wrap:wrap; padding-top:9px; padding-bottom:9px; }}
.gcc-topbar b {{ color:#fff; font-weight:700; }}
.gcc-topbar .free {{ color:{YELLOW}; font-weight:600; }}
.gcc-tb-msg {{ display:flex; align-items:center; gap:8px; }}
.gcc-pills {{ display:flex; gap:8px; flex-wrap:wrap; }}
.gcc-pill {{ display:inline-flex; align-items:center; gap:6px; padding:5px 12px; border-radius:999px;
  border:1px solid rgba(255,255,255,.28); color:#fff !important; text-decoration:none !important;
  font-size:.85rem; white-space:nowrap; }}
.gcc-pill:hover {{ background:rgba(255,255,255,.1); }}
.gcc-pill.wa {{ background:{WA}; border-color:{WA}; }}

/* ---------- header / navbar */
.st-key-gcc-nav {{ background:#fff; border-bottom:1px solid {LINE}; padding-top:12px !important;
  padding-bottom:4px !important; position:sticky; top:0; z-index:50; box-shadow:0 2px 10px rgba(15,23,42,.04); }}
.st-key-gcc-links {{ border-top:1px solid {LINE}; margin-top:10px; padding-top:4px; padding-bottom:2px; margin-left:-10px; }}
.gcc-brand {{ display:flex; align-items:center; gap:12px; }}
.gcc-brand img {{ width:52px; height:52px; border-radius:14px; display:block;
  box-shadow:0 4px 14px rgba(0,16,137,.25); }}
.gcc-brand-line {{ display:flex; align-items:center; gap:8px; white-space:nowrap; }}
.gcc-title {{ font-size:1.45rem; font-weight:800; color:{INK}; letter-spacing:-0.02em; white-space:nowrap; line-height:1.1; }}
.gcc-badge {{ background:{NAVY}; color:#fff; font-size:.68rem; font-weight:700; letter-spacing:.06em;
  padding:3px 7px; border-radius:6px; white-space:nowrap; }}
.gcc-tag {{ color:{MUTED}; font-size:.95rem; margin-top:2px; white-space:nowrap; }}
.st-key-gcc-links [data-testid="stPageLink-NavLink"], .st-key-gcc-links button, .gcc-navlink {{
  color:{INK} !important; font-weight:500 !important; text-decoration:none !important; }}
.st-key-gcc-links [data-testid="stPageLink-NavLink"] *, .st-key-gcc-links button * {{ color:{INK} !important; font-weight:500 !important; }}
.st-key-gcc-links [data-testid="stPopoverButton"], .st-key-gcc-links button {{ border:none !important;
  background:transparent !important; box-shadow:none !important; padding:6px 10px !important; }}
.st-key-gcc-links [data-testid="stPopoverButton"]:hover, .st-key-gcc-links button:hover,
.st-key-gcc-links [data-testid="stPageLink-NavLink"]:hover {{ background:{SURFACE} !important; border-radius:8px; }}
.st-key-gcc-links [data-testid="stPageLink-NavLink"] p, .st-key-gcc-links button p {{ font-size:1.02rem !important; }}
.gcc-navlink {{ display:inline-block; padding:6px 10px; border-radius:8px; font-size:1.02rem; font-weight:500 !important; }}
.gcc-navlink:hover {{ background:{SURFACE}; }}
.st-key-gcc-cart [data-testid="stPageLink-NavLink"] {{ background:{NAVY}; border-radius:12px; padding:8px 14px; }}
.st-key-gcc-cart [data-testid="stPageLink-NavLink"]:hover {{ background:{NAVY_700}; }}
.st-key-gcc-cart [data-testid="stPageLink-NavLink"] p, .st-key-gcc-cart [data-testid="stPageLink-NavLink"] span {{
  color:#fff !important; font-weight:600; }}

/* ---------- hero */
.gcc-hero {{ background:radial-gradient(1200px 500px at 15% 0%, #0A1FB8 0%, {NAVY} 45%, {NAVY_900} 100%);
  color:#fff; padding-top:56px; padding-bottom:64px; }}
.gcc-hero-grid {{ display:grid; grid-template-columns:minmax(0,1.5fr) minmax(0,1fr); gap:40px; align-items:center; }}
.gcc-chips {{ display:flex; align-items:center; flex-wrap:wrap; gap:10px; font-weight:600; letter-spacing:.02em; }}
.gcc-chip {{ border:1px solid rgba(255,201,60,.55); color:{YELLOW}; border-radius:999px; padding:4px 14px; }}
.gcc-chips .y {{ color:{YELLOW}; }} .gcc-chips .w {{ color:{ON_NAVY}; text-transform:uppercase; }}
.gcc-dot {{ color:{ON_NAVY_MUTED}; }}
.gcc-hero h1 {{ color:#fff !important; font-size:clamp(2.4rem, 5.6vw, 4.5rem) !important; font-weight:800 !important;
  line-height:1.02 !important; letter-spacing:-0.035em; margin:22px 0 18px !important; padding:0 !important; }}
.gcc-hero p.lead {{ color:{ON_NAVY}; font-size:clamp(1.05rem, 1.6vw, 1.3rem); line-height:1.6; font-weight:300; max-width:640px; margin:0; }}
.gcc-cta {{ display:flex; gap:12px; flex-wrap:wrap; margin-top:28px; }}
.gcc-btn {{ display:inline-flex; align-items:center; gap:8px; padding:12px 20px; border-radius:12px;
  font-weight:600; text-decoration:none !important; font-size:1rem; }}
.gcc-btn.light {{ background:#fff; color:{NAVY} !important; }}
.gcc-btn.light:hover {{ background:{SOFT}; }}
.gcc-btn.wa {{ background:{WA}; color:#fff !important; }}
.gcc-btn.wa:hover {{ background:#086332; }}
.gcc-facts {{ display:flex; gap:28px; flex-wrap:wrap; margin-top:34px; padding-top:22px; border-top:1px solid rgba(255,255,255,.18); }}
.gcc-fact b {{ display:block; color:#fff; font-size:1.25rem; font-weight:700; }}
.gcc-fact span {{ color:{ON_NAVY_MUTED}; font-size:.9rem; }}
.gcc-hero-card {{ border:1px solid rgba(255,255,255,.2); border-radius:22px; background:rgba(255,255,255,.04);
  overflow:hidden; }}
.gcc-hero-card > img {{ width:100%; display:block; }}
.gcc-hero-card .row {{ display:flex; gap:10px; padding:16px; border-top:1px solid rgba(255,255,255,.14); flex-wrap:wrap; }}
.gcc-hero-card .row span {{ flex:1 1 160px; display:flex; align-items:center; gap:8px; color:{ON_NAVY};
  background:rgba(255,255,255,.07); border-radius:12px; padding:10px 12px; font-size:.92rem; }}

/* ---------- sections */
.gcc-eyebrow {{ color:{NAVY}; font-weight:700; font-size:.8rem; letter-spacing:.12em; text-transform:uppercase; }}
.gcc-h2 {{ font-size:clamp(1.6rem, 3vw, 2.2rem); font-weight:800; color:{INK}; letter-spacing:-0.025em; margin:2px 0 4px; line-height:1.15; }}
.gcc-sub {{ color:{MUTED}; font-size:1.02rem; margin:0; }}
.gcc-sub b {{ color:{INK}; }}

/* ---------- product cards */
[class*="st-key-pc_"] {{ background:#fff; border:1px solid {LINE} !important; border-radius:16px !important;
  padding:12px !important; transition:box-shadow .15s, border-color .15s; }}
[class*="st-key-pc_"]:hover {{ border-color:#B9C0DA !important; box-shadow:0 8px 24px rgba(15,23,42,.08); }}
.gcc-price {{ font-size:1.2rem; font-weight:700; color:{NAVY}; }}
.gcc-mrp {{ color:#64748B; text-decoration:line-through; font-size:.88rem; margin-left:6px; }}
.gcc-save {{ display:inline-block; white-space:nowrap; background:#FFF1C7; color:#6B4200; border-radius:6px;
  padding:1px 8px; font-size:.78rem; font-weight:700; }}
.gcc-oos {{ background:#FDE2E2; color:#8F1A1A; border-radius:6px; padding:2px 8px; font-size:.8rem; font-weight:700; }}
.gcc-name {{ font-weight:600; color:{INK}; line-height:1.25; min-height:2.5em; font-size:1.02rem; }}
.gcc-urdu {{ color:{MUTED}; font-size:.95rem; direction:rtl; }}
.gcc-unit {{ color:{MUTED}; font-size:.85rem; }}
.gcc-ph {{ aspect-ratio:4/3; width:100%; display:flex; align-items:center; justify-content:center;
  font-size:3.2rem; background:{SOFT}; border-radius:12px; }}

/* ---------- inputs & controls: visible borders, brand focus */
.stApp [data-baseweb="input"], .stApp [data-baseweb="select"] > div, .stApp [data-baseweb="textarea"] {{
  background:#fff !important; border:1px solid #B9C0D4 !important; border-radius:10px !important; }}
.stApp [data-baseweb="input"]:focus-within, .stApp [data-baseweb="select"] > div:focus-within,
.stApp [data-baseweb="textarea"]:focus-within {{ border-color:{NAVY} !important; box-shadow:0 0 0 3px rgba(0,16,137,.15); }}
.stApp input, .stApp textarea {{ background:#fff !important; color:{INK} !important; }}
.stApp input::placeholder, .stApp textarea::placeholder {{ color:#64748B !important; opacity:1; }}
[data-testid="stWidgetLabel"] p {{ color:{INK} !important; font-weight:500; }}
[data-testid^="stBaseButton-primary"], [data-testid^="stBaseLinkButton-primary"] {{
  background:{NAVY} !important; border-color:{NAVY} !important; color:#fff !important; border-radius:10px !important; }}
[data-testid^="stBaseButton-primary"]:hover, [data-testid^="stBaseLinkButton-primary"]:hover {{
  background:{NAVY_700} !important; border-color:{NAVY_700} !important; }}
[data-testid^="stBaseButton-primary"] p, [data-testid^="stBaseLinkButton-primary"] p {{ color:#fff !important; }}
[data-testid="stBaseButton-secondary"], [data-testid="stPopoverButton"] {{ border:1px solid #B9C0D4 !important;
  border-radius:10px !important; color:{INK} !important; background:#fff !important; }}
[data-testid="stButtonGroup"] button {{ border:1px solid #B9C0D4 !important; color:{INK} !important; background:#fff !important; }}
[data-testid="stButtonGroup"] button p {{ color:{INK} !important; }}
[data-testid="stButtonGroup"] button[aria-pressed="true"], [data-testid="stButtonGroup"] button[aria-checked="true"] {{ background:{NAVY} !important; border-color:{NAVY} !important; }}
[data-testid="stButtonGroup"] button[aria-pressed="true"] p, [data-testid="stButtonGroup"] button[aria-checked="true"] p {{ color:#fff !important; font-weight:600; }}
[data-testid="stCheckbox"] label:has(input[role="switch"]:checked) > div:first-of-type {{ background:{NAVY} !important; }}
[data-testid="stCheckbox"] label:has(input[role="switch"]) p {{ color:{INK} !important; }}
[data-testid^="stBaseLinkButton-primary"][disabled] {{ background:#AEB4CC !important; border-color:#AEB4CC !important;
  pointer-events:none; }}
[data-testid^="stBaseLinkButton-primary"][disabled] p {{ color:#1F2547 !important; }}
.stApp a:focus-visible, .stApp button:focus-visible {{ outline:3px solid {YELLOW}; outline-offset:2px; }}

/* ---------- delivery rates table */
.st-key-gcc-rates {{ border:1px solid {LINE}; border-radius:16px; overflow:hidden; background:#fff; }}
[class*="st-key-rate_"] {{ border-top:1px solid {LINE}; padding:6px 16px 6px 0 !important; }}
[class*="st-key-rate_"]:hover {{ background:{SURFACE}; }}
.gcc-rates-row {{ display:grid; grid-template-columns:2.6fr 1.3fr 1.2fr 1.1fr 1.3fr; gap:12px; align-items:center;
  padding:10px 16px; color:{INK}; }}
.gcc-rates-head {{ grid-template-columns:2.6fr 1.3fr 1.2fr 1.1fr 1.3fr 120px; background:{SURFACE};
  font-weight:600; font-size:.92rem; color:{MUTED}; padding:12px 16px; }}
.gcc-rates-row.sel {{ background:{SOFT}; border-radius:10px; }}
.gcc-rates-row .nm {{ display:flex; align-items:center; gap:8px; font-weight:600; font-size:1.02rem; }}
.gcc-rates-row .nm em {{ font-style:normal; background:{NAVY}; color:#fff; font-size:.7rem; padding:2px 7px; border-radius:6px; }}
.gcc-rates-row .zn {{ color:{MUTED}; }}
.gcc-rates-row .tm {{ color:{NAVY}; font-weight:700; }}
.gcc-rates-row .rt b {{ display:block; }} .gcc-rates-row .rt small {{ color:{MUTED}; font-size:.78rem; }}
.gcc-rates-row .fr {{ color:#0B6B37; font-weight:700; }}
.gcc-rate-sel {{ color:{NAVY}; font-weight:700; white-space:nowrap; padding:0 8px; }}
[class*="st-key-rate_"] [data-testid="stBaseButton-secondary"] {{ white-space:nowrap; }}
@media (max-width: 760px) {{
  .gcc-rates-head {{ display:none; }}
  .gcc-rates-row {{ grid-template-columns:1fr 1fr; row-gap:4px; }}
  .gcc-rates-row .nm {{ grid-column:1 / -1; }}
}}

/* ---------- store info cards */
[class*="st-key-info_"] {{ background:{SURFACE}; border:1px solid {LINE} !important; border-radius:20px !important;
  padding:24px !important; }}
.gcc-card-h {{ display:flex; align-items:center; gap:10px; font-size:1.3rem; font-weight:700; color:{INK}; margin-bottom:6px; }}
.gcc-card-h .gcc-ic {{ color:{NAVY}; }}
.gcc-li {{ display:flex; gap:12px; margin:14px 0; color:{INK}; }}
.gcc-li .gcc-ic {{ color:{NAVY}; margin-top:3px; }}
.gcc-li b {{ display:block; font-weight:600; }}
.gcc-li span {{ color:{MUTED}; }}
.gcc-li a {{ color:{NAVY} !important; font-weight:700; text-decoration:none; }}
.gcc-li a.wa {{ color:{WA} !important; }}

/* ---------- footer */
.st-key-gcc-footer {{ background:{NAVY_900}; padding-top:56px !important; padding-bottom:28px !important; color:{ON_NAVY}; }}
.st-key-gcc-footer p, .st-key-gcc-footer span, .st-key-gcc-footer div {{ color:{ON_NAVY}; }}
.gcc-f-brand {{ display:flex; align-items:center; gap:12px; padding:14px; border-radius:16px;
  background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.14); }}
.gcc-f-brand img {{ width:48px; height:48px; border-radius:12px; }}
.st-key-gcc-footer .gcc-f-title {{ color:#fff !important; font-weight:800; font-size:1.2rem; white-space:nowrap; }}
.st-key-gcc-footer .gcc-badge {{ background:#fff; color:{NAVY} !important; }}
.st-key-gcc-footer .gcc-f-tag {{ color:{ON_NAVY_MUTED} !important; font-size:.95rem; }}
.st-key-gcc-footer .gcc-f-h {{ color:#fff !important; font-weight:700; letter-spacing:.08em; font-size:.95rem; margin-bottom:12px; }}
.st-key-gcc-footer .gcc-y {{ color:{YELLOW} !important; font-weight:600; }}
.st-key-gcc-footer .gcc-f-line {{ margin:6px 0; }}
.st-key-gcc-footer .gcc-f-line b {{ color:#fff !important; }}
.st-key-gcc-footer [data-testid="stColumn"] [data-testid="stVerticalBlock"] {{ gap:.35rem !important; }}
.st-key-gcc-footer [data-testid="stBaseButton-tertiary"] {{ padding:2px 0 !important; min-height:0 !important; }}
.st-key-gcc-footer [data-testid="stBaseButton-tertiary"] p {{ color:{ON_NAVY} !important; font-size:1rem; }}
.st-key-gcc-footer [data-testid="stBaseButton-tertiary"]:hover p {{ color:#fff !important; text-decoration:underline; }}
.gcc-f-card {{ display:flex; align-items:center; gap:12px; padding:12px 14px; border-radius:14px; margin-top:10px;
  text-decoration:none !important; border:1px solid rgba(255,255,255,.18); background:rgba(255,255,255,.06); }}
.gcc-f-card.wa {{ background:rgba(11,122,62,.35); border-color:rgba(74,222,128,.45); }}
.gcc-f-card .gcc-ic {{ color:#fff; }}
.st-key-gcc-footer .gcc-f-card small {{ color:{ON_NAVY_MUTED} !important; display:block; font-size:.8rem; }}
.st-key-gcc-footer .gcc-f-card b {{ color:#fff !important; font-size:1.05rem; }}
.gcc-f-bottom {{ border-top:1px solid rgba(255,255,255,.14); margin-top:28px; padding-top:18px;
  display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; font-size:.9rem; }}
.st-key-gcc-footer a {{ color:#fff !important; }}

/* ---------- menu links: page links styled like the design */
.st-key-gcc-links [data-testid="stPageLink-NavLink"] {{ padding:6px 12px !important; border-radius:8px; }}
.st-key-gcc-links [data-testid="stPageLink-NavLink"][aria-current="page"] {{ background:{SOFT} !important; }}
.st-key-gcc-links [data-testid="stPageLink-NavLink"][aria-current="page"] p {{ color:{NAVY} !important; font-weight:700 !important; }}
.st-key-gcc-area [data-testid="stPageLink-NavLink"] {{ border:1px solid #B9C0D4; border-radius:10px; padding:6px 12px; }}
.st-key-gcc-area [data-testid="stPageLink-NavLink"] p {{ color:{INK} !important; font-weight:500 !important; }}
.st-key-gcc-footer [data-testid="stPageLink-NavLink"] {{ padding:2px 0 !important; background:transparent !important; }}
.st-key-gcc-footer [data-testid="stPageLink-NavLink"] p {{ color:{ON_NAVY} !important; font-weight:400 !important; font-size:1rem; }}
.st-key-gcc-footer [data-testid="stPageLink-NavLink"]:hover p {{ color:#fff !important; text-decoration:underline; }}
[class*="st-key-pcrow_"] [data-testid="stNumberInput"] {{ min-width:0; }}

/* ---------- tablets */
@media (max-width: 900px) {{
  .gcc-hero-grid {{ grid-template-columns:1fr; }}
  .gcc-hero-card {{ max-width:460px; }}
}}

/* ---------- phones */
@media (max-width: 640px) {{
  /* no zoom-in on iPhone when tapping a field (needs 16px text) */
  .stApp input, .stApp textarea, .stApp [data-baseweb="select"] * {{ font-size:16px !important; }}

  /* top bar + header */
  .gcc-topbar {{ font-size:.8rem; }}
  .gcc-topbar-in {{ padding-top:6px; padding-bottom:6px; gap:6px; }}
  .gcc-tb-msg .extra {{ display:none; }}
  .gcc-pill {{ padding:3px 10px; font-size:.78rem; }}
  .st-key-gcc-nav {{ position:static; padding-top:8px !important; }}
  .gcc-brand {{ gap:10px; }}
  .gcc-brand img {{ width:42px; height:42px; border-radius:11px; }}
  .gcc-title {{ font-size:1.12rem; }}
  .gcc-badge {{ font-size:.6rem; padding:2px 5px; }}
  .gcc-tag {{ font-size:.82rem; }}
  .st-key-gcc-nav-top {{ gap:6px !important; }}
  /* menu: all five links visible, wrapping onto two short rows */
  .st-key-gcc-links {{ flex-wrap:wrap !important; gap:2px 2px !important; margin-left:-6px; margin-top:6px; }}
  .st-key-gcc-links [data-testid="stPageLink-NavLink"] {{ padding:5px 9px !important; }}
  .st-key-gcc-links [data-testid="stPageLink-NavLink"] p {{ font-size:.92rem !important; }}

  /* basket: a bar fixed to the bottom of the screen, always one tap away */
  .st-key-gcc-cart {{ position:fixed !important; left:12px; right:12px; bottom:12px; z-index:1000;
    width:calc(100% - 24px) !important; max-width:none !important; }}
  .st-key-gcc-cart [data-testid="stElementContainer"], .st-key-gcc-cart [data-testid="stPageLink"],
  .st-key-gcc-cart [data-testid="stPageLink"] > div, .st-key-gcc-cart [data-testid="stPageLink-NavLink"] {{
    width:100% !important; flex:1 1 100% !important; max-width:none !important; }}
  .st-key-gcc-cart [data-testid="stPageLink-NavLink"] {{ justify-content:center; padding:13px 16px !important;
    border-radius:14px; box-shadow:0 8px 24px rgba(0,8,77,.35); }}
  .st-key-gcc-cart [data-testid="stPageLink-NavLink"] p {{ font-size:1.02rem !important; }}
  .st-key-gcc-footer {{ padding-bottom:96px !important; }}
  .st-key-gcc-page {{ padding-top:20px !important; padding-bottom:36px !important; }}

  /* hero: shorter, no big logo card, facts in a 2 x 2 grid, buttons full width */
  .gcc-hero {{ padding-top:24px; padding-bottom:28px; }}
  .gcc-hero-card {{ display:none; }}
  .gcc-chips {{ font-size:.85rem; gap:6px; }}
  .gcc-chip {{ padding:2px 10px; }}
  .gcc-hero h1 {{ font-size:2.05rem !important; margin:14px 0 10px !important; }}
  .gcc-hero p.lead {{ font-size:1rem; line-height:1.5; }}
  .gcc-cta {{ margin-top:18px; gap:8px; }}
  .gcc-cta .gcc-btn {{ flex:1 1 0; justify-content:center; padding:11px 10px; font-size:.9rem; white-space:nowrap; }}
  .gcc-facts {{ display:grid; grid-template-columns:1fr 1fr; gap:12px 16px; margin-top:20px; padding-top:16px; }}
  .gcc-fact b {{ font-size:1.02rem; }} .gcc-fact span {{ font-size:.8rem; }}

  /* section titles */
  .gcc-h2 {{ font-size:1.45rem; }}
  .gcc-sub {{ font-size:.95rem; }}

  /* product grid: 2 cards per row instead of 1 */
  [class*="st-key-gcc-grid"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]) {{
    flex-wrap:wrap !important; gap:10px !important; margin-bottom:10px; }}
  [class*="st-key-gcc-grid"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]) > [data-testid="stColumn"] {{
    width:calc(50% - 5px) !important; flex:0 0 calc(50% - 5px) !important; min-width:0 !important; }}
  [class*="st-key-pc_"] {{ padding:8px !important; border-radius:14px !important; }}
  .gcc-ph {{ max-height:96px; font-size:2.2rem; border-radius:10px; }}
  [class*="st-key-pc_"] div[data-testid="stImage"] img {{ max-height:110px; }}
  .gcc-name {{ font-size:.9rem; min-height:2.5em; line-height:1.22; }}
  .gcc-urdu {{ font-size:.82rem; }}
  .gcc-unit {{ font-size:.75rem; }}
  .gcc-price {{ font-size:1rem; }}
  .gcc-mrp {{ font-size:.75rem; margin-left:4px; }}
  .gcc-save {{ font-size:.7rem; padding:1px 6px; }}
  /* on a phone the card is too narrow for a quantity box: "Add" adds one, change it in the basket */
  [class*="st-key-pcrow_"] [data-testid="stNumberInput"] {{ display:none !important; }}
  [class*="st-key-pc_"] [data-testid="stPopover"] button, [class*="st-key-pc_"] [data-testid="stPopoverButton"] {{
    min-height:32px !important; padding:2px 8px !important; }}
  [class*="st-key-pc_"] [data-testid="stCaptionContainer"] p {{ font-size:.75rem !important; }}

  /* delivery rates: compact two-line rows */
  .gcc-rates-row {{ grid-template-columns:auto 1fr; column-gap:10px; row-gap:2px; padding:8px 10px; }}
  .gcc-rates-row .fr {{ grid-column:1 / -1; }}
  .gcc-rates-row .nm {{ grid-column:1 / -1; font-size:.95rem; }}
  .gcc-rates-row .zn, .gcc-rates-row .rt small {{ display:none; }}
  .gcc-rates-row .tm, .gcc-rates-row .rt b, .gcc-rates-row .fr {{ font-size:.8rem; white-space:nowrap; }}
  [class*="st-key-rate_"] {{ flex-wrap:nowrap !important; padding:2px 8px 2px 0 !important; }}
  [class*="st-key-rate_"] [data-testid="stBaseButton-secondary"] {{ padding:4px 10px !important; min-height:34px; font-size:.85rem; }}

  /* cards on store / wholesale pages */
  [class*="st-key-info_"] {{ padding:16px !important; border-radius:16px !important; }}
  .gcc-card-h {{ font-size:1.12rem; }}

  /* basket lines + order status: keep on one row */
  [class*="st-key-bline_"] {{ flex-wrap:nowrap !important; gap:8px !important; }}
  .st-key-track_steps {{ flex-wrap:nowrap !important; gap:4px !important; }}
  .st-key-track_steps p {{ font-size:.78rem !important; text-align:center; }}
}}
div[data-testid="stImage"] img {{ border-radius:12px; aspect-ratio:4/3; object-fit:contain; background:#fff; }}
</style>
"""


def apply_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- top bar
def topbar(s: dict, sectors) -> None:
    zs = zones(sectors)
    free = zs[0]["free_over"] if zs else 0
    free_txt = (f'<span class="free extra">· Free delivery over {ui.rs(free)} in {e(zs[0]["zone"])}</span>'
                if free else "")
    wa = digits(s.get("store_whatsapp", ""))
    st.html(f"""
<div class="gcc-topbar"><div class="gcc-wrap gcc-topbar-in">
  <div class="gcc-tb-msg">{icon('truck', 18, YELLOW)}<span><b>Express delivery:</b> <b>{e(s.get('local_eta',''))}</b> in G-10
    <span class="extra">· <b>{e(s.get('other_eta',''))}</b> other sectors</span> {free_txt}</span></div>
  <div class="gcc-pills">
    <a class="gcc-pill gcc-mono" href="tel:{digits(s.get('store_landline',''))}">{icon('phone', 14, '#FFFFFF')}{e(s.get('store_landline',''))}</a>
    <a class="gcc-pill wa gcc-mono" href="https://wa.me/{wa}" target="_blank" rel="noopener">{icon('chat', 14, '#FFFFFF')}{e(s.get('store_helpline',''))}</a>
  </div>
</div></div>""")


# ---------------------------------------------------------------- header
def _brand_html(s: dict) -> str:
    return f"""
<div class="gcc-brand">
  <img src="data:image/png;base64,{logo_icon()}" alt="{e(s['store_name'])} logo">
  <div><div class="gcc-brand-line"><span class="gcc-title">{e(s['store_name'])}</span><span class="gcc-badge">G-10 MARKAZ</span></div>
  <div class="gcc-tag gcc-serif">{e(s['tagline'])}</div></div>
</div>"""


def _goto_category(cat: str) -> None:
    st.session_state["cat"] = cat
    st.session_state["deals_only"] = False
    st.session_state["search"] = ""
    st.session_state["_goto"] = "shop.py"


def navbar(s: dict, products, sectors) -> None:
    lines, subtotal, _ = ui.basket_lines(products)
    count = sum(l["qty"] for l in lines)
    with st.container(key="gcc-nav", gap=None):
        with st.container(key="gcc-nav-top", horizontal=True, horizontal_alignment="distribute",
                          vertical_alignment="center", gap="medium"):
            st.html(_brand_html(s), width="content")
            with st.container(key="gcc-actions", horizontal=True, vertical_alignment="center", gap="small",
                              width="content"):
                area = ui.current_sector(sectors)
                if area is not None:
                    with st.container(key="gcc-area", width="content"):
                        st.page_link("rates.py", label=area["name"].split(" (")[0], icon="📍",
                                     help="Your delivery area. Click to change it.")
                with st.container(key="gcc-cart", width="content"):
                    st.page_link("checkout.py", label=f"Basket ({count}) · {ui.rs(subtotal)}", icon="🛒")
        with st.container(key="gcc-links", horizontal=True, vertical_alignment="center", gap="small"):
            st.page_link("shop.py", label="Groceries")
            st.page_link("wholesale.py", label="Wholesale Deals")
            st.page_link("rates.py", label="Delivery Rates")
            st.page_link("track.py", label="Track Order")
            st.page_link("store.py", label="Store Info")


def _pick_area(sid: str, name: str) -> None:
    st.session_state["sector_id"] = sid
    st.session_state["co_area"] = sid
    st.toast(f"Delivery area set to {name}. You'll confirm your address at checkout.", icon="📍")


def delivery_rates(s: dict, sectors) -> None:
    """Sector-wise delivery table with a 'Deliver here' button per row (shop page)."""
    section_title("Sector-wise delivery", "Delivery rates across Islamabad",
                  "Pick your area to see your delivery charge at checkout. Your total bill is shown once you "
                  "enter your address. Not on the list? You can still order and the store adds the charge.",
                  anchor="delivery-rates")
    chosen = st.session_state.get("sector_id")
    with st.container(key="gcc-rates", gap=None):
        st.html(f"""<div class="gcc-rates-row gcc-rates-head"><span>Sector / area</span><span>Zone</span>
<span>Est. delivery time</span><span>Delivery rate</span><span>Free delivery</span><span></span></div>""")
        for _, r in sectors.iterrows():
            sel = r.id == chosen
            with st.container(key=f"rate_{r.id}", horizontal=True, vertical_alignment="center", gap=None):
                note = "Fixed local rate" if r.fee and "local" in (r.zone or "").lower() else (
                    "Subject to distance" if r.fee else "")
                st.html(f"""<div class="gcc-rates-row{' sel' if sel else ''}">
<span class="nm">{icon('pin', 16, NAVY if sel else '#64748B')}{e(r['name'])}{'<em>Selected</em>' if sel else ''}</span>
<span class="zn">{e(r.zone)}</span><span class="gcc-mono tm">{e(r.eta)}</span>
<span class="rt"><b class="gcc-mono">{ui.fee_text(r.fee)}</b><small>{note}</small></span>
<span class="gcc-mono fr">{'Over ' + ui.rs(r.free_over) if r.free_over else '—'}</span></div>""", width="stretch")
                if sel:
                    st.html('<span class="gcc-rate-sel">✓ Your area</span>', width="content")
                else:
                    st.button("Deliver here", key=f"pick_{r.id}", on_click=_pick_area, args=(r.id, r["name"]))
    if chosen:
        st.page_link("checkout.py", label="Continue to basket & checkout", icon="🛒")
    zs = zones(sectors)
    if zs:
        parts = " · ".join(f"{e(z['zone'])}: {ui.fee_text(z['fee'])}" for z in zs)
        frees = sorted({z["free_over"] for z in zs if z["free_over"]})
        free_txt = " · Free delivery " + " / ".join(f"over {ui.rs(f)}" for f in frees) if frees else ""
        st.html(f'<p class="gcc-sub" style="margin-top:10px;font-size:.92rem">{parts}{free_txt}.</p>')


# ---------------------------------------------------------------- hero (shop page)
def hero(s: dict, sectors) -> None:
    zs = zones(sectors)
    wa = digits(s.get("store_whatsapp", ""))
    hello = urllib.parse.quote("Assalam o Alaikum, I'd like to place a grocery order.")
    free = zs[0]["free_over"] if zs else 0
    hours = s.get("store_timings", "").split("(")[0].strip()
    st.html(f"""
<section class="gcc-hero"><div class="gcc-wrap gcc-hero-grid">
  <div>
    <div class="gcc-chips"><span class="gcc-chip">G-10 Markaz</span><span class="gcc-dot">·</span>
      <span class="y">Islamabad</span><span class="gcc-dot">·</span><span class="w">{e(hours)}</span></div>
    <h1>Wholesale grocery rates in G-10 &amp; Islamabad.</h1>
    <p class="lead">{e(s['store_name'])} G-10 Markaz brings fresh flour, premium basmati rice, cooking oils, ghee,
      tea, spices and household essentials straight to your home, with express delivery and bulk wholesale savings.</p>
    <div class="gcc-cta">
      <a class="gcc-btn light" href="#catalog">{icon('search', 18, NAVY)}Browse groceries</a>
      <a class="gcc-btn wa" href="https://wa.me/{wa}?text={hello}" target="_blank" rel="noopener">{icon('chat', 18, '#FFFFFF')}Order on WhatsApp</a>
    </div>
    <div class="gcc-facts">
      <div class="gcc-fact"><b>{e(s.get('local_eta',''))}</b><span>Delivery in G-10</span></div>
      <div class="gcc-fact"><b>{e(s.get('other_eta',''))}</b><span>Other Islamabad sectors</span></div>
      <div class="gcc-fact"><b>Cash on delivery</b><span>Pay at your door</span></div>
      {f'<div class="gcc-fact"><b>Free over {ui.rs(free)}</b><span>Delivery in {e(zs[0]["zone"])}</span></div>' if free else ''}
    </div>
  </div>
  <div class="gcc-hero-card">
    <img src="data:image/png;base64,{logo_full()}" alt="{e(s['tagline'])}: shopping cart logo">
    <div class="row"><span>{icon('box', 18, ON_NAVY)}Fresh daily stock</span><span>{icon('cash', 18, ON_NAVY)}Wholesale prices</span></div>
  </div>
</div></section>""")


# ---------------------------------------------------------------- store info page
def store_page(s: dict) -> None:
    section_title("Visit or order", f"{s['store_name']} G-10 Markaz Islamabad",
                  f"Conveniently located in the commercial heart of G-10 Markaz. Walk into our aisles or have groceries "
                  f"delivered in <b>{e(s.get('local_eta',''))} in G-10</b> or "
                  f"<b>{e(s.get('other_eta',''))} across Islamabad</b>.")
    c1, c2 = st.columns([1.2, 1], gap="medium")
    with c1, st.container(key="info_store"):
        st.html(f"""
<div class="gcc-card-h">{icon('store', 22)}G-10 Markaz store front</div>
<div class="gcc-li">{icon('pin')}<div><b>Address</b><span>{e(s['store_address'])}</span></div></div>
{f'<div class="gcc-li">{icon("pin")}<div><b>Landmark</b><span>{e(s["store_landmark"])}</span></div></div>' if s.get('store_landmark') else ''}
<div class="gcc-li">{icon('clock')}<div><b>Store &amp; delivery hours</b><span>{e(s['store_timings'])}</span></div></div>
<div class="gcc-li">{icon('phone')}<div><b>Shop landline</b><a class="gcc-mono" href="tel:{digits(s.get('store_landline',''))}">{e(s.get('store_landline',''))}</a></div></div>
<div class="gcc-li">{icon('chat', 18, WA)}<div><b>WhatsApp helpline</b><a class="wa gcc-mono" href="https://wa.me/{digits(s.get('store_whatsapp',''))}" target="_blank" rel="noopener">{e(s.get('store_helpline',''))}</a></div></div>
<div class="gcc-li">{icon('mail')}<div><b>Email</b><a href="mailto:{e(s.get('store_email',''))}" style="font-weight:500">{e(s.get('store_email',''))}</a></div></div>""")
        if s.get("map_url"):
            st.link_button("📍 Open in Google Maps", s["map_url"], width="stretch", type="primary")
    with c2, st.container(key="info_how"):
        st.html(f"""
<div class="gcc-card-h">{icon('truck', 22)}How ordering works</div>
<div class="gcc-li">{icon('search')}<div><b>1. Pick your groceries</b><span>Wholesale cash &amp; carry prices, updated live.</span></div></div>
<div class="gcc-li">{icon('pin')}<div><b>2. Add your area and address</b><span>Your delivery charge and total bill appear at checkout.</span></div></div>
<div class="gcc-li">{icon('chat', 18, WA)}<div><b>3. Send the order on WhatsApp</b><span>We confirm by phone before dispatch.</span></div></div>
<div class="gcc-li">{icon('cash')}<div><b>4. Pay cash on delivery</b><span>{e(s.get('local_eta',''))} in G-10, {e(s.get('other_eta',''))} elsewhere.</span></div></div>""")
        st.page_link("shop.py", label="Start shopping", icon="🛍️")
        st.page_link("rates.py", label="See delivery rates", icon="🚚")


# ---------------------------------------------------------------- wholesale / bulk request (wholesale page)
def bulk_request(s: dict) -> None:
    with st.container(key="info_bulk"):
        st.html(f"""<div class="gcc-card-h">{icon('box', 22)}Wholesale &amp; office rations</div>
<p class="gcc-sub">Special cash &amp; carry pricing for schools, hostels, restaurants, offices and monthly household
cartons. Send us your list and we'll reply on WhatsApp with a quote.</p>""")
        c1, c2 = st.columns(2)
        name = c1.text_input("Your name / institution", key="bulk_name")
        phone = c2.text_input("WhatsApp number", placeholder="03XX-XXXXXXX", key="bulk_phone")
        items = st.text_area("Items needed", placeholder="e.g. 5× Dalda cartons, 10× 10 kg atta bags, sugar bags",
                             key="bulk_items", height=110)
        msg = (f"Assalam o Alaikum, I'd like bulk cash & carry pricing.\nName: {name}\nWhatsApp: {phone}\n"
               f"Items needed:\n{items}")
        st.link_button("Request bulk pricing on WhatsApp", ui.wa_link(s["store_whatsapp"], msg), type="primary",
                       width="stretch", disabled=not (name.strip() and items.strip()))
        if not (name.strip() and items.strip()):
            st.caption("Fill in your name and the items to send the request.")


# ---------------------------------------------------------------- footer (every customer page)
def footer(s: dict, products, sectors) -> None:
    cats = [c for c in products.category.dropna().unique().tolist() if c][:7] if not products.empty else []
    zs = zones(sectors)
    with st.container(key="gcc-footer"):
        c1, c2, c3, c4 = st.columns([1.25, 1, 1, 1.25], gap="large")
        with c1:
            st.html(f"""
<div class="gcc-f-brand"><img src="data:image/png;base64,{logo_icon()}" alt="">
  <div><div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap"><span class="gcc-f-title">{e(s['store_name'])}</span><span class="gcc-badge">G-10 MARKAZ</span></div>
  <div class="gcc-f-tag gcc-serif">{e(s['tagline'])}</div></div></div>
<p style="margin:16px 0 10px;line-height:1.6">Wholesale pricing on pantry essentials, basmati rice, cooking oils, dairy
and household goods, delivered across Islamabad.</p>
<div class="gcc-y" style="text-transform:uppercase;font-size:.92rem">{e(s['store_timings'])}</div>""")
        with c2:
            st.html('<div class="gcc-f-h">GROCERY CATALOG</div>')
            for i, c in enumerate(cats):
                st.button(c, type="tertiary", key=f"f_cat_{i}", on_click=_goto_category, args=(c,))
            st.page_link("wholesale.py", label="Wholesale deals")
        with c3:
            rows = "".join(
                f'<div class="gcc-f-line"><span class="{"gcc-y" if i == 0 else ""}"><b>{e(z["zone"])}:</b></span> '
                f'{ui.fee_text(z["fee"])} · {e(z["eta"])}'
                f'{"<br><small>Free over " + ui.rs(z["free_over"]) + "</small>" if z["free_over"] else ""}</div>'
                for i, z in enumerate(zs))
            st.html(f"""<div class="gcc-f-h">HOME DELIVERY</div>{rows}
<div class="gcc-f-line" style="margin-top:10px">Area not listed? Order anyway and the store adds the charge.</div>
<div class="gcc-f-line"><span class="gcc-y">Cash on delivery</span> across Islamabad</div>""")
            st.page_link("rates.py", label="View all sectors & fees")
        with c4:
            st.html(f"""<div class="gcc-f-h">HELPLINE &amp; CONTACTS</div>
<div class="gcc-f-line">{e(s['store_address'])}</div>
{f'<div class="gcc-f-line gcc-y" style="font-size:.92rem">Landmark: {e(s["store_landmark"])}</div>' if s.get('store_landmark') else ''}
<a class="gcc-f-card" href="tel:{digits(s.get('store_landline',''))}">{icon('phone', 20, '#FFFFFF')}<div><small>Landline</small><b class="gcc-mono">{e(s.get('store_landline',''))}</b></div></a>
<a class="gcc-f-card wa" href="https://wa.me/{digits(s.get('store_whatsapp',''))}" target="_blank" rel="noopener">{icon('chat', 20, '#FFFFFF')}<div><small>WhatsApp</small><b class="gcc-mono">{e(s.get('store_helpline',''))}</b></div></a>
<div class="gcc-f-line" style="margin-top:12px">Email: <a class="gcc-mono" href="mailto:{e(s.get('store_email',''))}">{e(s.get('store_email',''))}</a></div>""")
        st.html(f"""<div class="gcc-f-bottom"><span>© {date.today().year} {e(s['store_name'])}, G-10 Markaz, Islamabad</span>
<span>Prices update live · Cash on delivery</span></div>""")


# ---------------------------------------------------------------- helpers used by pages
def section_title(eyebrow: str, title: str, sub: str = "", anchor: str = "") -> None:
    st.html(f"""<div {f'id="{anchor}"' if anchor else ''} style="scroll-margin-top:90px">
<div class="gcc-eyebrow">{e(eyebrow)}</div><div class="gcc-h2">{e(title)}</div>
{f'<p class="gcc-sub">{sub}</p>' if sub else ''}</div>""")


def scroll_if_requested(target: str) -> None:
    if st.session_state.get("scroll_to") == target:
        st.session_state.pop("scroll_to", None)
        st.html(f"""<script>setTimeout(function(){{var el=document.getElementById('{target}');
if(el){{el.scrollIntoView({{behavior:'smooth', block:'start'}});}}}}, 450);</script>""",
                unsafe_allow_javascript=True)
