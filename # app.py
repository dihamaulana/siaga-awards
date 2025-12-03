# app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import StringIO
import plotly.express as px

st.set_page_config(page_title="AI-EcoRecovery Dashboard (Sibolga)", layout="wide")

st.title("AI-EcoRecovery — Dashboard Pemulihan Ekonomi Pascabencana (Sibolga)")
st.markdown("Interactive dashboard: prioritas hibah / pinjaman, MMB, cicilan aman, dan analisis sensitivitas.")

# 1) DATA SOURCE: raw GitHub URL (ubah ke raw URL CSV di repo kalian)
DATA_URL = st.secrets.get("DATA_URL", "https://raw.githubusercontent.com/<USERNAME>/<REPO>/main/sibolga_final_analysis_with_hibah.csv")

@st.cache_data(ttl=300)
def load_data(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return pd.read_csv(StringIO(r.text))
    except Exception as e:
        st.error("Gagal memuat data. Periksa DATA_URL atau jaringan. Error: " + str(e))
        return pd.DataFrame()

df = load_data(DATA_URL)
if df.empty:
    st.stop()

# Basic filters
left, right = st.columns([1,3])
with left:
    st.header("Filter")
    kelurahan_sel = st.multiselect("Kelurahan", sorted(df['kelurahan'].unique()), default=sorted(df['kelurahan'].unique()))
    tipe_sel = st.multiselect("Tipe entitas", sorted(df['type'].unique()), default=sorted(df['type'].unique()))
    priority_sel = st.multiselect("Kategori prioritas", sorted(df['priority'].unique()), default=sorted(df['priority'].unique()))

# Apply filters
df_f = df[(df['kelurahan'].isin(kelurahan_sel)) & (df['type'].isin(tipe_sel)) & (df['priority'].isin(priority_sel))].copy()

# KPIs
with right:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Entitas tampil", f"{len(df_f)}")
    total_mmb = int(df_f['MMB'].sum())
    k2.metric("Total MMB (Rp)", f"{total_mmb:,}")
    total_hibah_100 = int(df_f.loc[df_f['priority'].isin(['Prioritas','Prioritas Hibah']), 'hibah_100pct'].sum())
    k3.metric("Total Hibah 100% (Rp)", f"{total_hibah_100:,}")
    k4.metric("Total Cicilan Aman (Rp/bln)", f"{int(df_f['cicilan_aman'].sum()):,}")

st.markdown("---")

# Charts: Prioritas per kelurahan
st.subheader("Prioritas per Kelurahan")
group = df_f.groupby(['kelurahan','priority']).size().reset_index(name='count')
fig = px.bar(group, x='kelurahan', y='count', color='priority', barmode='stack', title="Jumlah entitas per kategori prioritas")
st.plotly_chart(fig, use_container_width=True)

# Table top N
st.subheader("Top 15 Entitas Prioritas (urut by vuln_synth)")
topn = st.slider("Jumlah baris", 5, 30, 15)
top_table = df_f.sort_values('vuln_synth', ascending=False).head(topn)[[
    'id','type','kelurahan','priority','vuln_synth','MMB','hibah_100pct','hibah_prop','EMI_raw','cicilan_aman'
]]
st.dataframe(top_table.style.format({
    'vuln_synth': "{:.3f}",
    'MMB': "{:,.0f}",
    'hibah_100pct': "{:,.0f}",
    'hibah_prop': "{:,.0f}",
    'EMI_raw': "{:,.0f}",
    'cicilan_aman': "{:,.0f}"
}), height=420)

# Sensitivity heatmap
st.subheader("Analisis Sensitivitas Penjualan (proporsi Aman/Bahaya)")
sens_cols = ['sens_10','sens_25','sens_50']
sens_summary = df_f[sens_cols].apply(lambda col: (col=='Bahaya').sum()).reset_index()
sens_summary.columns = ['scenario','count_bahaya']
fig2 = px.bar(sens_summary, x='scenario', y='count_bahaya', title='Jumlah entitas dalam status "Bahaya" per scenario')
st.plotly_chart(fig2, use_container_width=True)

# Download CSV
st.subheader("Unduh hasil (CSV)")
csv = df_f.to_csv(index=False).encode('utf-8')
st.download_button(label="Download CSV hasil filter", data=csv, file_name='sibolga_filtered_results.csv', mime='text/csv')

st.markdown("---")
st.caption("Catatan: data simulasi. Untuk produksi, arahkan DATA_URL ke CSV yang terupdate di repo/Google Drive yang publik.")
