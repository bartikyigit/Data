import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from config import AGE_GROUPS, METRICS, PRIMARY_METRICS, DEFAULT_MINUTES
from database import db_manager
from styles import inject_styles, page_header, section_title, COLORS
from utils import calculate_impact_score_engine, calculate_development_stats, render_export_buttons

# ── SAYFA KONFİGÜRASYONU VE GİRİŞ ──────────────────────────────────────────────
st.set_page_config(page_title="Impact Analizi | TFF", layout="wide")
inject_styles()

page_header("⚡", "IMPACT (ETKİ) ANALİZİ",
            "Tüm atletik değişkenlerin Z-Skoru ile hesaplanmış objektif günlük ve kamp performansı.")

# ── DİNAMİK METRİK İSİMLERİ (CONFIG'DEN ÇEKİLİR) ──────────────────────────────
# Açıklamalarda ve tablolarda kendi uydurduğumuz isimleri değil, config'deki orijinal isimleri kullanıyoruz.
d_dist_25 = METRICS.get('dist_25_plus', {}).get('display', '25+ Hız (m)').upper()
d_load = METRICS.get('player_load', {}).get('display', 'Player Load').upper()
d_smax = METRICS.get('smax_kmh', {}).get('display', 'Max Hız').upper()
d_tdist = METRICS.get('total_distance', {}).get('display', 'Toplam Mesafe').upper()

