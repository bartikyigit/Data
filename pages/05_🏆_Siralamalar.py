import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import AGE_GROUPS, METRICS, PRIMARY_METRICS, DEFAULT_MINUTES
from database import db_manager
from styles import inject_styles, page_header, section_title, info_box, COLORS
from utils import (render_export_buttons, calculate_composite_score,
                   percentile_color)

st.set_page_config(page_title="Sıralamalar | TFF", layout="wide")
inject_styles()
page_header("📊", "SIRALAMALAR",
            "Günlük · Kamp · Atletik Performans Skorlaması (Percentile) bazlı performans sıralamaları")

# ── Yaş Grubu Seçimi ve Veri Çekme ───────────────────────────────────────────
age_group = st.selectbox("YAŞ GRUBU", AGE_GROUPS, key="rk_age")

try:
    raw_age_data = db_manager.get_data_by_age_group(age_group)
    if raw_age_data.empty:
        st.warning(f"{age_group} için veri bulunamadı."); st.stop()

    camps = db_manager.get_camps(age_group)
    if camps.empty:
        st.warning("Kamp bulunamadı."); st.stop()
    camp_options = {row['camp_name']: row['camp_id'] for _, row in camps.iterrows()}

    # ── Dakika Filtreleri (Veri Kirliliğini Önler) ───────────────────────────
    with st.expander("⚙️ DAKİKA VE VERİ FİLTRELERİ", expanded=False):
        st.markdown("<div style='font-size:13px; color:#6B7280; margin-bottom:10px;'>Sıralama adaletsizliğini önlemek için az süre alınan seansları filtreleyebilirsiniz.</div>", unsafe_allow_html=True)
        dk1, dk2 = st.columns(2)
        with dk1: min_train_dk = st.number_input("Minimum Antrenman Dakikası", value=DEFAULT_MINUTES['TRAINING'], step=5, key="rk_dk_tr")
        with dk2: min_match_dk = st.number_input("Minimum Maç Dakikası", value=DEFAULT_MINUTES['MATCH'], step=5, key="rk_dk_ma")

    def apply_minute_filter(df):
        if df.empty: return df
        is_tr = df['tip'].str.upper().str.contains('TRAINING')
        is_ma = df['tip'].str.upper().str.contains('MATCH')
        mask = (is_tr & (df['minutes'] >= min_train_dk)) | (is_ma & (df['minutes'] >= min_match_dk))
        return df[mask].copy()

    age_data = apply_minute_filter(raw_age_data)
    if age_data.empty:
        st.warning("Seçili dakika filtresine uygun veri kalmadı. Lütfen filtreyi düşürün."); st.stop()

    rk_type = st.radio("SIRALAMA TİPİ",
                        ["📅 GÜNLÜK", "⚽ KAMP ORTALAMASI", "🎯 ATLETİK SKORLAMA (PERCENTILE)"],
                        horizontal=True, key="rk_type")
    st.divider()

    # ── 1. GÜNLÜK SIRALAMA ───────────────────────────────────────────────────
    if rk_type == "📅 GÜNLÜK":
        section_title("GÜNLÜK SIRALAMA", "📅")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sel_camp = st.selectbox("KAMP SEÇİMİ", list(camp_options.keys()), key="rk_gcamp")
            sel_cid  = camp_options[sel_camp]
            raw_cd = db_manager.get_data_by_camp(sel_cid)
            cd = apply_minute_filter(raw_cd)
        with c2:
            dates = sorted(cd['tarih'].dropna().unique())
            sel_date = st.selectbox("TARİH", dates,
                format_func=lambda x: pd.Timestamp(x).strftime('%d.%m.%Y') if x else "—",
                key="rk_gdate")
        with c3:
            ses = st.radio("SEANS TİPİ", ["Tümü","TRAINING","MATCH"],
                           horizontal=True, key="rk_gses")
        with c4:
            # Sadece geçerli ana metrikleri (11 metrik) dinamik olarak listeler
            avail = [m for m in PRIMARY_METRICS if m in cd.columns and cd[m].dropna().any()]
            sel_m = st.selectbox("METRİK SEÇİMİ", avail,
                                 format_func=lambda x: METRICS.get(x,{}).get('display',x).upper(),
                                 key="rk_gm")

        if sel_date is None: st.stop()
        filt   = cd if ses=="Tümü" else cd[cd['tip'].str.upper()==ses]
        sel_ts = pd.Timestamp(sel_date)
        day    = filt[filt['tarih'].dt.normalize()==sel_ts.normalize()].copy()

        if day.empty:
            st.info(f"{sel_ts.strftime('%d.%m.%Y')} için geçerli dakika sınırına ulaşan veri yok.")
        else:
            day = day.sort_values(sel_m, ascending=False).reset_index(drop=True)
            day['_rank'] = range(1, len(day)+1)
            n      = len(day)
            m_info = METRICS.get(sel_m, {})
            metric_label = m_info.get('display',sel_m).upper()
            metric_unit  = m_info.get('unit','')

            # 0 olan değerleri minimum hesabından çıkarıyoruz
            valid_for_min = day[sel_m].replace(0, pd.NA).dropna()
            min_v = valid_for_min.min() if not valid_for_min.empty else 0.0
            avg_v = day[sel_m].mean()
            max_v = day[sel_m].max()

            mm1, mm2, mm3 = st.columns(3)
            with mm1: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>MİN DEĞER</div><div class='sc-val' style='font-size:22px;'>{min_v:.1f} <span style='font-size:11px;color:#9CA3AF;'>{metric_unit}</span></div></div>", unsafe_allow_html=True)
            with mm2: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>ORTALAMA</div><div class='sc-val' style='font-size:22px;'>{avg_v:.1f} <span style='font-size:11px;color:#9CA3AF;'>{metric_unit}</span></div></div>", unsafe_allow_html=True)
            with mm3: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>MAX DEĞER</div><div class='sc-val' style='font-size:22px;'>{max_v:.1f} <span style='font-size:11px;color:#9CA3AF;'>{metric_unit}</span></div></div>", unsafe_allow_html=True)

            bar_colors = [
                f"rgba({'13,13,13' if 'MATCH' in str(t).upper() else '227,10,23'},{max(0.35,1-(i/max(n-1,1))*0.55)})"
                for i, t in enumerate(day['tip'])
            ]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=day['player_name'].str.upper(), x=day[sel_m], orientation='h',
                marker=dict(color=bar_colors, line=dict(color='rgba(0,0,0,0.06)', width=1)),
                text=[f"  #{r}  {v:.1f}" for r, v in zip(day['_rank'], day[sel_m])],
                textposition='inside', insidetextanchor='start',
                textfont=dict(color='white', size=12, family='DM Sans, sans-serif', weight='bold'),
                hovertemplate='<b>%{y}</b><br>%{x:.2f}<extra></extra>',
            ))
            fig.add_vline(x=avg_v, line_dash="dash", line_color=COLORS['GRAY_500'], line_width=1.5,
                          annotation_text=f"ORT: {avg_v:.1f}",
                          annotation_font=dict(size=11, color=COLORS['GRAY_700'], weight='bold'))
            fig.add_vline(x=min_v, line_dash="dot", line_color=COLORS['DANGER'],
                          line_width=1, opacity=0.5)
            fig.add_vline(x=max_v, line_dash="dot", line_color=COLORS['SUCCESS'],
                          line_width=1, opacity=0.5)
            fig.update_layout(
                title=dict(text=f"<b>{sel_ts.strftime('%d.%m.%Y')} · {metric_label}</b>",
                           font=dict(family='Bebas Neue, sans-serif', size=24, color=COLORS['GRAY_900'])),
                xaxis=dict(gridcolor='#F3F4F6', tickfont=dict(family='DM Sans', size=11, weight='bold'), title=metric_unit),
                yaxis=dict(tickfont=dict(family='DM Sans', size=12, color=COLORS['GRAY_800'], weight='bold')),
                template='plotly_white', height=max(450, n*35), showlegend=False,
                plot_bgcolor='#FAFAFA', paper_bgcolor=COLORS['WHITE'],
                font=dict(family='DM Sans'), margin=dict(l=20, r=60, t=60, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)

            disp = day[['_rank','player_name','tip','minutes',sel_m]].copy()
            disp.columns = ['SIRA','OYUNCU','TİP','DAKİKA', metric_label]
            render_export_buttons(fig=fig, df=disp, key_prefix="rk_g",
                                  filename=f"siralama_{sel_ts.strftime('%d%m%Y')}_{sel_m}")
            st.dataframe(disp, use_container_width=True, hide_index=True)

    # ── 2. KAMP ORTALAMASI SIRALAMASI ─────────────────────────────────────────
    elif rk_type == "⚽ KAMP ORTALAMASI":
        section_title("KAMP ORTALAMA SIRALAMASI", "⚽")
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_camp = st.selectbox("KAMP SEÇİMİ", list(camp_options.keys()), key="rk_kcamp")
            sel_cid  = camp_options[sel_camp]
            raw_cd = db_manager.get_data_by_camp(sel_cid)
            cd = apply_minute_filter(raw_cd)
        with c2:
            ses = st.radio("SEANS TİPİ", ["Tümü","TRAINING","MATCH"],
                           horizontal=True, key="rk_kses")
        with c3:
            avail = [m for m in PRIMARY_METRICS if m in cd.columns and cd[m].dropna().any()]
            sel_m = st.selectbox("METRİK SEÇİMİ", avail,
                                 format_func=lambda x: METRICS.get(x,{}).get('display',x).upper(),
                                 key="rk_km")

        filt = cd if ses=="Tümü" else cd[cd['tip'].str.upper()==ses]
        if filt.empty:
            st.warning("Seçilen kriterlere uygun veri bulunamadı."); st.stop()

        rk   = filt.groupby('player_name')[sel_m].agg(['mean','min','max','count']).round(2)
        rk   = rk.sort_values('mean', ascending=False)
        rk['Sıra'] = range(1, len(rk)+1)

        # Min/Max/Ort metrikleri
        valid_for_min = filt[sel_m].replace(0, pd.NA).dropna()
        team_min = valid_for_min.min() if not valid_for_min.empty else 0.0

        mm1, mm2, mm3 = st.columns(3)
        with mm1: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>TAKIM MİN</div><div class='sc-val' style='font-size:22px;'>{team_min:.1f}</div></div>", unsafe_allow_html=True)
        with mm2: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>TAKIM ORT.</div><div class='sc-val' style='font-size:22px;'>{filt[sel_m].mean():.1f}</div></div>", unsafe_allow_html=True)
        with mm3: st.markdown(f"<div class='metric-card' style='padding:12px;'><div class='sc-label'>TAKIM MAX</div><div class='sc-val' style='font-size:22px;'>{filt[sel_m].max():.1f}</div></div>", unsafe_allow_html=True)

        vals   = rk['mean'].values
        norms  = (vals - vals.min()) / (vals.max() - vals.min() + 1e-9)
        bar_c  = [f"rgba(227,{int(10+n*20)},{int(23+n*10)},{0.45+n*0.55})" for n in norms]
        m_info = METRICS.get(sel_m, {})
        metric_label = m_info.get('display',sel_m).upper()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=rk.index.str.upper(), y=rk['mean'],
            marker=dict(color=bar_c, line=dict(color='rgba(0,0,0,0.06)', width=1)),
            error_y=dict(
                type='data',
                array=rk['max'] - rk['mean'],
                arrayminus=rk['mean'] - rk['min'],
                visible=True,
                color=COLORS['GRAY_500'], thickness=1.5, width=4,
            ),
            text=[f"#{i}  {v:.1f}" for i, v in zip(rk['Sıra'], rk['mean'])],
            textposition='outside',
            textfont=dict(family='DM Sans', size=11, weight='bold'),
            hovertemplate='<b>%{x}</b><br>ORT: %{y:.2f}<extra></extra>',
        ))
        
        team_avg = filt[sel_m].mean()
        fig.add_hline(y=team_avg, line_dash='dash', line_color=COLORS['GRAY_500'], line_width=1.5,
                      annotation_text=f"TAKIM ORT: {team_avg:.1f}",
                      annotation_font=dict(size=11, color=COLORS['GRAY_700'], weight='bold'))
        
        fig.update_layout(
            title=dict(text=f"<b>KAMP SIRALAMASI · {metric_label}</b>  "
                            f"<span style='font-size:13px;color:#9CA3AF;'>— HATA ÇUBUKLARI: MİN/MAX ARALIĞI</span>",
                       font=dict(family='Bebas Neue', size=24, color=COLORS['GRAY_900'])),
            xaxis=dict(tickangle=-35, tickfont=dict(family='DM Sans', size=11, weight='bold')),
            yaxis=dict(title=m_info.get('unit',''), gridcolor='#F3F4F6',
                       tickfont=dict(family='DM Sans', size=11, weight='bold')),
            template='plotly_white', height=500, showlegend=False,
            plot_bgcolor='#FAFAFA', paper_bgcolor=COLORS['WHITE'],
            font=dict(family='DM Sans'), margin=dict(l=20, r=20, t=60, b=60)
        )
        st.plotly_chart(fig, use_container_width=True)
        info_box("📌 <b>Hata çubukları</b> oyuncunun o metrikte kamp boyunca çıktığı minimum ve maksimum aralığı (dalgalanmayı) gösterir.")

        show = rk.rename(columns={'mean':'ORTALAMA','min':'MİN','max':'MAX','count':'GEÇERLİ SEANS'})
        show = show[['Sıra','ORTALAMA','MİN','MAX','GEÇERLİ SEANS']]
        show.index.name = 'OYUNCU'
        render_export_buttons(fig=fig, df=show.reset_index(), key_prefix="rk_k",
                              filename=f"kamp_siralama_{sel_m}")
        st.dataframe(show, use_container_width=True)

    # ── 3. PERCENTİLE RANK (ATLETİK SKORLAMA) ────────────────────────────────
    else:
        section_title("ATLETİK PERFORMANS SKORLAMASI (PERCENTILE RANK)", "🎯")
        info_box(
            "<b>Atletik Performans Skorlaması</b>: Her oyuncunun her metrikte seçili gruptaki tüm oyuncular "
            "arasında kaçıncı yüzdelikte olduğu hesaplanır. Sonra bu yüzdeliklerin "
            "ortalaması alınarak <b>Bileşik Skor</b> elde edilir. "
            "<i>(50 = Takım Medyanı · 100 = En İyi)</i>"
        )

        c1, c2 = st.columns(2)
        with c1:
            sel_camp = st.selectbox("KAMP SEÇİMİ", list(camp_options.keys()), key="rk_bcamp")
            sel_cid  = camp_options[sel_camp]
            raw_cd = db_manager.get_data_by_camp(sel_cid)
            cd = apply_minute_filter(raw_cd)
        with c2:
            ses = st.radio("SEANS TİPİ", ["Tümü","TRAINING","MATCH"],
                           horizontal=True, key="rk_bses")

        filt    = cd if ses=="Tümü" else cd[cd['tip'].str.upper()==ses]
        if filt.empty:
            st.warning("Seçilen kriterlere uygun veri bulunamadı."); st.stop()
            
        players = filt['player_name'].unique()
        vpm     = [m for m in PRIMARY_METRICS if m in filt.columns and filt[m].notna().any()]

        # Tüm oyuncular için percentile hesapla
        rows = []
        for p in players:
            pdata = filt[filt['player_name'] == p]
            sc    = calculate_composite_score(pdata, filt,
                                              session_filter=ses if ses!="Tümü" else "ALL")
            row = {'OYUNCU': p.upper()}
            for m in vpm:
                row[METRICS.get(m,{}).get('display',m).upper()] = sc.get(m, 50)
            row['BİLEŞİK SKOR'] = sc.get('composite', 50)
            rows.append(row)

        result_df = pd.DataFrame(rows).sort_values('BİLEŞİK SKOR', ascending=False)
        result_df['SIRA'] = range(1, len(result_df)+1)

        # Bileşik skor bar grafiği
        sc_vals = result_df['BİLEŞİK SKOR'].values
        bar_c   = [percentile_color(v) for v in sc_vals]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=result_df['OYUNCU'], y=sc_vals,
            marker=dict(color=bar_c, line=dict(color='rgba(0,0,0,0.06)', width=1)),
            text=[f"#{i}  %{v:.0f}" for i, v in zip(result_df['SIRA'], sc_vals)],
            textposition='outside',
            textfont=dict(family='DM Sans', size=11, weight='bold'),
            hovertemplate='<b>%{x}</b><br>Bileşik Skor: %{y:.1f}<extra></extra>',
        ))
        fig.add_hline(y=50, line_dash='dash', line_color=COLORS['GRAY_500'], line_width=1.5,
                      annotation_text="TAKIM MEDYANI (50)",
                      annotation_font=dict(size=11, color=COLORS['GRAY_700'], weight='bold'))
        fig.update_layout(
            title=dict(text="<b>ATLETİK PERFORMANS BİLEŞİK SKORLARI</b>",
                       font=dict(family='Bebas Neue', size=24, color=COLORS['GRAY_900'])),
            xaxis=dict(tickangle=-35, tickfont=dict(family='DM Sans', size=11, weight='bold')),
            yaxis=dict(title='SKOR (%)', range=[0,115], gridcolor='#F3F4F6',
                       tickfont=dict(family='DM Sans', size=11, weight='bold')),
            template='plotly_white', height=500, showlegend=False,
            plot_bgcolor='#FAFAFA', paper_bgcolor=COLORS['WHITE'],
            font=dict(family='DM Sans'), margin=dict(l=20, r=20, t=60, b=60)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Heatmap tablosu
        section_title("SKORLAMA (PERCENTILE) ISI HARİTASI", "🗺️")
        metric_cols = [METRICS.get(m,{}).get('display',m).upper() for m in vpm]
        heat_df = result_df.set_index('OYUNCU')[metric_cols + ['BİLEŞİK SKOR']].round(0)
        
        # Streamlit dataframe gradient styling
        st.dataframe(heat_df.style.background_gradient(cmap="RdYlGn", vmin=0, vmax=100), use_container_width=True)

        render_export_buttons(fig=fig, df=result_df, key_prefix="rk_b",
                              filename="percentile_siralama")

        st.caption(
            "📌 Her sütundaki sayı, oyuncunun o metrikte kamp ortalamasının üstünde mi (yeşil) yoksa altında mı (kırmızı) kaldığını yüzdelik olarak gösterir. "
            "Bileşik skor, tüm metriklerin skorlamalarının eşit ağırlıklı ortalamasıdır."
        )

except Exception as e:
    st.error(f"❌ Hata: {str(e)}")
    import traceback; st.code(traceback.format_exc())

st.markdown('<div class="tff-footer"><p>Rugby Performans Sistemi · Performans Sıralamaları</p></div>',
            unsafe_allow_html=True)