import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re

# Streamlit UI
st.title("SEC Form 5.07 Checker")
st.write("Check if a company has filed Form 5.07 (8-K Filings).")

# User Email Input for SEC API Authentication
user_email = st.text_input("Enter your email (used for SEC API authentication):", type="default")

if user_email:
    st.success(f"Using {user_email} for SEC API requests.")

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


def fetch_filings(cik, user_email):
    """Fetch 8-K filings and scan for Form 5.07 using SEC API and HTML parsing"""
    headers = {"User-Agent": user_email}
    cik = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for CIK {cik}: {e}")
        return {
            "CIK": cik,
            "Form_5.07_Available": "Error",
            "Form_5.07_Link": None
        }

    if response.status_code == 200:
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
                    filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{formatted_accession_number}/index.html"
                    
                    filing_html_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{formatted_accession_number}/primary-document.html"
                    
                    try:
                        filing_html_response = requests.get(filing_html_url, headers=headers, timeout=10)
                        filing_html_response.raise_for_status()
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 404:
                            st.warning(f"Warning: Primary document not found for CIK {cik}, accession number {formatted_accession_number}. Checking index page instead.")
                        else:
                            st.warning(f"Warning: Error fetching filing HTML for CIK {cik}, accession number {formatted_accession_number}: {e}")
                        continue
                        

                    if filing_html_response.status_code == 200:
                        soup = BeautifulSoup(filing_html_response.text, "html.parser")
                        filing_text = soup.get_text().lower()

                        if re.search(r"\bitem\s*5\.07\b", filing_text):
                            form_507_link = filing_url
                            form_507_found = True
                            break

                    time.sleep(0.1)

            return {
                "CIK": cik,
                "Form_5.07_Available": "Yes" if form_507_found else "No",
                "Form_5.07_Link": form_507_link if form_507_found else f"https://www.sec.gov/Archives/edgar/data/{cik}/NotFound.htm"
            }
        else:
            st.error(f"Error fetching data for CIK {cik}: HTTP {response.status_code}")
            return {
                "CIK": cik,
                "Form_5.07_Available": "Error",
                "Form_5.07_Link": None
            }

# Process Data on Button Click
if st.button("Check Filings"):
    if not user_email:
        st.error("Please enter your email to proceed.")
    elif not ciks:
        st.warning("Please enter at least one CIK or upload a file.")
    else:
        results = []
        for cik in ciks:
            result = fetch_filings(cik, user_email)
            results.append(result)

        results_df = pd.DataFrame(results)
        st.dataframe(results_df)

        # Provide download option
        output_file = "output_results.xlsx"
        results_df.to_excel(output_file, index=False)
        st.download_button("Download Results as Excel", data=open(output_file, "rb"), file_name="output_results.xlsx")
