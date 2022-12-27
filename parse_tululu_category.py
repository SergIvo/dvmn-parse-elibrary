from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup





def main():
    base_url = 'https://tululu.org/l55/'
    response = requests.get(base_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    book_tags = soup.find_all('table', attrs={'class': 'd_book'})

    book_urls = []
    for tag in book_tags:
        relative_book_url = tag.find('a')['href']
        book_url = urljoin(base_url, relative_book_url)
        print(book_url)

        book_urls.append(book_url)

    print(len(book_urls))


if __name__ == '__main__':
    main()
