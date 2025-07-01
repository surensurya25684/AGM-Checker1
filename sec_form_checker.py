import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime

# === CONFIGURATION ===
LOCAL_TRACKER_PATH = r"C:\Users\surysur\OneDrive\MSCI Office 365\DOC - Governance & EDM - dummy\Duplicate tracker.xlsx"

# === Clean Issuer IDs ===
def clean_id_column(series):
    return series.astype(str).str.replace(r"\s+", "", regex=True).str.strip().str.upper()

# === Load tracker from any source ===
@st.cache_data
def load_tracker_from_file(file):
    try:
        df = pd.read_excel(file)
        df["DMX issuer id"] = clean_id_column(df["DMX issuer id"])
        return df
    except Exception as e:
        st.error(f"❌ Failed to load tracker: {e}")
        return pd.DataFrame()

# === Send results to Teams ===
def send_to_teams(merged_df, webhook_url):
    if merged_df.empty:
        message = {"text": "📣 Issuer Lookup: No matching Issuer IDs found."}
    else:
        rows = [
            f"- {row['DMX_ISSUER_ID']} → {row['Profiler'] if pd.notnull(row['Profiler']) else 'Not Found'}"
            for _, row in merged_df.iterrows()
        ]
        message = {"text": f"📣 *Issuer Lookup Results:*\n" + "\n".join(rows)}

    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, json=message, headers=headers)

    if response.status_code == 200:
        st.success("✅ Message sent to Teams.")
    else:
        st.error(f"❌ Failed to send to Teams: {response.status_code} - {response.text}")

# === UI ===
st.set_page_config(page_title="Issuer Lookup", layout="wide")
st.title("🔍 Issuer ID → Profiler Lookup")

# === Tracker loading logic ===
tracker_df = pd.DataFrame()
tracker_source = ""

if os.path.exists(LOCAL_TRACKER_PATH):
    tracker_df = load_tracker_from_file(LOCAL_TRACKER_PATH)
    tracker_source = "📁 Loaded from local path"
    try:
        mod_time = os.path.getmtime(LOCAL_TRACKER_PATH)
        readable_time = datetime.fromtimestamp(mod_time).strftime("%d-%b-%Y %H:%M:%S")
        tracker_source += f" — last modified: **{readable_time}**"
    except:
        pass
else:
    uploaded_file = st.file_uploader("📤 Upload 'Duplicate tracker.xlsx'", type=["xlsx"])
    if uploaded_file:
        tracker_df = load_tracker_from_file(uploaded_file)
        tracker_source = "📤 Loaded from uploaded file"

if not tracker_df.empty:
    st.success(tracker_source)

    user_input = st.text_area("Enter DMX Issuer IDs (comma or newline separated):", height=150)

    if user_input:
        raw_ids = user_input.replace(",", "\n").splitlines()
        issuer_ids = [id.strip() for id in raw_ids if id.strip()]
        input_df = pd.DataFrame({"DMX_ISSUER_ID": issuer_ids})
        input_df["DMX_ISSUER_ID"] = clean_id_column(input_df["DMX_ISSUER_ID"])

        # Merge with tracker
        merged_df = pd.merge(
            input_df,
            tracker_df[["DMX issuer id", "Profiler"]],
            left_on="DMX_ISSUER_ID",
            right_on="DMX issuer id",
            how="left"
        )

        merged_df = merged_df[["DMX_ISSUER_ID", "Profiler"]]
        merged_df["Profiler"].fillna("Not Found", inplace=True)

        # Display results
        st.subheader("📊 Lookup Results")
        st.dataframe(merged_df, use_container_width=True)

        # Download button
        csv = merged_df.to_csv(index=False)
        st.download_button("📥 Download as CSV", csv, "issuer_lookup_results.csv", "text/csv")

        # Optional Teams integration
        webhook_url = st.text_input("Optional: Enter Microsoft Teams Webhook URL", type="password")
        if webhook_url:
            if st.button("📨 Send to Teams"):
                send_to_teams(merged_df, webhook_url)
else:
    st.warning("📂 Please upload the tracker file or make sure the local file exists.")
