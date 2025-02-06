import streamlit as st
import pandas as pd
from edgar import Company, set_identity

# Set identity for SEC API requests
set_identity("suren.surya@msci.com")  # Replace with your email

# Streamlit UI Layout
st.title("SEC Form 5.07 Checker")
st.write("Check if a company has filed Form 5.07 under 8-K filings.")

# File Upload Option
uploaded_file = st.file_uploader("Upload an Excel file (must contain a 'CIK' column)", type=["xlsx"])

# Manual CIK Input
manual_cik = st.text_input("Or enter a CIK number manually:")

# Button to Process Data
if st.button("Check Filings"):
    results = []
    
    if uploaded_file:
        # Load Data from Uploaded File
        companies_df = pd.read_excel(uploaded_file)

        # Strip whitespace from column names
        companies_df.columns = companies_df.columns.str.strip()

        # Check if 'CIK' column exists
        if 'CIK' not in companies_df.columns:
            st.error("Uploaded file must contain a 'CIK' column.")
        else:
            st.write("Processing file...")

            # Iterate through each company
            for index, row in companies_df.iterrows():
                cik = row.get('CIK', None)
                company_name = row.get('Company Name', 'Unknown')
                issuer_id = row.get('Issuer id', 'Unknown')
                analyst_name = row.get('Analyst name', 'Unknown')

                if cik:
                    try:
                        company = Company(str(cik))
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

                        # Store results
                        results.append({
                            "CIK": cik,
                            "Company Name": company_name,
                            "Issuer ID": issuer_id,
                            "Analyst Name": analyst_name,
                            "Form_5.07_Available": "Yes" if form_507_found else "No",
                            "Form_5.07_Link": form_507_link if form_507_found else f"https://www.sec.gov/Archives/edgar/data/{cik}/NotFound.htm"
                        })

                    except Exception as e:
                        st.error(f"Error processing CIK {cik}: {e}")
                        results.append({
                            "CIK": cik,
                            "Company Name": company_name,
                            "Issuer ID": issuer_id,
                            "Analyst Name": analyst_name,
                            "Form_5.07_Available": "Error",
                            "Form_5.07_Link": None
                        })

            # Display Results
            if results:
                results_df = pd.DataFrame(results)
                st.dataframe(results_df)

                # Provide option to download results
                output_file = "output_results.xlsx"
                results_df.to_excel(output_file, index=False)
                st.download_button("Download Results as Excel", data=open(output_file, "rb"), file_name="output_results.xlsx")

    elif manual_cik:
        try:
            st.write(f"Processing CIK: {manual_cik}")

            company = Company(str(manual_cik))
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
                                form_507_link = f"https://www.sec.gov/Archives/edgar/data/{manual_cik}/{formatted_accession_number}/index.html"
                                break
                except Exception as e:
                    st.warning(f"Error processing filing for CIK {manual_cik}: {e}")

            # Show result for manual input
            result = {
                "CIK": manual_cik,
                "Form_5.07_Available": "Yes" if form_507_found else "No",
                "Form_5.07_Link": form_507_link if form_507_found else f"https://www.sec.gov/Archives/edgar/data/{manual_cik}/NotFound.htm"
            }
            st.write(result)

        except Exception as e:
            st.error(f"Error processing CIK {manual_cik}: {e}")

    else:
        st.warning("Please upload a file or enter a CIK number.")
