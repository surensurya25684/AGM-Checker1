import streamlit as st
import pandas as pd
import requests

# Streamlit UI
st.title("SEC Form 5.07 Checker")
st.write("Check if a company has filed Form 5.07 (8-K Filings).")

# API-Ninjas API Key Input
api_ninjas_api_key = st.text_input("Enter your API-Ninjas API Key:", type="password")

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


def check_form_507(cik, api_key):
    """Checks for Form 5.07 filings using the API-Ninjas API."""
    base_url = "https://api.api-ninjas.com/v1/sec"  # API-Ninjas SEC API endpoint

    # Construct the API request URL
    url = f"{base_url}?ticker={cik}&filing=8-K"  # API ninjas uses the ticker, not CIK
    try:
        response = requests.get(url, headers={'X-Api-Key': api_key})
        response.raise_for_status()  # Raise an exception for bad status codes

        data = response.json()

        # Adapt this part depending on API-Ninjas response structure
        links = []
        for filing in data:  # Assuming the response is a list of filings
            #From API-Ninjas, the links are .documents
            form_507_link = filing.get('documents')  # URL is within the 'documents' field
            if form_507_link:
                links.append(form_507_link)
        return links

    except requests.exceptions.RequestException as e:
        st.error(f"Error while accessing API-Ninjas API: {e}")
        return []
    except Exception as e:
        st.error(f"Error processing the API-Ninjas API response: {e}")
        return []


# Process Data on Button Click
if st.button("Check Filings"):
    if not api_ninjas_api_key:
        st.error("Please enter your API-Ninjas API key to proceed.")
    elif not ciks:
        st.warning("Please enter at least one CIK or upload a file.")
    else:
        results = []
        with st.spinner("Processing..."):
            for cik in ciks:
                links = check_form_507(cik, api_ninjas_api_key)

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
                        "Form_5.07_Link": "No 5.07 filings found"
                    })

        results_df = pd.DataFrame(results)
        st.dataframe(results_df, column_config={
            "Form_5.07_Link": st.column_config.LinkColumn("EDGAR Filing Link")
        })

        # Provide download option
        output_file = "output_results.xlsx"
        results_df.to_excel(output_file, index=False)
        st.download_button("Download Results as Excel", data=open(output_file, "rb"), file_name="output_results.xlsx")
