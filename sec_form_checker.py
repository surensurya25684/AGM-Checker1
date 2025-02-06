import streamlit as st
import pandas as pd
from sec_edgar_downloader import Downloader

st.title("SEC Form 5.07 Checker")

@st.cache_data
def check_form_507(cik):
    try:
        dl = Downloader(".", cik) # Downloads to current directory
        num_8k = dl.get("8-K")
        # Check if any 8-K filings exist
        if num_8k > 0:
            return "Yes"
        else:
            return "No"
    except Exception as e:
        st.error(f"Error processing CIK {cik}: {e}")
        return "Error"

# Input Method Selection
input_method = st.radio("Select Input Method:", ("Manual CIK Input", "Upload Excel File"))

if input_method == "Manual CIK Input":
    # Input: CIKs (comma-separated)
    ciks_input = st.text_area("Enter CIKs (comma-separated):")
    ciks = [cik.strip() for cik in ciks_input.split(',') if cik.strip()]

    if st.button("Check"):
        if not ciks:
            st.warning("Please enter at least one CIK.")
        else:
            with st.spinner("Processing..."):
                results = []
                for cik in ciks:
                    form_507_available = check_form_507(cik)
                    results.append({"CIK": cik, "Form_5.07_Available": form_507_available})

            df = pd.DataFrame(results)
            st.dataframe(df)
            st.download_button(
                label="Download Results (Excel)",
                data=df.to_excel(index=False).encode('utf-8'),
                file_name="sec_form_507_results.xlsx",
                mime="application/vnd.ms-excel",
            )

elif input_method == "Upload Excel File":
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.str.strip()
            ciks = df['CIK'].astype(str).tolist()

            with st.spinner("Processing..."):
                results = []
                for cik in ciks:
                    form_507_available = check_form_507(cik)
                    results.append({"CIK": cik, "Form_5.07_Available": form_507_available})

            df = pd.DataFrame(results)
            st.dataframe(df)
            st.download_button(
                label="Download Results (Excel)",
                data=df.to_excel(index=False).encode('utf-8'),
                file_name="sec_form_507_results.xlsx",
                mime="application/vnd.ms-excel",
            )
        except Exception as e:
            st.error(f"Error processing file: {e}")
