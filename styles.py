"""
Bursaspor Kulübü — Atletik Performans Tasarım Sistemi v5.0
"""

import base64, os
import streamlit as st
from config import COLORS, PLAYER_PALETTE

# ── ASSETS YÖNETİMİ ────────────────────────────────────

def get_local_img(file_name):
    """Assets klasöründeki dosyayı güvenle okur ve Base64'e çevirir."""
    path = os.path.join("assets", file_name)
    if not os.path.exists(path):
        path = file_name
        
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            ext = file_name.split(".")[-1].lower().replace("jpg", "jpeg")
            return f"data:image/{ext};base64,{data}"
        except Exception:
            return ""
    return ""

# ── Bursaspor Renklerine Uygun Yedek SVG (Görsel Yüklenmezse) ───────────────
_CLUB_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 140">
  <defs><clipPath id="shield"><path d="M60 4 L112 26 L112 80 Q112 122 60 138 Q8 122 8 80 L8 26 Z"/></clipPath></defs>
  <path d="M60 4 L112 26 L112 80 Q112 122 60 138 Q8 122 8 80 L8 26 Z" fill="#007A33"/>
  <polygon points="8,95 112,52 112,80 60,138 8,115" fill="white" clip-path="url(#shield)"/>
  <circle cx="48" cy="48" r="18" fill="white"/>
  <circle cx="54" cy="43" r="14" fill="#007A33"/>
  <polygon points="74,32 76,39 83,39 77,44 79,51 74,46 69,51 71,44 65,39 72,39" fill="white"/>
  <circle cx="72" cy="100" r="22" fill="white" stroke="#007A33" stroke-width="1.5"/>
  <path d="M72,78 C80,85 82,95 72,122 C62,95 64,85 72,78Z" fill="#222" opacity="0.5"/>
  <line x1="50" y1="97" x2="94" y2="97" stroke="#222" stroke-width="1.2" opacity="0.4"/>
