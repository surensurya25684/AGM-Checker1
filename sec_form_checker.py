import streamlit as st
import pandas as pd
from edgar import Company
import io

# Streamlit App
st.title("SEC Form 5.07 Checker")

# Helper Function
@st.cache_data
def process_company(cik):
    """Processes a single company and returns the result, fetching company name from Edgar."""
    try:
        company = Company(cik)  # Only CIK is needed
        company_name = company.name
        filings = company.get_filings(form="8-K")
        form_507_found = any(
            hasattr(filing, 'items') and '5.07' in filing.items and filing.filing_date.year == 2024  #hardcoded target_year for safety and to allow it to work
            for filing in filings
        )

        link = next(
            (
                f"https://www.sec.gov/Archives/edgar/data/{cik}/{filing.accession_number.replace('-', '')}/index.html"
                for filing in filings
                if hasattr(filing, 'items') and '5.07' in filing.items and filing.filing_date.year == 2024   #Hardcoded target_year for safety and to allow it to work
            ),
            f"https://www.sec.gov/Archives/edgar/data/{cik}/NotFound.htm",
        )
        return {
            "CIK": cik,
            "Company Name": company_name,
            "Form_5.07_Available": "Yes" if form_507_found else "No",
            "Form_5.07_Link": link,
        }
    except Exception as e:
        st.error(f"Error processing CIK {cik}: {e}")
        return {"CIK": cik, "Company Name": "Error", "Form_5.07_Available": "Error", "Form_5.07_Link": None}

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
                results = [process_company(cik) for cik in ciks]
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
                results = [process_company(cik) for cik in ciks]
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
