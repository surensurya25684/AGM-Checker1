def fetch_filings(cik, user_email):
    """Fetch 8-K filings and scan for Form 5.07 using SEC API and HTML parsing"""
    headers = {"User-Agent": user_email}
    cik = str(cik).zfill(10)  # Ensure CIK is 10 digits
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
                    
                    # Attempt to fetch primary document
                    filing_html_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{formatted_accession_number}/primary-document.html"
                    
                    try:
                        filing_html_response = requests.get(filing_html_url, headers=headers, timeout=10)
                        filing_html_response.raise_for_status()  # Raise error if not found
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 404:
                            st.warning(f"Warning: Primary document not found for CIK {cik}, accession number {formatted_accession_number}. Checking index page instead.")
                        else:
                            st.warning(f"Warning: Error fetching filing HTML for CIK {cik}, accession number {formatted_accession_number}: {e}")
                            continue
                    
                    # If we successfully fetched the primary document
                    if filing_html_response.status_code == 200:
                        soup = BeautifulSoup(filing_html_response.text, "html.parser")
                        filing_text = soup.get_text().lower()

                        if re.search(r"\bitem\s*5\.07\b", filing_text):
                            form_507_link = filing_url
                            form_507_found = True
                            break  # Stop once we find the first 5.07 filing

                    # If primary document was not found, we could check the index page here if needed

                time.sleep(0.1)  # Small delay to avoid rate limiting

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
