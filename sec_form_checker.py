import streamlit as st
import pandas as pd
from edgar import Company, set_identity
import io
from edgar.exceptions import EdgarFileNotFoundException  # Import the exception

# 1. Configuration
set_identity("suren.surya@msci.com")  # **IMPORTANT: REPLACE WITH YOUR EMAIL**
TARGET_YEAR = 2024
DEFAULT_COMPANY_NAME = "Unknown"

# 2. Helper Function
def process_company(cik, issuer_id="Unknown", analyst_name="Unknown"):
    """Processes a single company and returns the result, fetching company name from Edgar."""
    try:
        company = Company(str(cik))
        company_name = company.name  # Get the company name from Edgar
        filings = company.get_filings(form="8-K")
        form_507_found = False
        form_507_link = None

        for filing in filings:
            try:
                if hasattr(filing, 'items') and '5.07' in filing.items:
                    if hasattr(filing, 'filing_date'):
                        filing_year = filing.filing_date.year
                        if filing_year == TARGET_YEAR:
                            form_507_found = True
                            accession_number = filing.accession_number.replace('-', '')
                            form_507_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/index.html"
                            break
            except Exception as e:
                print(f"  Error processing filing: {e}")

        if form_507_found:
            return {
                "CIK": cik,
                "Company Name": company_name,
                "Issuer ID": issuer_id,
                "Analyst Name": analyst_name,
                "Form_5.07_Available": "Yes",
                "Form_5.07_Link": form_507_link
            }
        else:
            return {
                "CIK": cik,
                "Company Name": company_name,
                "Issuer ID": issuer_id,
                "Analyst Name": analyst_name,
                "Form_5.07_Available": "No",
                "Form_5.07_Link": f"https://www.sec.gov/Archives/edgar/data/{cik}/NotFound.htm"
            }

    except EdgarFileNotFoundException as e:  # Catch specific Edgar exception
        st.error(f"Company with CIK {cik} not found on EDGAR.") # Display error in Streamlit
        return {
            "CIK": cik,
            "Company Name": "Not Found",
            "Issuer ID": issuer_id,
            "Analyst Name": analyst_name,
            "Form_5.07_Available": "Not Found",
            "Form_5.07_Link": None
        }

    except Exception as e:
        print(f"  Error processing company: {e}")
        return {
            "CIK": cik,
            "Company Name": "Error",
            "Issuer ID": issuer_id,
            "Analyst Name": analyst_name,
            "Form_5.07_Available": "Error",
            "Form_5.07_Link": None
        }


# 3. Streamlit UI
st.title("SEC Form 5.07 Checker")

# Input Method Selection
input_method = st.radio("Select Input Method:", ("Manual CIK Input", "Upload Excel File"))

# 4. Manual CIK Input
if input_method == "Manual CIK Input":
    ciks_input = st.text_area("Enter CIK(s) (comma-separated):", "")

    if st.button("Process CIK(s)"):
        ciks = [cik.strip() for cik in ciks_input.split(',') if cik.strip()]

        if not ciks:
            st.warning("Please enter at least one CIK number.")
        else:
            results = []
            with st.spinner("Processing..."):  # Show a spinner
                for cik in ciks:
                    results.append(process_company(cik)) # Company name now fetched from Edgar

            df = pd.DataFrame(results)
            st.dataframe(df)  # Display results in a table

            # Download Button
            excel_file = io.BytesIO()
            df.to_excel(excel_file, index=False)
            excel_file.seek(0)

            st.download_button(
                label="Download Excel File",
                data=excel_file.read(),
                file_name="sec_form_507_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


# 5. Excel File Upload
elif input_method == "Upload Excel File":
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.str.strip()

            results = []
            with st.spinner("Processing..."): # Show a spinner
                for index, row in df.iterrows():
                    cik = row.get('CIK', None)
                    # Company name is now fetched from Edgar, so we don't need to get it from the file
                    issuer_id = row.get('Issuer id', 'Unknown')
                    analyst_name = row.get('Analyst name', 'Unknown')

                    if cik is None:
                        results.append({
                            "CIK": "Unknown",
                            "Company Name": "No CIK Found",
                            "Issuer ID": issuer_id,
                            "Analyst Name": analyst_name,
                            "Form_5.07_Available": "No CIK Found",
                            "Form_5.07_Link": "Not Available"
                        })
                        continue
                    results.append(process_company(cik, issuer_id, analyst_name))

            df_results = pd.DataFrame(results)  # Convert results to DataFrame

            st.dataframe(df_results)  # Display the DataFrame

            # Download Button
            excel_file = io.BytesIO()
            df_results.to_excel(excel_file, index=False)
            excel_file.seek(0)

            st.download_button(
                label="Download Excel File",
                data=excel_file.read(),
                file_name="sec_form_507_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


        except Exception as e:
            st.error(f"Error processing file: {e}")
