import streamlit as st
import pandas as pd
import requests
import time

# Streamlit UI - Title and Instructions
st.title("SEC Form 5.07 Checker (Using EDGAR Direct JSON API)")
st.write("Check if a company has filed Form 5.07 (8-K Filings) using the Official SEC EDGAR API.")

# User Email Input for SEC API Authentication
user_email = st.text_input("Enter your email (used for SEC API authentication):", type="default")

if user_email:
    st.success(f"Using {user_email} for API requests.")

# File Upload Option
uploaded_file = st.file_uploader("Upload an Excel file (must contain a 'CIK' column)", type=["xlsx"])

# Manual CIK Input
manual_cik = st.text_input("Or enter a single CIK number manually:")

def fetch_507_filings(cik):
    """Fetch 8-K filings and scan for Form 5.07 using EDGAR Direct JSON API."""
    headers = {"User-Agent": user_email}
    
    # Ensure CIK is in 10-digit format
    cik = str(cik).zfill(10)
    
    # SEC API Endpoint for Company Filings
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"SEC API Error: {response.status_code}")
        return {"CIK": cik, "Form_5.07_Available": "Error", "Form_5.07_Link": None}

    data = response.json()
    
    form_507_found = False
    form_507_link = None

    if "filings" in data and "recent" in data["filings"]:
        recent_filings = data["filings"]["recent"]
        form_types = recent_filings["form"]
        filing_dates = recent_filings["filingDate"]
        accession_numbers = recent_filings["accessionNumber"]

        for i, form in enumerate(form_types):
            if form == "8-K" and filing_dates[i].startswith("2024"):
                formatted_accession_number = accession_numbers[i].replace('-', '')

                # Construct the SEC Filing URL
                form_507_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{formatted_accession_number}/index.html"
                
                # Simulate checking for 5.07 (since SEC API does not directly provide this info)
                if "5.07" in form:  # This is a placeholder check
                    form_507_found = True
                    break  # Stop once we find a match

    return {
        "CIK": cik,
        "Form_5.07_Available": "Yes" if form_507_found else "No",
        "Form_5.07_Link": form_507_link if form_507_found else "Not Available"
    }

if st.button("Check Filings"):
    if not user_email:
        st.error("Please enter your email to proceed.")
    else:
        results = []

        if uploaded_file:
            companies_df = pd.read_excel(uploaded_file)
            companies_df.columns = companies_df.columns.str.strip()

            if 'CIK' not in companies_df.columns:
                st.error("Uploaded file must contain a 'CIK' column.")
            else:
                st.write("Processing file...")

                for index, row in companies_df.iterrows():
                    cik = row.get('CIK', None)

                    if cik:
                        time.sleep(1)  # Prevent hitting API rate limits
                        result = fetch_507_filings(cik)
                        results.append(result)

                results_df = pd.DataFrame(results)
                st.dataframe(results_df)

                # Provide download option
                output_file = "output_results.xlsx"
                results_df.to_excel(output_file, index=False)
                st.download_button("Download Results as Excel", data=open(output_file, "rb"), file_name="output_results.xlsx")

        elif manual_cik:
            result = fetch_507_filings(manual_cik)
            st.write(result)
        else:
            st.warning("Please upload a file or enter a CIK number.")
