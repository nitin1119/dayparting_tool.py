
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="India DayParting Analysis Tool", layout="wide")

st.title("📊 India DayParting Analysis Tool")

uploaded_file = st.file_uploader("Upload your Sponsored Products Report (.csv or .xlsx)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df['Start Time'] = pd.to_datetime(df['Start Time'], format='%H:%M:%S', errors='coerce')
        df['Hour'] = df['Start Time'].dt.hour

        df['Impressions'] = pd.to_numeric(df['Impressions'], errors='coerce')
        df['Clicks'] = pd.to_numeric(df['Clicks'], errors='coerce')
        df['Spend'] = df['Spend'].replace('[₹$,]', '', regex=True)
        df['Spend'] = pd.to_numeric(df['Spend'], errors='coerce')
        df['7 Day Total Sales (₹)'] = df['7 Day Total Sales (₹)'].replace('[₹$,]', '', regex=True)
        df['7 Day Total Sales (₹)'] = pd.to_numeric(df['7 Day Total Sales (₹)'], errors='coerce')

        summary = df.groupby('Hour').agg({
            'Impressions': 'sum',
            'Clicks': 'sum',
            'Spend': 'sum',
            '7 Day Total Sales (₹)': 'sum'
        }).reset_index()

        summary['CTR (%)'] = (summary['Clicks'] / summary['Impressions']) * 100
        summary['CPC (₹)'] = summary['Spend'] / summary['Clicks'].replace(0, np.nan)
        summary['ACOS (%)'] = (summary['Spend'] / summary['7 Day Total Sales (₹)'].replace(0, np.nan)) * 100
        summary['ROAS'] = summary['7 Day Total Sales (₹)'] / summary['Spend'].replace(0, np.nan)
        summary.fillna(0, inplace=True)

        st.subheader("📋 Hourly Summary Table")
        st.dataframe(summary.style.format({
            "CTR (%)": "{:.2f}",
            "CPC (₹)": "₹{:.2f}",
            "ACOS (%)": "{:.2f}",
            "ROAS": "{:.2f}"
        }))

        st.subheader("🔥 ROAS Heatmap by Hour")
        fig, ax = plt.subplots(figsize=(10, 5))
        heatmap_data = summary.pivot_table(values='ROAS', index='Hour', aggfunc='sum')
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
        st.error(f"Error: {e}")
