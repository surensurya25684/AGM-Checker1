import streamlit as st
import pandas as pd
import requests
from secedgar.client import NetworkClient
from secedgar.company import Company

# Streamlit UI
st.title("SEC Form 5.07 Checker")
st.write("Check if a company has filed Form 5.07 (8-K Filings).")

# User Email Input
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
            """Fetch 8-K filings and check for Form 5.07 using user's email"""
            client = NetworkClient(user_agent=user_email)
            company = Company(str(cik), client=client)
            filings = company.get_filings(form="8-K")

            form_507_found = False
            form_507_link = None

            for filing in filings:
                try:
                    if hasattr(filing, 'items') and '5.07' in filing.items:
                        if hasattr(filing, 'filing_date'):
                            filing_date = filing.filing_date.strftime('%Y-%m-%d')
                            if filing_date.startswith("2024"):
                                form_507_found = True
                                formatted_accession_number = filing.accession_number.replace('-', '')
                                form_507_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{formatted_accession_number}/index.html"
                                break
                except Exception as e:
                    st.warning(f"Error processing filing for CIK {cik}: {e}")

            return {
                "CIK": cik,
                "Form_5.07_Available": "Yes" if form_507_found else "No",
                "Form_5.07_Link": form_507_link if form_507_found else f"https://www.sec.gov/Archives/edgar/data/{cik}/NotFound.htm"
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
