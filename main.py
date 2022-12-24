import os
from urllib.parse import urljoin, urlsplit, unquote
from argparse import ArgumentParser
from time import sleep

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def get_text_from_url(url, params=None):
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
    return response.text


def parse_book_page(page_html):
    soup = BeautifulSoup(page_html, 'lxml')

    image_tag = soup.find('div', attrs={'class': 'bookimage'}).find('img')
    image_relative_url = image_tag['src']

    comments_tags = soup.find_all('div', attrs={'class': 'texts'})
    comments = [tag.span.text for tag in comments_tags]

    genre_tags = soup.find('span', attrs={'class': 'd_book'}).find_all('a')
    genres = [tag.text for tag in genre_tags]

    author_and_title_tag = soup.find('div', attrs={'id': 'content'}).find('h1')
    title, _ = author_and_title_tag.text.split('::')

    book_details = {
        'title': title.strip(),
        'author': author_and_title_tag.a.text,
        'image_relative_url': image_relative_url,
        'comments': comments,
        'genres': genres,
    }
    return book_details


def save_txt(text, filename, folder='books'):
    safe_filename = sanitize_filename(filename)
    filepath = os.path.join(folder, f'{safe_filename}.txt')
    with open(filepath, 'w') as file:
        file.write(text)
    return filepath


def download_image(url, folder='images'):
    response = None
    reconnect_delay = 0
    while not response:
        try:
            response = requests.get(url)
        except requests.exceptions.ConnectionError:
            sleep(reconnect_delay)
            reconnect_delay = 10

    response.raise_for_status()
    check_for_redirect(response)
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
    parser = ArgumentParser(description='Программа скачивает книги с сайта tululu.org в указанном интервале')
    parser.add_argument('-s', '--start_id', help='ID книги, с которой начнется скачивание', type=int, default=1)
    parser.add_argument('-e', '--end_id', help='ID книги, на которой закончится скачивание', type=int, default=10)
    args = parser.parse_args()

    books_dir = 'books'
    os.makedirs(books_dir, exist_ok=True)
    images_dir = 'images'
    os.makedirs(images_dir, exist_ok=True)

    base_book_url = 'https://tululu.org/b{}/'
    base_text_url = 'https://tululu.org/txt.php'

    for book_id in range(args.start_id, args.end_id + 1):
        book_url = base_book_url.format(book_id)
        try:
            book_page_html = get_text_from_url(book_url)
        except requests.HTTPError:
            print(f'Описание книги {book_id} не доступно.')
            continue

        book_details = parse_book_page(book_page_html)
        filename = f"{book_id}. {book_details['title']}"

        text_url_params = {'id': book_id}
        try:
            text = get_text_from_url(base_text_url, text_url_params)
            save_txt(text, filename, books_dir)
        except requests.HTTPError:
            print(f'Текст книги {book_id} не доступен.')
            continue

        image_url = urljoin(book_url, book_details['image_relative_url'])
        print(image_url)
        try:
            download_image(image_url, images_dir)
        except requests.HTTPError:
            print(f'Обложка книги {book_id} не доступна.')
        print(f"Название: {book_details['title']} \nАвтор: {book_details['author']}")


if __name__ == '__main__':
    main()