# ── MODEL METODOLOJİSİ (Ayrıntılı İstatistiksel Açıklama) ──────────────────────
with st.expander("📌 TFF İMPACT (ETKİ) MODELİ: İSTATİSTİKSEL METODOLOJİ VE HESAPLAMA MANTIĞI", expanded=False):
    st.markdown(f"""
    Bu modül, birbirinden farklı birimlere sahip (metre, adet, km/h, arbitrary unit) karmaşık atletik verileri tek bir potada eriterek, oyuncunun takıma göre "Fiziksel Etkisini" objektif olarak hesaplar. Hesaplama 5 temel adımdan oluşur:

    **Adım 1: Ekolojik Geçerlilik ve Normalizasyon (Intensity vs. Volume)**
    Saha içindeki adaletsizliği önlemek için ilk adım veriyi "Şiddete" dönüştürmektir. 90 dakika oynayan bir stoperin 10.000 metre koşması ile, 45 dakika oynayan bir kanat oyuncusunun 6.000 metre koşması ham veride kıyaslanamaz.
    Bu yüzden model, "Max Sürat (Peak)" verisi hariç tüm kümülatif verileri oyuncunun oynadığı dakikaya bölerek **Birim Dakika (Per Minute / pm)** verisine dönüştürür.
    * **Hesaplama:** `{d_tdist} / Oynanan Dakika`
    * **Sonuç:** Hacim (Volume), Şiddet'e (Intensity) dönüştürülerek herkes eşit süre oynamış gibi adil bir zemin yaratılır.

    **Adım 2: Z-Skoru ile Standardizasyon (Elmalarla Armutları Toplamak)**
    En büyük problem: Sürat (km/h) ile Mesafeyi (metre) nasıl toplayıp tek bir puan elde edeceğiz? İstatistik bilimi burada devreye girer. Tüm veriler **Z-Skoruna** (Standart Normal Dağılım) dönüştürülür.
    Z-Skoru, bir oyuncunun değerinin, o günkü takım ortalamasından kaç standart sapma ($\sigma$) uzakta olduğunu ölçer.
    * **Formül:** $$Z = \\frac{{X - \mu}}{{\sigma}}$$ 
    *(X: Oyuncu Değeri, $\mu$: Takım Ortalaması, $\sigma$: Standart Sapma)*
    * **Örnek:** Eğer oyuncunun Z-Skoru $+1.5$ ise, bu onun takım ortalamasının oldukça üzerinde (Elit bölgede) olduğunu kanıtlar. Artık tüm metrikler $+3$ ile $-3$ arasında standart bir formata gelmiştir ve toplanabilirler.

    **Adım 3: Futbolun Fiziksel Doğasına Göre Ağırlıklandırma (Weighting)**
    Modern futbolda her metrik aynı değere sahip değildir. "Jogging" (düşük tempolu koşu) ile maçı kazandıran "Sprint" eylemi eşit puanlanamaz. Bu yüzden elde edilen Z-Skorları, spor bilimi literatürüne uygun olarak şu ağırlıklarla çarpılır:
    * **%25 - {d_dist_25}:** Modern oyunun en belirleyici faktörü (Sprint).
    * **%20 - Patlayıcı Aksiyon:** Yüksek şiddetli ivmelenme ($>3 m/s^2$) ve yavaşlamaların ($<-3 m/s^2$) ortalaması. Kas hasarını ve çevikliği temsil eder.
    * **%20 - {d_load}:** İç ivmeölçerlerden gelen 3 eksenli stres verisi.
    * **%15 - {d_tdist}:** Genel motor kapasite.
    * **%10 - {d_smax}:** Oyuncunun ulaşabildiği en yüksek tavan sürat.
    * **%10 - Metabolik Güç:** AMP ve Metrage verilerinin harmanlandığı, enerji harcama kapasitesi.

    **Adım 4: Skor Ölçekleme (0-100 Scale)**
    Ağırlıklandırılmış Z-Skorlarının toplamı (genellikle $-2$ ile $+2$ arası çıkar), teknik heyetin ve antrenörlerin kolayca anlayabilmesi için **0 ile 100 arasında** bir puana (Impact Score) dönüştürülür.
    * **Hesaplama:** $$Impact\_Score = \min\\left(100, \max\\left(0, \\frac{{\\text{{Toplam\_Z}} + 2.5}}{{5}} \\times 100\\right)\\right)$$
    * **İstatistiksel Durum Etiketleri:** * $\geq 80$: **Elit (+1.5 SD)** -> İnanılmaz bir fiziksel performans.
        * $60 - 79$: **Ort. Üstü (+0.5 SD)** -> Takımı yukarı çeken performans.
        * $40 - 59$: **Ortalama Standardı** -> Takıma ayak uyduran performans.
        * $< 40$: **Gelişim Bölgesi** -> Bireysel yükleme gerektiren yetersiz performans.

    **Adım 5: Boylamsal Gelişim Analizi (Longitudinal Development)**
    "Geçmiş Kamplara Göre Gelişim" sekmesi, oyuncunun mevcut kamp verilerini, veritabanındaki **tüm geçmiş kamp ortalamaları** ile kıyaslar.
    * **Formül:** $$Gelişim\ \% = \\left( \\frac{{\\text{{Güncel Kamp Ort.}} - \\text{{Geçmiş Kamplar Ort.}}}}{{\\text{{Geçmiş Kamplar Ort.}}}} \\right) \\times 100$$
    Bu sayede antrenörler "Bu çocuk geçen kampa göre %15 daha fazla sprint üretiyor" yorumunu verilere dayanarak net bir şekilde yapabilir.
    """, unsafe_allow_html=True)

# ── VERİ FİLTRELEME VE ÇEKME KATI ─────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    age_group = st.selectbox("HEDEF YAŞ GRUBU", AGE_GROUPS, key="ia_age")

raw_age_data = db_manager.get_data_by_age_group(age_group)
if raw_age_data.empty:
    st.warning(f"{age_group} için veritabanında kayıtlı veri bulunamadı.")
    st.stop()

camps_df = db_manager.get_camps(age_group)
camp_options = {row['camp_name']: row['camp_id'] for _, row in camps_df.iterrows()}

