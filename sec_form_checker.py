import streamlit as st
import pandas as pd
from edgar import Company, set_identity

# Streamlit UI
st.title("SEC Form 5.07 Checker")
st.write("Check if a company has filed Form 5.07 (8-K Filings).")

# Set your identity (replace with your email address)
identity = st.text_input("Enter your email (used for SEC API authentication):", type="default")

# Input Method Selection
input_method = st.radio("Select Input Method:", ("Manual CIK Input", "Upload Excel File"))

if input_method == "Manual CIK Input":
    # Manual CIK Input
    manual_cik = st.text_area("Enter CIKs (comma-separated):")
    ciks = [cik.strip() for cik in manual_cik.split(',') if cik.strip()]

elif input_method == "Upload Excel File":
    # File Upload Option
    uploaded_file = st.file_uploader("Upload an Excel file (must contain a 'CIK' column)", type=["xlsx"])
    if uploaded_file is not None:
        try:
            companies_df = pd.read_excel(uploaded_file)
            companies_df.columns = companies_df.columns.str.strip()
            if 'CIK' not in companies_df.columns:
                st.error("Uploaded file must contain a 'CIK' column.")
                ciks = []  # Ensure ciks is empty to prevent processing
            else:
                ciks = companies_df['CIK'].astype(str).tolist()
        except Exception as e:
            st.error(f"Error processing file: {e}")
            ciks = [] # Ensure ciks is empty to prevent processing
else:
    ciks = []  # Initialize ciks to an empty list


def check_form_507(cik):
    """Checks for Form 5.07 filing for a given CIK."""
    try:
        # Initialize the company object using CIK number
        company = Company(cik)

        # Get all 8-K filings
        filings = company.get_filings(form="8-K")

        # Filter for Form 5.07 within the retrieved 8-K filings for the year 2024
        form_507_found = False
        form_507_link = None

        for filing in filings:
            try:
                if hasattr(filing, 'items') and '5.07' in filing.items:
                    if hasattr(filing, 'filing_date'):
                        filing_date = filing.filing_date.strftime('%Y-%m-%d')
                        if filing_date.startswith("2024"):
                            form_507_found = True

                            # Format Accession Number Correctly
                            formatted_accession_number = filing.accession_number.replace('-', '')

                            # Construct the correct SEC URL
                            form_507_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{formatted_accession_number}/index.html"
                            break  # Exit loop as soon as we find one match
            except Exception as e:
                st.error(f"Error processing filing for CIK {cik}: {e}")
                return "Error", None

        return form_507_found, form_507_link

    except Exception as e:
        st.error(f"Error processing company with CIK {cik}: {e}")
        return "Error", None

# Process Data on Button Click
if st.button("Check Filings"):
    if not identity:
        st.error("Please enter your email to proceed.")
    elif not ciks:
        st.warning("Please enter at least one CIK or upload a file.")
    else:
        set_identity(identity)
        results = []
        with st.spinner("Processing..."):
            for cik in ciks:
                form_507_found, form_507_link = check_form_507(cik)
                if form_507_found == "Error":
                    results.append({
                        "CIK": cik,
                        "Form_5.07_Available": "Error",
                        "Form_5.07_Link": "Error"
                    })
                else:
                    results.append({
                        "CIK": cik,
                        "Form_5.07_Available": "Yes" if form_507_found else "No",
                        "Form_5.07_Link": form_507_link if form_507_found else f"https://www.sec.gov/Archives/edgar/data/{cik}/NotFound.htm"
                    })
        results_df = pd.DataFrame(results)
        st.dataframe(results_df)

        # Provide download option
        output_file = "output_results.xlsx"
        results_df.to_excel(output_file, index=False)
        st.download_button("Download Results as Excel", data=open(output_file, "rb"), file_name="output_results.xlsx")
