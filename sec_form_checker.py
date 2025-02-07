import streamlit as st
import pandas as pd
from sec_api import SecAPI

# Streamlit UI
st.title("SEC Form 5.07 Checker")
st.write("Check if a company has filed Form 5.07 (8-K Filings).")

# SEC API Key Input
sec_api_key = st.text_input("Enter your SEC API key:", type="password") # Add your api key

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

def check_form_507(cik, sec_api_key):
    """Checks for Form 5.07 filings in 2024 using the SEC API."""
    sec_api = SecAPI(api_key=sec_api_key) # Add your api key

    query = {
        "query": f"formType:\"8-K\" AND item:\"5.07\" AND cikNumber:{cik} AND filedAt:[2024-01-01 TO 2024-12-31]",
        "from": "0",
        "size": "100",  # Get up to 100 filings
        "sort": [{"filedAt": {"order": "desc"}}]
    }

    try:
        response = sec_api.query(query)
        filings = response.get('filings', [])  # Safely get the filings list

        # Extract links from the filings
        links = []
        for filing in filings:
            accession_number = filing['accessionNumber'].replace('-', '')
            form_507_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/index.html"
            links.append(form_507_link)

        return links

    except Exception as e:
        st.error(f"Error processing company with CIK {cik}: {e}")
        return []

# Process Data on Button Click
if st.button("Check Filings"):
    if not sec_api_key:
        st.error("Please enter your SEC API key to proceed.")
    elif not ciks:
        st.warning("Please enter at least one CIK or upload a file.")
    else:
        results = []
        with st.spinner("Processing..."):
            for cik in ciks:
                links = check_form_507(cik, sec_api_key)

                if links:
                    for link in links:
                        results.append({
                            "CIK": cik,
                            "Form_5.07_Available": "Yes",
                            "Form_5.07_Link": link
                        })
                else:
                    results.append({
                        "CIK": cik,
                        "Form_5.07_Available": "No",
                        "Form_5.07_Link": "No 5.07 filings found in 2024"
                    })

        results_df = pd.DataFrame(results)
        st.dataframe(results_df, column_config={
            "Form_5.07_Link": st.column_config.LinkColumn("EDGAR Filing Link")
        })

        # Provide download option
        output_file = "output_results.xlsx"
        results_df.to_excel(output_file, index=False)
        st.download_button("Download Results as Excel", data=open(output_file, "rb"), file_name="output_results.xlsx")