with c2:
    if camp_options:
        sel_camp_label = st.selectbox("KAMP SEÇİMİ", list(camp_options.keys()), key="ia_camp")
        sel_camp_id = camp_options[sel_camp_label]
        
        # Seçilen kampın başlama tarihini bul (Tarihsel kronolojik filtreleme için)
        camp_dates = raw_age_data[raw_age_data['camp_id'] == sel_camp_id]['tarih']
        if not camp_dates.empty:
            sel_camp_start_date = pd.to_datetime(camp_dates.min())
        else:
            sel_camp_start_date = pd.Timestamp.now()
    else:
        st.warning(f"{age_group} için tanımlı bir kamp bulunamadı.")
        st.stop()

with c3:
    ses = radio_ses = st.radio("SEANS TİPİ", ["Tümü", "TRAINING", "MATCH"], horizontal=True, key="ia_ses")

# ── IMPACT ENGINE (HESAPLAMA MOTORU) ──────────────────────────────────────────
raw_camp_data = raw_age_data[raw_age_data['camp_id'] == sel_camp_id].copy()

if raw_camp_data.empty:
    st.warning("Seçilen kamp için veri kaydı bulunmuyor.")
    st.stop()

if ses != "Tümü":
    raw_camp_data = raw_camp_data[raw_camp_data['tip'].str.upper() == ses]

# utils.py içindeki yenilenmiş objektif Z-Score motoru çalıştırılıyor
camp_data = calculate_impact_score_engine(raw_camp_data)

if camp_data.empty:
    st.warning("Hesaplanabilir geçerli veri bulunamadı (dakikası 0 olan veya hatalı veriler sistem tarafından filtrelenmiştir).")
    st.stop()

st.divider()

# ── ANALİZ SEKMELERİ (TABS) ───────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 GÜNLÜK TAKIM SIRALAMASI",
    "📋 KAMP LİDERLERİ (TÜM KADRO)", 
    "📈 GEÇMİŞ KAMPLARA GÖRE GELİŞİM",
    "📉 KAMP İÇİ TREND"
])

# ── TAB 1: GÜNLÜK SIRALAMA (Anlık Form Durumu) ────────────────────────────────
with tab1:
    unique_dates = sorted(camp_data['tarih'].unique(), reverse=True)
    sel_date = st.selectbox("İNCELENECEK SEANS TARİHİ", unique_dates, format_func=lambda x: pd.to_datetime(x).strftime('%d.%m.%Y'), key="ia_daily_date")
    
    day_data = camp_data[camp_data['tarih'] == sel_date].sort_values('impact_score', ascending=False)
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        section_title("TAKIM SIRALAMASI TABLOSU", "📋")
        display_cols = ['player_name', 'impact_score', 'status_tag', 'dist_25_plus', 'player_load', 'smax_kmh']
        show_df = day_data[display_cols].copy()
        
        # Sütun isimlerini dinamik olarak config'den atıyoruz
        show_df.columns = ['OYUNCU', 'IMPACT SKOR', 'İSTATİSTİKSEL DURUM', d_dist_25, d_load, d_smax]
        show_df.index = np.arange(1, len(show_df) + 1)
        
        st.dataframe(show_df.style.background_gradient(cmap='Reds', subset=['IMPACT SKOR'], vmin=20, vmax=90), 
                     use_container_width=True, height=600)
        
        render_export_buttons(df=show_df.reset_index(drop=True), key_prefix="ia_daily", filename=f"Gunluk_Impact_{pd.to_datetime(sel_date).strftime('%d%m%Y')}")
                     
    with col_b:
        section_title("İMPACT SKOR DAĞILIMI", "📊")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=day_data['player_name'].str.upper(),
            x=day_data['impact_score'],
            orientation='h',
            marker=dict(
                color=day_data['impact_score'],
                colorscale='Reds',
                cmin=30, cmax=90,
                line=dict(color='rgba(0,0,0,0.1)', width=1)
            ),
            text=[f"{v:.1f}" for v in day_data['impact_score']],
            textposition='outside',
            textfont=dict(family="DM Sans", size=11, color=COLORS['GRAY_800'], weight="bold")
        ))
        fig.update_layout(
            template='plotly_white',
            height=max(600, len(day_data) * 25),
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(title="Etki Puanı / Impact Score (0-100)", gridcolor='#F3F4F6'),
            yaxis=dict(autorange="reversed", tickfont=dict(weight="bold", color=COLORS['GRAY_800']))
        )
        st.plotly_chart(fig, use_container_width=True)

