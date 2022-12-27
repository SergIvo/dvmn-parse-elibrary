from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def parse_urls_from_page(page_url):
    response = requests.get(page_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    book_tags = soup.find_all('table', attrs={'class': 'd_book'})

    book_urls = []
    for tag in book_tags:
        relative_book_url = tag.find('a')['href']
        book_url = urljoin(page_url, relative_book_url)
        print(book_url)

        book_urls.append(book_url)

    return book_urls


def main():
    base_url = 'https://tululu.org/l55/{}/'

    book_urls = []
    for page_number in range(1, 11):
        page_url = base_url.format(page_number)
        url_from_page = parse_urls_from_page(page_url)

        book_urls.extend(url_from_page)

    print(len(book_urls))


if __name__ == '__main__':
    main()
