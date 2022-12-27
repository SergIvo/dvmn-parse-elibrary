from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def main():
    base_url = 'https://tululu.org/l55/'
    response = requests.get(base_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    book_url_tag = soup.find('table', attrs={'class': 'd_book'}).find('a')
    relative_book_url = book_url_tag['href']

    book_url = urljoin(base_url, relative_book_url)
    print(book_url)


if __name__ == '__main__':
    main()