# ── TAB 2: KAMP LİDERLERİ (Genel Değerlendirme) ──────────────────────────────
with tab2:
    section_title("KAMP GENEL ORTALAMASI VE LİDERLİK TABLOSU", "🏆")
    st.markdown("<p style='color: gray; font-size: 13px;'>Kamp boyunca tüm oyuncuların günlük Impact skorlarının ve dakikaya oranlanmış (m/min) değişkenlerinin genel aritmetik ortalamasıdır.</p>", unsafe_allow_html=True)
    
    camp_impact = camp_data.groupby('player_name').agg(
        avg_impact=('impact_score', 'mean'),
        avg_high_speed=('dist_25_plus_pm', 'mean'),
        avg_load=('player_load_pm', 'mean'),
        max_speed=('smax_kmh', 'max'),
        session_count=('tarih', 'count')
    ).reset_index().sort_values('avg_impact', ascending=False)
    
    camp_impact.index = np.arange(1, len(camp_impact) + 1)
    
    # Kolon isimleri dinamik çekiliyor
    camp_impact.columns = ['OYUNCU', 'KAMP ORT. İMPACT', f'ORT. {d_dist_25} (m/dk)', f'ORT. {d_load} (/dk)', f'KAMP {d_smax}', 'KATILDIĞI SEANS']
    
    st.dataframe(
        camp_impact.style.format(precision=1)\
            .background_gradient(cmap='Greys', subset=['KAMP ORT. İMPACT'], vmin=40, vmax=80)\
            .highlight_max(subset=[f'KAMP {d_smax}'], color='#fee2e2'),
        use_container_width=True, height=650
    )
    
    render_export_buttons(df=camp_impact.reset_index(drop=True), key_prefix="ia_camp", filename=f"Kamp_Liderleri_{sel_camp_label.replace(' ', '_')}")

