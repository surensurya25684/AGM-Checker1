import streamlit as st
import pandas as pd
import requests

# Streamlit UI
st.title("SEC Form 5.07 Checker")
st.write("Check if a company has filed Form 5.07 (8-K Filings).")

# User Email Input for SEC API Authentication
user_email = st.text_input("Enter your email (used for SEC API authentication):", type="default")

if user_email:
    st.success(f"Using {user_email} for SEC API requests.")

# File Upload Option
uploaded_file = st.file_uploader("Upload an Excel file (must contain a 'CIK' column)", type=["xlsx"])

# Manual CIK Input
manual_cik = st.text_input("Or enter a CIK number manually:")

# Button to Process Data
if st.button("Check Filings"):
    if not user_email:
        st.error("Please enter your email to proceed.")
    else:
        results = []

        def fetch_filings(cik):
            """Fetch 8-K filings and check for Form 5.07 using the SEC API"""
            headers = {"User-Agent": user_email}
            cik = str(cik).zfill(10)  # Ensure CIK is 10 digits
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                
                # Extract the latest 8-K filings
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
                            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{formatted_accession_number}/index.json"

                            # Fetch filing details
                            filing_response = requests.get(filing_url, headers=headers)

                            if filing_response.status_code == 200:
                                filing_data = filing_response.json()

                                # Check if Item 5.07 is in the filing
                                if "items" in filing_data and "5.07" in filing_data["items"]:
                                    form_507_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{formatted_accession_number}/index.html"
                                    form_507_found = True
                                    break

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

        if uploaded_file:
            companies_df = pd.read_excel(uploaded_file)
            companies_df.columns = companies_df.columns.str.strip()

            if 'CIK' not in companies_df.columns:
                st.error("Uploaded file must contain a 'CIK' column.")
            else:
                st.write("Processing file...")

                for index, row in companies_df.iterrows():
                    cik = row.get('CIK', None)
                    company_name = row.get('Company Name', 'Unknown')
                    issuer_id = row.get('Issuer id', 'Unknown')
                    analyst_name = row.get('Analyst name', 'Unknown')

                    if cik:
                        result = fetch_filings(cik)
                        result.update({
                            "Company Name": company_name,
                            "Issuer ID": issuer_id,
                            "Analyst Name": analyst_name
                        })
                        results.append(result)

                results_df = pd.DataFrame(results)
                st.dataframe(results_df)

                # Provide download option
                output_file = "output_results.xlsx"
                results_df.to_excel(output_file, index=False)
                st.download_button("Download Results as Excel", data=open(output_file, "rb"), file_name="output_results.xlsx")

        elif manual_cik:
            result = fetch_filings(manual_cik)
            st.write(result)
        else:
            st.warning("Please upload a file or enter a CIK number.")
