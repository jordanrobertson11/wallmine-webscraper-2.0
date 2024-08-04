FREECURRENCY_API_KEY = open('FREECURRENCY_API_KEY').read()
SEARCH_API_KEY = open('SEARCH_API_KEY').read()
SEARCH_ENGINE_ID = open('SEARCH_ENGINE_ID').read()

import freecurrencyapi
client = freecurrencyapi.Client(FREECURRENCY_API_KEY)
print(client.status())
rates = client.latest()
print(rates)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def scrape_financials(ticker_links: list) -> pd.DataFrame:
    
    """
    Scrapes financial data for the given tickers from wallmine.com

    Args:
    ticker_links (list): Links for stock tickers.

    Returns:
    pd.DataFrame: DataFrame containing the scraped financial data.
    """
    
    data = {}

    for ticker in ticker_links:
        url = ticker
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        property_data = {}
        properties = [
            'revenue', 'yearly_revenue_growth', 'quarterly_revenue_growth', 'ebitda', 'ebitda_margin',
            'profit_margin', 'market_cap', 'enterprise_value', 'ev_sales', 'ev_ebitda', 'pe', 'shares_outstanding'
        ]
        
        # Scrape the data for each property in the properties list
        
        for prop in properties:
            values = soup.find('td', {'data-property': prop})
            property_values = values.get_text().strip() 
            property_data[prop] = property_values

        # Scrape the 52 week high
        
        yearly_high_element = soup.find_all('td', {'class': 'small text-mobile-small'})[1]
        fifty_two_week_high = yearly_high_element.get_text().strip()
        property_data['fifty_two_week_high'] = fifty_two_week_high

        # Scraping the price (price was contained within a script tag in the source)
        
        script_tag = soup.find('body')
        script = script_tag.find('script').get_text()

        # Regex to find the price in the script

        match = re.search(r'"price":\s*([\d.]+)', script) 
        if match:
            price = match.group(1) 
            
        # Extract the price
        
        property_data['share_price'] = price

        data[ticker] = property_data

    df = pd.DataFrame(data).T

    return df

####################################################################### USER INPUT ###################################################################

tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'SMSN', 'TCEHY', 'NVDA', 'ADBE']  # Add more tickers as needed
ticker_links = []

for ticker in tickers:
    search_query = 'wallmine ' + ticker

    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': search_query,
        'key': SEARCH_API_KEY,
        'cx': SEARCH_ENGINE_ID
    }

    response = requests.get(url, params=params)
    results = response.json()

    if 'items' in results:
        ticker_links.append(results['items'][0]['link'])

financial_data = scrape_financials(ticker_links)
fd = financial_data

####################################################################### FORMATTING ####################################################################

# Gets only the value after the hyphon from the fifty two week high column
fd['fifty_two_week_high'] = fd['fifty_two_week_high'].str.rsplit(' – ').str[1]

# Convert monetary values to USD (Billions), except for the share price which is in USD
def convert_currency(value):
    if 'B' in value:
        multiplier = 1
    elif 'T' in value:
        multiplier = 1000
    elif 'M' in value:
        multiplier = 0.001
    else:
        multiplier = 1

    if '₩' in value:
        return float(value.replace('₩', '').replace('B', '').replace('T', '').replace('M', '')) * multiplier / rates.get('data').get('KRW')
    elif '¥' in value:
        return float(value.replace('¥', '').replace('B', '').replace('T', '').replace('M', '')) * multiplier / rates.get('data').get('JPY')
    else:
        return float(value.replace('$', '').replace('B', '').replace('T', '').replace('M', '')) * multiplier

fd['revenue'] = fd['revenue'].apply(convert_currency)
fd['ebitda'] = fd['ebitda'].apply(convert_currency)
fd['market_cap'] = fd['market_cap'].apply(convert_currency)
fd['enterprise_value'] = fd['enterprise_value'].apply(convert_currency)
fd['shares_outstanding'] = fd['shares_outstanding'].apply(convert_currency)
fd['fifty_two_week_high'] = fd['fifty_two_week_high'].apply(lambda x: float(x.replace('$', '').replace(',', '')))

# Convert percentage values to decimals
def convert_percentage(value):
    return float(value.replace('%', '')) / 100

fd['yearly_revenue_growth'] = fd['yearly_revenue_growth'].apply(convert_percentage)
fd['quarterly_revenue_growth'] = fd['quarterly_revenue_growth'].apply(convert_percentage)
fd['ebitda_margin'] = fd['ebitda_margin'].apply(convert_percentage)
fd['profit_margin'] = fd['profit_margin'].apply(convert_percentage)

fd['ev_sales'] = fd['ev_sales'].astype('float')
fd['ev_ebitda'] = fd['ev_ebitda'].astype('float')
fd['pe'] = fd['pe'].astype('float')
fd['share_price'] = fd['share_price'].astype('float')

######################################################################## EXPORTING ####################################################################

# Export df to excel file

file_name = 'trading_comps_data.xlsx'

with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
    financial_data.to_excel(writer, sheet_name='Data')

print(f"DataFrames have been exported to {file_name}")