</svg>"""

_CLUB_LOGO_B64 = base64.b64encode(_CLUB_SVG.encode()).decode()

def get_logo_src():
    """Önce assets klasöründeki Bursaspor logoyu arar, bulamazsa SVG döner."""
    src = get_local_img("Bursaspor.png")
    return src if src else f"data:image/svg+xml;base64,{_CLUB_LOGO_B64}"

def inject_styles():
    """Tüm sayfaların arayüz, menü ve üst kurumsal renklerini ayarlar."""
    logo_main = get_logo_src()
    logo_header = get_local_img("yatay_bursaspor.jpg")
    stadium_bg = get_local_img("timsah_arena.jpg")
    
    try:
        st.logo("assets/Bursaspor.png")
    except Exception:
        pass
    
    st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800;900&family=DM+Mono:wght@400;500&family=Bebas+Neue&display=swap" rel="stylesheet">

<style>
/* ── RESET & BASE ─────────────────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; }}

html, body, [class*="css"], .stApp {{
    font-family: 'DM Sans', system-ui, sans-serif !important;
    color: {COLORS['GRAY_900']} !important;
    background: {COLORS['GRAY_50']} !important;
}}

.main .block-container {{
    padding-top: 1rem !important; 
    padding-bottom: 4rem !important;
    max-width: 1480px !important;
}}

/* ── EN ÜSTTEKİ KURUMSAL ŞERİT (GLOBAL HEADER - TİMSAH ARENA ARKA PLAN) ── */
.tff-global-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(90deg, rgba(255,255,255,1) 35%, rgba(255,255,255,0.92) 55%, rgba(255,255,255,0.1) 100%), url('{stadium_bg}') right center/cover no-repeat;
    padding: 15px 35px;
    border-bottom: 4px solid {COLORS['GREEN']};
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    margin: -1rem -2.5rem 2rem -2.5rem; 
    position: relative;
    z-index: 1000;
}}

.tgh-left {{ display: flex; align-items: center; gap: 20px; }}
.tgh-logo {{ height: 55px; width: auto; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1)); transition: transform 0.3s ease; }}
.tgh-logo:hover {{ transform: scale(1.05); }}
.tgh-titles {{ display: flex; flex-direction: column; }}
.tgh-main-title {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 30px;
    letter-spacing: 1.5px;
    color: {COLORS['GREEN']};
    line-height: 1;
}}
.tgh-sub-title {{
    font-size: 14px;
    font-weight: 800;
    color: {COLORS['GRAY_800']};
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 4px;
}}

/* ── ARKA PLAN FİLİGRANI (WATERMARK) ── */
.watermark-container {{
    position: fixed;
    top: 50%;
    left: 55%;
    transform: translate(-50%, -50%);
    z-index: -9999;
    opacity: 0.03;
    pointer-events: none;
}}
.watermark-container img {{
    width: 65vw;
    max-width: 800px;
    filter: grayscale(100%);
}}

/* ── SIDEBAR (TAM SİYAH TEMA VE YEŞİL VURGULAR) ──────────────────────── */
[data-testid="stSidebar"] {{
    background-color: #0D0D0D !important;
    border-right: 3px solid {COLORS['GREEN']} !important;
}}

section[data-testid="stSidebar"] > div {{ padding-top: 0 !important; }}

[data-testid="stSidebar"] p, 
[data-testid="stSidebar"] label, 
[data-testid="stSidebar"] span, 
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] div.stMarkdown p {{
    color: #F3F4F6 !important;
}}

[data-testid="stSidebarNav"] {{ padding: 12px 6px !important; }}

[data-testid="stSidebarNav"] a {{
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    color: #9CA3AF !important; 
    border-radius: 8px !important;
    margin: 4px 0 !important;
    padding: 10px 14px !important;
    transition: all 0.2s ease-in-out !important;
    border: 1px solid transparent !important;
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    text-transform: none !important;
    background-color: transparent !important;
    text-decoration: none !important;
}}

[data-testid="stSidebarNav"] a:hover {{
    background-color: rgba(0,122,51,0.15) !important;
    transform: translateX(4px) !important;
}}

[data-testid="stSidebarNav"] a:hover span {{
    color: #FFFFFF !important;
}}

[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background-color: {COLORS['GREEN']} !important;
    box-shadow: 0 4px 12px rgba(0,122,51,0.4) !important;
}}

[data-testid="stSidebarNav"] a[aria-current="page"] span {{
    color: #FFFFFF !important;
    font-weight: 800 !important;
}}

/* ── SIDEBAR İÇİ: VERİ YÜKLE KESİN ÇÖZÜM ── */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {{ background-color: transparent !important; }}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section {{
    background-color: #1F2937 !important;
    border: 1px dashed #4B5563 !important;
    border-radius: 10px !important;
    padding: 15px !important;
}}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section:hover {{
    border-color: {COLORS['GREEN']} !important;
    background-color: #374151 !important;
}}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section span,
[data-testid="stSidebar"] [data-testid="stFileUploader"] section small {{ color: #D1D5DB !important; }}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button {{
    background-color: #374151 !important;
    color: #FFFFFF !important;
    border: 1px solid #4B5563 !important;
    border-radius: 6px !important;
}}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {{
    background-color: {COLORS['GREEN']} !important;
    border-color: {COLORS['GREEN']} !important;
    color: #FFFFFF !important;
}}

/* ── SIDEBAR İÇİ: SİSTEM ÖZETİ ── */
[data-testid="stSidebar"] [data-testid="stMetric"] {{
    background-color: #1F2937 !important;
    border: 1px solid #374151 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
}}
[data-testid="stSidebar"] [data-testid="stMetricLabel"] p {{
    color: #9CA3AF !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}}
[data-testid="stSidebar"] [data-testid="stMetricValue"] div {{
    color: {COLORS['GREEN']} !important;
    font-size: 26px !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-weight: 400 !important;
}}

/* ── BUTTONS (Genel) ─────────────────────────────────────────────────────── */
.stButton > button {{
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 800 !important;
    font-size: 13px !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    background: {COLORS['GREEN']} !important;
    color: white !important;
    border: none !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 10px rgba(0,122,51,0.2) !important;
}}

.stButton > button:hover {{
    background: {COLORS['BLACK']} !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(13,13,13,0.35) !important;
}}

/* ── FORM ELEMENTS (ANA GÖVDE İÇİN) ─────────────────────────────────────── */
.main [data-testid="stSelectbox"] label,
.main [data-testid="stRadio"] > label,
.main [data-testid="stMultiSelect"] > label,
.main [data-testid="stFileUploader"] > label,
.main [data-testid="stSlider"] > label {{
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 800 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    color: {COLORS['GRAY_700']} !important;
}}

.main div[data-baseweb="select"] > div {{
    border-radius: 8px !important;
    border-color: {COLORS['GRAY_300']} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    background: {COLORS['WHITE']} !important;
}}

.main div[data-baseweb="select"] > div:focus-within {{
    border-color: {COLORS['GREEN']} !important;
    box-shadow: 0 0 0 3px rgba(0,122,51,0.1) !important;
}}

/* ── METRICS (Ana Sayfa Kartları) ─────────────────────────────────────── */
.main [data-testid="stMetric"] {{
    background: {COLORS['WHITE']} !important;
    border: 1px solid {COLORS['GRAY_300']} !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
    transition: all 0.3s ease !important;
}}

.main [data-testid="stMetric"]:hover {{
    border-color: {COLORS['GREEN']} !important;
    box-shadow: 0 8px 20px rgba(0,122,51,0.08) !important;
    transform: translateY(-3px) !important;
}}

.main [data-testid="stMetricLabel"] p {{
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    color: {COLORS['GRAY_500']} !important;
}}

.main [data-testid="stMetricValue"] {{
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 34px !important;
    font-weight: 400 !important;
    color: {COLORS['GRAY_900']} !important;
    letter-spacing: 1px !important;
}}

/* ── DATAFRAME ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border-radius: 10px !important;
    border: 1px solid {COLORS['GRAY_300']} !important;
    overflow: hidden !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
}}
thead tr th {{
    text-transform: none !important;
    font-weight: 700 !important;
    color: {COLORS['GRAY_900']} !important;
}}

/* ── TABS ─────────────────────────────────────────────────────────────────── */
.stTabs [data-testid="stTab"] p {{
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 800 !important;
    font-size: 13px !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}}

.stTabs [data-testid="stTab"][aria-selected="true"] {{
    color: {COLORS['GREEN']} !important;
}}

.stTabs [role="tablist"] {{
    border-bottom: 2px solid {COLORS['GRAY_300']} !important;
    gap: 4px !important;
}}

hr {{
    border: none !important;
    border-top: 1px solid {COLORS['GRAY_300']} !important;
    margin: 1.5rem 0 !important;
}}

/* ── TOOLTIP ─────────────── */
.tff-tooltip {{
    position: relative;
    display: inline-flex;
    align-items: center;
    cursor: help;
    color: {COLORS['GREEN']};
    margin-left: 6px;
    font-size: 16px;
}}
.tff-tooltip .tooltip-text {{
    visibility: hidden;
    width: max-content;
    max-width: 280px;
    background-color: {COLORS['GRAY_900']};
    color: #fff;
    text-align: center;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    position: absolute;
    z-index: 9999;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    opacity: 0;
    transition: opacity 0.3s, transform 0.3s;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    line-height: 1.4;
}}
.tff-tooltip:hover .tooltip-text {{
    visibility: visible;
    opacity: 1;
    transform: translateX(-50%) translateY(-4px);
}}

/* ── PAGE HEADER (KART TASARIMI) ────────────────────────────────────────── */
.tff-header {{
    background: linear-gradient(135deg, {COLORS['BLACK']} 0%, {COLORS['GRAY_800']} 100%);
    border-radius: 0 0 20px 20px;
    padding: 28px 36px 24px;
    margin: 0 -2.5rem 28px -2.5rem;
    display: flex;
    align-items: center;
    gap: 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}}

.tff-header::before {{
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 6px;
    background: {COLORS['GREEN']};
}}

.tff-header::after {{
    content: '';
    position: absolute;
    right: -60px; top: -60px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(0,122,51,0.15) 0%, transparent 65%);
    border-radius: 50%;
}}

.tff-header .h-icon {{
    width: 65px; height: 65px;
    background: rgba(255,255,255,0.1);
    border: 1.5px solid rgba(0,122,51,0.4);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 32px;
    flex-shrink: 0;
    z-index: 1;
    overflow: hidden;
}}

.tff-header .h-icon img {{ 
    width: 100%; 
    height: 100%; 
    object-fit: contain; 
    padding: 8px;
}}

.tff-header .h-body {{ z-index: 1; }}

.tff-header .h-title {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 34px;
    letter-spacing: 2px;
    color: white;
    line-height: 1;
    margin-bottom: 4px;
}}

.tff-header .h-sub {{
    font-family: 'DM Sans', sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: {COLORS['GRAY_300']};
    letter-spacing: 0.5px;
}}

/* ── SECTION TITLE ──────────────────────────────────────────────────────── */
.tff-section {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 30px 0 16px 0;
}}

.tff-section .s-pill {{
    background: {COLORS['GREEN']};
    border-radius: 3px;
    width: 5px; height: 22px;
    flex-shrink: 0;
}}

.tff-section .s-text {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 22px;
    letter-spacing: 2px;
    color: {COLORS['GRAY_900']};
}}

/* ── INFO BOX ───────────────────────────────────────────────────────────── */
.tff-info {{
    background: rgba(0,122,51,0.04);
    border: 1px solid rgba(0,122,51,0.15);
    border-left: 4px solid {COLORS['GREEN']};
    border-radius: 8px;
    padding: 12px 18px;
    font-size: 14px;
    font-weight: 500;
    color: {COLORS['GRAY_800']};
    margin: 10px 0;
    display: flex;
    align-items: center;
    gap: 10px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}}

/* ── STAT CARDS ─────────────────────────────────────────────────────────── */
.tff-stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 12px;
    margin: 16px 0;
}}

.tff-stat-card {{
    background: white;
    border: 1px solid {COLORS['GRAY_300']};
    border-radius: 12px;
    padding: 16px 18px;
    transition: all 0.3s ease;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}}

.tff-stat-card:hover {{
    border-color: {COLORS['GREEN']};
    box-shadow: 0 8px 16px rgba(0,122,51,0.08);
    transform: translateY(-2px);
}}

.tff-stat-card .sc-val {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 28px;
    letter-spacing: 1.5px;
    color: {COLORS['GREEN']};
    line-height: 1;
}}

.tff-stat-card .sc-label {{
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: {COLORS['GRAY_600']};
    margin-top: 8px;
}}

.tff-stat-card .sc-sub {{
    font-size: 11px;
    font-weight: 500;
    color: {COLORS['GRAY_400']};
    margin-top: 4px;
}}

/* ── PLAYER CARD ─────────────────────────────────────────────────────────── */
.tff-player-hero {{
    background: linear-gradient(135deg, {COLORS['GRAY_900']} 0%, {COLORS['GRAY_800']} 100%);
    border-radius: 16px;
    padding: 30px 36px;
    margin-bottom: 25px;
    border-left: 6px solid {COLORS['GREEN']};
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 25px rgba(0,0,0,0.15);
}}

.tff-player-hero::after {{
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 250px; height: 250px;
    background: radial-gradient(circle, rgba(0,122,51,0.15) 0%, transparent 65%);
    border-radius: 50%;
}}

.tff-player-hero .ph-name {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 44px;
    letter-spacing: 3px;
    color: white;
    line-height: 1;
    text-transform: uppercase;
}}

.tff-player-hero .ph-sub {{
    font-size: 13px;
    color: {COLORS['GRAY_300']};
    margin: 8px 0 28px;
    font-weight: 500;
    letter-spacing: 0.5px;
}}

.tff-player-chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    position: relative;
    z-index: 1;
}}

.tff-chip {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 12px 18px;
    display: flex; flex-direction: column; align-items: center;
    min-width: 80px;
    transition: all 0.2s ease;
}}

.tff-chip:hover {{
    background: rgba(0,122,51,0.15);
    border-color: rgba(0,122,51,0.5);
    transform: translateY(-2px);
}}

.tff-chip .c-val {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 24px;
    letter-spacing: 1px;
    color: {COLORS['GREEN']};
    line-height: 1;
}}

.tff-chip .c-lbl {{
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: {COLORS['GRAY_300']};
    margin-top: 6px;
    text-align: center;
}}

/* ── SIDEBAR BRAND ───────────────────────────────────────────────────────── */
.sb-brand {{
    padding: 20px 10px;
    border-bottom: 2px solid {COLORS['GREEN']};
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 10px;
}}

.sb-brand img {{
    width: 85px;
    filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.3));
    margin-bottom: 5px;
    transition: transform 0.3s;
}}
.sb-brand img:hover {{
    transform: scale(1.05);
}}

.sb-brand .sb-title {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 26px;
    letter-spacing: 1.5px;
    color: white; 
    line-height: 1.1;
}}

.sb-brand .sb-sub {{
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    color: {COLORS['GREEN']};
    letter-spacing: 1.5px;
    margin-top: 4px;
}}

/* ── RANK BADGES ─────────────────────────────────────────────────────────── */
.rk-1,.rk-2,.rk-3,.rk-n {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px; border-radius: 50%;
    font-family: 'DM Mono', monospace; font-weight: 700; font-size: 12px;
}}
.rk-1 {{ background: #FFD700; color: #5C4300; box-shadow: 0 2px 5px rgba(255,215,0,0.3); }}
.rk-2 {{ background: #C0C0C0; color: #333; box-shadow: 0 2px 5px rgba(192,192,192,0.3); }}
.rk-3 {{ background: #CD7F32; color: white; box-shadow: 0 2px 5px rgba(205,127,50,0.3); }}
.rk-n {{ background: {COLORS['GRAY_100']}; color: {COLORS['GRAY_700']}; }}

/* ── BADGES ──────────────────────────────────────────────────────────────── */
.badge-match {{
    display: inline-block;
    background: {COLORS['BLACK']};
    color: white;
    font-size: 10px; font-weight: 800; letter-spacing: 1px;
    text-transform: uppercase; padding: 4px 10px; border-radius: 4px;
}}

.badge-training {{
    display: inline-block;
    background: {COLORS['GREEN']};
    color: white;
    font-size: 10px; font-weight: 800; letter-spacing: 1px;
    text-transform: uppercase; padding: 4px 10px; border-radius: 4px;
}}

/* ── PERF LABELS ─────────────────────────────────────────────────────────── */
.perf-elite {{ display:inline-block;background:#ECFDF5;color:#059669;border:1px solid #A7F3D0;border-radius:20px;padding:3px 12px;font-size:11px;font-weight:800; }}
.perf-good  {{ display:inline-block;background:#EFF6FF;color:#2563EB;border:1px solid #BFDBFE;border-radius:20px;padding:3px 12px;font-size:11px;font-weight:800; }}
.perf-avg   {{ display:inline-block;background:{COLORS['GRAY_100']};color:{COLORS['GRAY_700']};border:1px solid {COLORS['GRAY_300']};border-radius:20px;padding:3px 12px;font-size:11px;font-weight:800; }}
.perf-low   {{ display:inline-block;background:#FEF2F2;color:#DC2626;border:1px solid #FECACA;border-radius:20px;padding:3px 12px;font-size:11px;font-weight:800; }}

/* ── FOOTER ──────────────────────────────────────────────────────────────── */
.tff-footer {{
    text-align: center;
    padding: 24px 0 8px;
    margin-top: 48px;
    border-top: 1px solid {COLORS['GRAY_300']};
}}

.tff-footer p {{
    font-size: 12px;
    font-weight: 500;
    color: {COLORS['GRAY_400']};
    margin: 2px 0;
    letter-spacing: 0.5px;
}}

/* ── DOWNLOAD BUTTON ─────────────────────────────────────────────────────── */
.stDownloadButton > button {{
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.8px !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    background: white !important;
    color: {COLORS['GRAY_800']} !important;
    border: 1.5px solid {COLORS['GRAY_300']} !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
    text-transform: uppercase !important;
    transition: all 0.2s ease !important;
}}

.stDownloadButton > button:hover {{
    border-color: {COLORS['GREEN']} !important;
    color: {COLORS['GREEN']} !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 10px rgba(0,122,51,0.08) !important;
}}

/* ── HIDE STREAMLIT DEFAULTS ─────────────────────────────────────────────── */
#MainMenu, footer {{ visibility: hidden; }}
header {{ background: transparent !important; }}
[data-testid="stDecoration"] {{ display: none; }}

</style>
""", unsafe_allow_html=True)
    
    # Global HTML Şeridi
    st.markdown(f"""
<div class="tff-global-header">
<div class="tgh-left">
<img src="{logo_header if logo_header else logo_main}" class="tgh-logo">
<div class="tgh-titles">
<div class="tgh-main-title">BURSASPOR SPORTİF PERFORMANS</div>
<div class="tgh-sub-title">A Takım ve Akademi Veri Merkezi</div>
</div>
</div>
</div>
<div class="watermark-container"><img src="{logo_main}"></div>
""", unsafe_allow_html=True)


