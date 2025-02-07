import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re

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

@st.cache_data(show_spinner=False) #Added cache and took out spinner from fetch filing since its already there
def fetch_filings(cik):
    """Fetch 8-K filings and scan for Form 5.07 using SEC API and HTML parsing"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36", #Static user agent for this project to take out the reliance on the user email
    }
    cik = str(cik).zfill(10)
    base_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=8-K&dateb=&owner=exclude&count=100" #Look for 8k and filter from that
    try:
        with st.spinner(f"Fetching filings for CIK: {cik}"): #Added spinner for the user
            response = requests.get(base_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # This parsing logic needs to be adapted based on the actual HTML structure
            # of the EDGAR search results page. This example assumes a table structure.

            table = soup.find('table', class_='tableFile2')  # Adapt class name if needed
            if table:
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) > 3:
                        description = cells[1].text.strip().lower()
                        filing_date = cells[2].text.strip()
                        document_link = cells[3].find('a', href=True)
                        if document_link and filing_date.startswith("2024"): #Added the filing date for only the year 2024
                            document_url = "https://www.sec.gov" + document_link['href']
                            #Checking document Link here
                            document_response = requests.get(document_url)
                            document_response.raise_for_status()
                            document_soup = BeautifulSoup(document_response.content, 'html.parser')
                            document_text = document_soup.get_text().lower()

                            if "item 5.07" in document_text:
                                return {"CIK": cik, "Form_5.07_Available": "Yes", "Form_5.07_Link":document_url}
            return {"CIK": cik,"Form_5.07_Available": "No", "Form_5.07_Link": 'N/A'}
    except requests.exceptions.RequestException as e:
        st.error(f"Scraping error for CIK {cik}: {e}")
        return {"CIK": cik, "Form_5.07_Available": "Error", "Form_5.07_Link": None}

# Process Data on Button Click
if st.button("Check Filings"):
    if not ciks:
        st.warning("Please enter at least one CIK or upload a file.")
    else:
        results = []
        for cik in ciks:
            result = fetch_filings(cik)
            results.append(result)

        results_df = pd.DataFrame(results)
        st.dataframe(results_df)

        # Provide download option
        output_file = "output_results.xlsx"
        results_df.to_excel(output_file, index=False)
        st.download_button("Download Results as Excel", data=open(output_file, "rb"), file_name="output_results.xlsx")
