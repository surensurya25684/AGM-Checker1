import requests
from bs4 import BeautifulSoup

def check_form_507_scraping(cik):  #Removed the need of User Email since this has no API calls
    cik = str(cik).zfill(10)
    base_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=8-K&dateb=&owner=exclude&count=100" #Look for 8k and filter from that

    try:
        response = requests.get(base_url, timeout=10)
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
                            return {"Form_5.07_Available": "Yes", "Form_5.07_Link":document_url}
        return {"Form_5.07_Available": "No", "Form_5.07_Link": 'N/A'}
    except requests.exceptions.RequestException as e:
        print(f"Scraping error: {e}")
        return {"Form_5.07_Available": "Error", "Form_5.07_Link": None}
