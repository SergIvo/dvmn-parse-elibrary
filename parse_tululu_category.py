import os
import json
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
    book_tags = soup.select('.d_book')
    book_urls = []

    for tag in book_tags:
        relative_book_url = tag.select_one('a')['href']
        book_url = urljoin(page_url, relative_book_url)
        book_urls.append(book_url)

    return book_urls


def save_txt(text, filename, folder='books'):
    safe_filename = sanitize_filename(filename)
    filepath = os.path.join(folder, f'{safe_filename}.txt')
    with open(filepath, 'w') as file:
        file.write(text)
    return filepath


def parse_book_page(page_html):
    soup = BeautifulSoup(page_html, 'lxml')

    image_tag = soup.select_one('.bookimage img')
    image_relative_url = image_tag['src']

    comments_tags = soup.select('.texts')
    comments = [tag.span.text for tag in comments_tags]

    genre_tags = soup.select('span.d_book a')
    genres = [tag.text for tag in genre_tags]

    author_and_title_tag = soup.select_one("div[id='content'] h1")
    title, _ = author_and_title_tag.text.split('::')

    text_url_selector = ".d_book a[title*='скачать книгу txt']"
    text_url_tag = soup.select_one(text_url_selector)
    if text_url_tag:
        text_relative_url = text_url_tag['href']
    else:
        text_relative_url = None

    book_details = {
        'title': title.strip(),
        'author': author_and_title_tag.a.text,
        'image_relative_url': image_relative_url,
        'comments': comments,
        'genres': genres,
        'text_relative_url': text_relative_url
    }
    return book_details


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
    for page_number in range(1, 2):
        page_url = base_url.format(page_number)
        url_from_page = parse_urls_from_page(page_url)
        book_urls.extend(url_from_page)

    books_json = []
    for i, book_url in enumerate(book_urls):
        try:
            book_page_response = ensure_request(book_url)
        except requests.HTTPError:
            print(f'Описание книги по ссылке {book_url} не доступно.')
            continue

        book_details = parse_book_page(book_page_response.text)

        if not book_details['text_relative_url']:
            print(f'Текст книги по ссылке {book_url} не доступен.')
            continue

        text_url = urljoin(book_url, book_details['text_relative_url'])
        filename = f"{i}. {book_details['title']}"
        try:
            text_response = ensure_request(text_url)
            save_txt(text_response.text, filename, books_dir)
        except requests.HTTPError:
            print(f'Текст книги по ссылке {book_url} не доступен.')
            continue

        image_url = urljoin(book_url, book_details['image_relative_url'])
        try:
            download_image(image_url, images_dir)
        except requests.HTTPError:
            print(f'Обложка книги по ссылке {book_url} не доступна.')

        books_json.append(book_details)

    with open('books.json', 'w') as json_file:
        json.dump(books_json, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
