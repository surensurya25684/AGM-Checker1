import streamlit as st
import pandas as pd
import requests
import time

# Financial Modeling Prep API Key (Get a free API key at https://financialmodelingprep.com/)
FMP_API_KEY = "YOUR_API_KEY"

# Streamlit UI - Title and Instructions
st.title("SEC Form 5.07 Checker")
st.write("Check if a company has filed Form 5.07 (8-K Filings) using the Financial Modeling Prep API.")

# User Email Input for SEC API Authentication
user_email = st.text_input("Enter your email (used for SEC API authentication):", type="default")

if user_email:
    st.success(f"Using {user_email} for API requests.")

# File Upload Option
uploaded_file = st.file_uploader("Upload an Excel file (must contain a 'CIK' column)", type=["xlsx"])

# Manual CIK Input
manual_cik = st.text_input("Or enter a single CIK number manually:")

def fetch_507_filings(cik):
    """Fetch 8-K filings and scan for Form 5.07 using Financial Modeling Prep API."""
    url = f"https://financialmodelingprep.com/api/v4/sec_filings?cik={cik}&apikey={FMP_API_KEY}"

    response = requests.get(url)
    if response.status_code != 200:
        st.error(f"API Error: {response.status_code}")
        return {"CIK": cik, "Form_5.07_Available": "Error", "Form_5.07_Link": None}

    data = response.json()
    
    form_507_found = False
    form_507_link = None

    if "filings" in data:
        for filing in data["filings"]:
            if filing["form"] == "8-K" and "5.07" in filing["description"]:
                form_507_link = filing["link"]
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
