# app.py

import streamlit as st
import pandas as pd
from simpro_utils import get_access_token
from prebuild_export import extract_prebuilds

st.set_page_config(page_title="SimPro Prebuild Export", layout="centered")
st.title("📦 SimPro Prebuild Export Tool")

with st.form("export_form"):
    simpro_username = st.text_input("SimPro Username")
    simpro_password = st.text_input("SimPro Password", type="password")
    simpro_company_id = st.text_input("SimPro Company ID")
    run_export = st.form_submit_button("Run Export")

if run_export:
    if not simpro_username or not simpro_password or not simpro_company_id:
        st.error("❌ Please enter username, password, and company ID.")
    else:
        token = get_access_token(simpro_username, simpro_password)
        if not token:
            st.error("❌ Authentication failed. Check your credentials.")
        else:
            st.success("✅ Logged in to SimPro.")
            with st.spinner("Fetching and processing data..."):
                df = extract_prebuilds(token, simpro_company_id)
                if df.empty:
                    st.warning("⚠️ No data found.")
                else:
                    filename = f"prebuild_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    df.to_excel(filename, index=False)

                    with open(filename, "rb") as f:
                        st.download_button(
                            label="📥 Download Excel File",
                            data=f,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )