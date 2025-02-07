import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Streamlit UI
st.title("SEC Form 5.07 Checker")
st.write("Check if a company has filed Form 5.07 (8-K Filings).")

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
    """Checks for Form 5.07 filing for a given CIK, and tries to automate the manual check."""

    cik_str = str(cik).zfill(10)  # CIKs need to be 10 digits

    # Construct the EDGAR search URL
    edgar_search_url = f"https://www.sec.gov/edgar/search/#/q=formType%253A%25228-K%2522%20AND%20item%253A%25225.07%2522%20AND%20cikNumber%253A%2522{cik_str}%2522&dateRange=all&category=custom&entityName=CIK{cik_str}&forms=8-K"

    try:
        response = requests.get(edgar_search_url)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.content, "html.parser")

        # Check if any results are displayed on the page
        no_results_element = soup.find("div", class_="no-results")
        if no_results_element:
            #If No results found
            return edgar_search_url, "No"
        else:
            #If results were found
            return edgar_search_url, "Yes"

    except requests.exceptions.RequestException as e:
        st.error(f"Error while scraping EDGAR: {e}")
        return edgar_search_url, "Error"

# Process Data on Button Click
if st.button("Check Filings"):
    if not ciks:
        st.warning("Please enter at least one CIK or upload a file.")
    else:
        results = []
        for cik in ciks:
            edgar_search_url, availability = check_form_507(cik)

            results.append({
                "CIK": cik,
                "Form_5.07_Available": availability,
                "Form_5.07_Link": f"[{edgar_search_url}]({edgar_search_url})",
                "Instructions": "Click the link to manually *VERIFY* the 5.07 filing on EDGAR."
            })

        results_df = pd.DataFrame(results)
        st.dataframe(results_df, column_config={
            "Form_5.07_Link": st.column_config.LinkColumn("EDGAR Search Link")
        })

        # Provide download option
        output_file = "output_results.xlsx"
        results_df.to_excel(output_file, index=False)
        st.download_button("Download Results as Excel", data=open(output_file, "rb"), file_name="output_results.xlsx")