# ── BİLEŞEN FONKSİYONLARI ──────────────

def page_header(icon_or_url: str, title: str, subtitle: str = ""):
    import streamlit as st
    if str(icon_or_url).startswith("http") or "data:image" in icon_or_url:
        icon_html = f'<img src="{icon_or_url}" style="width: 100%; height: 100%; object-fit: contain;">'
    else:
        icon_html = icon_or_url

    st.markdown(f"""
    <div class="tff-header">
        <div class="h-icon">{icon_html}</div>
        <div class="h-body">
            <div class="h-title" style="color:white;">{title.upper()}</div>
            <div class="h-sub" style="color:#D1D5DB;">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def section_title(text: str, icon: str = "", tooltip: str = ""):
    import streamlit as st
    label = f"{icon}&thinsp;&thinsp;{text}" if icon else text
    
    tooltip_html = f"""
    <div class="tff-tooltip">
        <span style="font-size:18px;">ℹ️</span>
        <span class="tooltip-text">{tooltip}</span>
    </div>
    """ if tooltip else ""
    
    st.markdown(f'''
    <div class="tff-section">
        <div class="s-pill"></div>
        <span class="s-text">{label}</span>
        {tooltip_html}
    </div>
    ''', unsafe_allow_html=True)

def info_box(html_text: str):
    import streamlit as st
    st.markdown(f'''
    <div class="tff-info">
        <span style="font-size:20px; color:{COLORS['GREEN']};">💡</span> 
        <div>{html_text}</div>
    </div>''', unsafe_allow_html=True)

def sidebar_brand():
    import streamlit as st
    logo = get_logo_src()
    st.markdown(f"""
    <div class="sb-brand">
        <img src="{logo}" alt="Bursaspor Logo">
        <div>
            <div class="sb-title">BURSASPOR</div>
            <div class="sb-sub">VERİ MERKEZİ</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def player_profile_card(name: str, age_group: str, stats: dict):
    import streamlit as st

    def chip(val, lbl):
        return f'<div class="tff-chip"><span class="c-val">{val}</span><span class="c-lbl">{lbl}</span></div>'

    # Futbol verilerine göre çipleri ayarladık ("Kamp" yerine "Hafta/Döngü")
    chips = (
        chip(int(stats.get('week_count', stats.get('camp_count', 0))), 'HAFTA')
      + chip(int(stats.get('session_count', 0)), 'SEANS')
      + chip(int(stats.get('match_count', 0)), 'MAÇ')
      + chip(f"{stats.get('avg_training_minutes', 0):.0f}'", 'ANT. DK')
      + chip(f"{stats.get('avg_match_minutes', 0):.0f}'", 'MAÇ DK')
      + chip(f"{stats.get('distance_per_90', 0):.0f}m", "MES/90'")
      + chip(f"{stats.get('max_speed', 0):.1f}", 'MAX KM/H')
    )

    st.markdown(f"""
    <div class="tff-player-hero">
        <div class="ph-name">{name}</div>
        <div class="ph-sub">{age_group} · Futbol · Atletik Performans Departmanı</div>
        <div class="tff-player-chips">{chips}</div>
    </div>
    """, unsafe_allow_html=True)

def tip_badge(tip: str) -> str:
    if "MATCH" in str(tip).upper() or "MAÇ" in str(tip).upper():
        return '<span class="badge-match">MAÇ</span>'
    return '<span class="badge-training">ANTRENMAN</span>'

def rank_badge_html(rank: int) -> str:
    if rank == 1: return '<span class="rk-1">1</span>'
    if rank == 2: return '<span class="rk-2">2</span>'
    if rank == 3: return '<span class="rk-3">3</span>'
    return f'<span class="rk-n">{rank}</span>'

def perf_label(value: float, team_avg: float) -> str:
    if not team_avg: return '<span class="perf-avg">—</span>'
    r = value / team_avg
    if r >= 1.15: return '<span class="perf-elite">▲ ELİT</span>'
    if r >= 1.05: return '<span class="perf-good">▲ İYİ</span>'
    if r >= 0.95: return '<span class="perf-avg">→ ORTA</span>'
    return '<span class="perf-low">▼ DÜŞÜK</span>'