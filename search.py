import requests

SEARCH_API_KEY = open('SEARCH_API_KEY').read()
SEARCH_ENGINE_ID = open('SEARCH_ENGINE_ID').read()

tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'SMSN', 'TCEHY', 'NVDA', 'ADBE']
links = []

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
        links.append(results['items'][0]['link'])

print(links)