# ── TAB 3: GELİŞİM ANALİZİ (Tarihsel Kıyaslama - DÜZELTİLDİ) ──────────────────
with tab3:
    section_title("GEÇMİŞ KAMPLARA GÖRE BİREYSEL GELİŞİM (LONGITUDINAL ANALYSIS)", "📈")
    st.markdown("<p style='color: gray; font-size: 13px;'>Oyuncunun güncel kamp verileri, <b>sadece kronolojik olarak bu kamptan önce gerçekleşmiş</b> tüm kampların ortalaması ile kıyaslanır.</p>", unsafe_allow_html=True)
    
    # HATA ÇÖZÜMÜ: Sadece seçilen kamptan "önceki" tarihli kampları tarihi (Chronological) veritabanı olarak alıyoruz.
    raw_age_data['tarih_dt'] = pd.to_datetime(raw_age_data['tarih'])
    historical_raw = raw_age_data[(raw_age_data['camp_id'] != sel_camp_id) & (raw_age_data['tarih_dt'] < sel_camp_start_date)].copy()
    
    if historical_raw.empty:
        st.info("Bu yaş grubunda seçili kamptan daha eski (önceki aylara ait) bir kamp verisi bulunmuyor. Gelişim analizi yapılamaz.")
    else:
        players = sorted(camp_data['player_name'].unique())
        sel_player = st.selectbox("OYUNCU SEÇİNİZ", players, key="ia_dev_player")
        
        # Geçmiş kamp verilerini Z-Score motorundan geçir
        historical_processed = calculate_impact_score_engine(historical_raw)
        
        # HATA KORUMASI: Oyuncu eski kamplarda var mı?
        if historical_processed.empty or sel_player not in historical_processed['player_name'].values:
             st.warning(f"⚠️ {sel_player.upper()} isimli oyuncunun seçilen tarihten daha eski bir kamp kaydı bulunmuyor (İlk kez kampa katılmış olabilir). Gelişim oranı hesaplanamadı.")
        else:
            dev_stats = calculate_development_stats(camp_data, historical_processed)
            
            if sel_player in dev_stats.index:
                player_dev = dev_stats.loc[sel_player]
                
                cols = st.columns(4)
                
                # Dinamik İsimlerle Sözlük Tanımlama
                metrics_dict = {
                    'impact_score': 'İMPACT SKOR DEĞİŞİMİ',
                    'dist_25_plus_pm': f'{d_dist_25} (m/dk)',
                    'player_load_pm': f'{d_load} (/dk)',
                    'total_distance_pm': f'{d_tdist} (m/dk)'
                }
                
                for idx, (key, label) in enumerate(metrics_dict.items()):
                    change = player_dev[key] if key in player_dev else np.nan
                    
                    if pd.isna(change):
                         color, arrow, val_str = COLORS['GRAY_500'], "▬", "Veri Yok"
                    else:
                        color = COLORS['GREEN'] if change < 0 else COLORS['SUCCESS'] if change > 0 else COLORS['GRAY_500']
                        arrow = "▼" if change < 0 else "▲" if change > 0 else "▬"
                        val_str = f"{arrow} {abs(change):.1f}%"
                    
                    with cols[idx]:
                        st.markdown(f"""
                        <div style="border: 1px solid #E5E7EB; border-radius: 6px; padding: 20px; background: white; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                            <div style="font-size: 11px; color: #6B7280; font-weight: 800; letter-spacing: 1px;">{label}</div>
                            <div style="font-size: 32px; font-family: 'Bebas Neue'; color: {color}; margin-top: 5px;">
                                {val_str}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("Seçili oyuncunun gelişim verisi hesaplanamadı.")

# ── TAB 4: TREND ANALİZİ (İstikrar Tespiti) ──────────────────────────────────
with tab4:
    section_title("KAMP İÇİ ETKİ (IMPACT) TRENDİ", "📉")
    st.markdown("<p style='color: gray; font-size: 13px;'>Oyuncunun kampın ilk gününden son gününe kadar gösterdiği performans dalgalanması (Varyans). Bu grafik oyuncunun yorgunluk direncini ölçer.</p>", unsafe_allow_html=True)
    
    sel_player_trend = st.selectbox("OYUNCU SEÇİNİZ", sorted(camp_data['player_name'].unique()), key="ia_trend_player")
    player_trend_data = camp_data[camp_data['player_name'] == sel_player_trend].sort_values('tarih')
    
    if len(player_trend_data) >= 2:
        daily_impact = player_trend_data[['tarih', 'impact_score']].copy()
        daily_impact['tarih_str'] = daily_impact['tarih'].dt.strftime('%d.%m')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_impact['tarih_str'], y=daily_impact['impact_score'],
            mode='lines+markers',
            name='Impact Score',
            line=dict(color=COLORS['GREEN'], width=3, shape='spline'),
            marker=dict(size=10, color='white', line=dict(color=COLORS['GREEN'], width=2))
        ))
        
        mean_impact = daily_impact['impact_score'].mean()
        fig.add_hline(y=mean_impact, line_dash="dash", line_color=COLORS['GRAY_400'], 
                      annotation_text=f"Kamp Ortalaması: {mean_impact:.1f}",
                      annotation_position="top left",
                      annotation_font=dict(size=11, color=COLORS['GRAY_600']))
                      
        fig.update_layout(
            template="plotly_white", 
            height=450, 
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(title="Tarih", gridcolor='#F3F4F6', tickfont=dict(weight="bold")),
            yaxis=dict(title="Impact Score (0-100)", gridcolor='#F3F4F6')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Trend analizi grafiği çizebilmek için oyuncunun bu kampta en az 2 seans verisi gereklidir.")

st.markdown('<div class="tff-footer"><p>Rugby Performans Sistemi · İstatistik ve Performans Modelleme</p></div>', unsafe_allow_html=True)