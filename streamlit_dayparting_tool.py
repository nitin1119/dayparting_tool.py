
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="India DayParting Analysis Tool", layout="wide")
st.title("📊 India DayParting Analysis Tool")

uploaded_file = st.file_uploader("Upload your Sponsored Products Report (.csv or .xlsx)", type=["csv", "xlsx"])

def clean_column(name):
    return name.strip().lower().replace('₹', '').replace('(', '').replace(')', '').replace('#', '').replace('%', '').strip()

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Normalize columns
        df.columns = [clean_column(col) for col in df.columns]

        # Column mapping
        col_map = {
            'start_time': next((c for c in df.columns if 'start time' in c), None),
            'impressions': next((c for c in df.columns if 'impression' in c), None),
            'clicks': next((c for c in df.columns if 'clicks' in c or c == 'clicks'), None),
            'spend': next((c for c in df.columns if 'spend' in c), None),
            'sales': next((c for c in df.columns if 'sales' in c), None)
        }

        missing = [k for k, v in col_map.items() if v is None]
        if missing:
            st.error(f"❌ Missing required columns: {', '.join(missing)}")
            st.stop()

        # Clean data
        df['hour'] = pd.to_datetime(df[col_map['start_time']].astype(str).str.zfill(5) + ":00", format='%H:%M:%S', errors='coerce').dt.hour
        df['impressions'] = pd.to_numeric(df[col_map['impressions']].astype(str).str.replace(',', ''), errors='coerce')
        df['clicks'] = pd.to_numeric(df[col_map['clicks']], errors='coerce')

        # STRONG CLEANUP FOR CURRENCY FIELDS
        df['spend'] = df[col_map['spend']].astype(str).str.replace(r'[₹$,A-Za-z\s]', '', regex=True).str.strip()
        df['sales'] = df[col_map['sales']].astype(str).str.replace(r'[₹$,A-Za-z\s]', '', regex=True).str.strip()
        df['spend'] = pd.to_numeric(df['spend'], errors='coerce')
        df['sales'] = pd.to_numeric(df['sales'], errors='coerce')

        summary = df.groupby('hour').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'spend': 'sum',
            'sales': 'sum'
        }).reset_index()

        if summary.empty:
            st.warning("⚠️ No data available after processing. Please check your report file.")
            st.stop()

        summary['ctr (%)'] = (summary['clicks'] / summary['impressions']) * 100
        summary['cpc (₹)'] = summary['spend'] / summary['clicks'].replace(0, np.nan)
        summary['acos (%)'] = (summary['spend'] / summary['sales'].replace(0, np.nan)) * 100
        summary['roas'] = summary['sales'] / summary['spend'].replace(0, np.nan)
        summary.fillna(0, inplace=True)

        st.subheader("📋 Hourly Summary Table")
        st.dataframe(summary.style.format({
            "ctr (%)": "{:.2f}",
            "cpc (₹)": "₹{:.2f}",
            "acos (%)": "{:.2f}",
            "roas": "{:.2f}"
        }))

        st.subheader("🔥 ROAS Heatmap by Hour")
        fig, ax = plt.subplots(figsize=(10, 5))
        heatmap_data = summary.pivot_table(values='roas', index='hour', aggfunc='sum')
        sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap="YlGnBu", ax=ax)
        st.pyplot(fig)

        st.subheader("⬇️ Download Processed Report")
        towrite = io.BytesIO()
        summary.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)
        st.download_button(
            label="📥 Download Excel Report",
            data=towrite,
            file_name="india_dayparting_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Something went wrong during processing: {e}")
