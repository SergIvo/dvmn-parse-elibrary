import os
from urllib.parse import urljoin, urlsplit, unquote
from time import sleep

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def ensure_request(url, params=None):
    response = None
    reconnect_delay = 0
    while not response:
        try:
            response = requests.get(url, params=params)
        except requests.exceptions.ConnectionError:
            sleep(reconnect_delay)
            reconnect_delay = 10

    response.raise_for_status()
    check_for_redirect(response)
    return response


def parse_urls_from_page(page_url):
    response = ensure_request(page_url)

    soup = BeautifulSoup(response.text, 'lxml')
    book_tags = soup.find_all('table', attrs={'class': 'd_book'})

    book_urls = []
    for tag in book_tags:
        relative_book_url = tag.find('a')['href']
        book_url = urljoin(page_url, relative_book_url)
        print(book_url)

        book_urls.append(book_url)

    return book_urls


def save_txt(text, filename, folder='books'):
    safe_filename = sanitize_filename(filename)
    filepath = os.path.join(folder, f'{safe_filename}.txt')
    with open(filepath, 'w') as file:
        file.write(text)
    return filepath


def download_image(url, folder='images'):
    response = ensure_request(url)
    image = response.content

    url_parts = urlsplit(url)
    filename = unquote(url_parts.path)
    safe_filename = sanitize_filename(filename)
    filepath = os.path.join(folder, safe_filename)
    if not os.path.exists(filepath):
        with open(filepath, 'wb') as file:
            file.write(image)
    return filepath


def main():
    books_dir = 'books'
    os.makedirs(books_dir, exist_ok=True)
    images_dir = 'images'
    os.makedirs(images_dir, exist_ok=True)

    base_url = 'https://tululu.org/l55/{}/'

    book_urls = []
    for page_number in range(1, 5):
        page_url = base_url.format(page_number)
        url_from_page = parse_urls_from_page(page_url)

        book_urls.extend(url_from_page)

    print(len(book_urls))


if __name__ == '__main__':
    main()
