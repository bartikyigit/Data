import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import re

class ExportManager:
    @staticmethod
    def _safe_filename(filename):
        """Dosya isimlerindeki boşluk ve özel karakterleri güvenli hale getirir"""
        return re.sub(r'[^\w\s-]', '', filename).strip()

    @staticmethod
    def export_figure_png(fig, filename="figure"):
        """Plotly figürü PNG olarak indir (Kaleido hatasına karşı korumalı)"""
        safe_fname = ExportManager._safe_filename(filename)
        try:
            from plotly.io import write_image
            # Çözünürlüğü ve kaliteyi artırmak için scale=2 eklendi
            img_bytes = fig.to_image(format="png", width=1400, height=700, scale=2)
            st.download_button(
                label="📷 PNG İNDİR",
                data=img_bytes,
                file_name=f"{safe_fname}.png",
                mime="image/png",
                key=f"png_{safe_fname}"
            )
        except Exception as e:
            # Kaleido çalışmazsa ekranı bozmadan şık bir hata butonu gösterir
            st.button("❌ PNG HATASI (KALEIDO)", disabled=True, key=f"png_err_{safe_fname}", help=f"Sisteminizde 'kaleido' eksik olabilir. Detay: {str(e)}")

    @staticmethod
    def export_figure_html(fig, filename="figure"):
        """Plotly figürü HTML olarak indir"""
        safe_fname = ExportManager._safe_filename(filename)
        try:
            from plotly.io import write_html
            html_string = write_html(fig, include_plotlyjs='cdn', output_type='div')
            st.download_button(
                label="🌐 İNTERAKTİF HTML",
                data=html_string,
                file_name=f"{safe_fname}.html",
                mime="text/html",
                key=f"html_{safe_fname}"
            )
        except Exception as e:
            st.error(f"HTML export hatası: {e}")

    @staticmethod
    def export_dataframe_excel(df, filename="data"):
        """DataFrame'i Excel olarak indir"""
        safe_fname = ExportManager._safe_filename(filename)
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Data', index=False)
            buffer.seek(0)
            st.download_button(
                label="📊 EXCEL İNDİR",
                data=buffer.getvalue(),
                file_name=f"{safe_fname}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"excel_{safe_fname}"
            )
        except Exception as e:
            st.error(f"Excel export hatası: {e}")

    @staticmethod
    def export_dataframe_csv(df, filename="data"):
        """DataFrame'i CSV olarak indir"""
        safe_fname = ExportManager._safe_filename(filename)
        try:
            # utf-8-sig Excel'de Türkçe karakterlerin (ı,ş,ğ vb.) düzgün okunmasını sağlar
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📝 CSV İNDİR",
                data=csv,
                file_name=f"{safe_fname}.csv",
                mime="text/csv",
                key=f"csv_{safe_fname}"
            )
        except Exception as e:
            st.error(f"CSV export hatası: {e}")

export_manager = ExportManager()