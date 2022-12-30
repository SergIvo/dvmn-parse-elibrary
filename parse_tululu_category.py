import os
import json
from urllib.parse import urljoin, urlsplit, unquote
from time import sleep
from argparse import ArgumentParser

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


def parse_urls_from_page(html, page_url):
    soup = BeautifulSoup(html, 'lxml')
    book_tags = soup.select('.d_book')
    book_urls = []

    for tag in book_tags:
        relative_book_url = tag.select_one('a')['href']
        book_url = urljoin(page_url, relative_book_url)
        book_urls.append(book_url)

    return book_urls


def parse_last_page_number(html):
    soup = BeautifulSoup(html, 'lxml')
    pagination_tags = soup.select("[class*='npage']")
    last_page = pagination_tags[-1].text
    return int(last_page)


def parse_all_book_urls(start_page, end_page):
    base_url = 'https://tululu.org/l55/{}/'
    book_urls = []
    if not end_page:
        response = ensure_request(base_url.format(1))
        end_page = parse_last_page_number(response.text) + 1

    for page_number in range(start_page, end_page):
        page_url = base_url.format(page_number)
        try:
            response = ensure_request(page_url)
        except requests.HTTPError:
            continue
        url_from_page = parse_urls_from_page(response.text, page_url)
        book_urls.extend(url_from_page)

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


def get_command_line_args():
    parser = ArgumentParser(
        description='Программа скачивает книги с сайта tululu.org из раздела "Научная фантастика"'
    )
    parser.add_argument(
        '--start_page',
        help='Номер страницы, с которой начнется скачивание',
        type=int,
        default=1
    )
    parser.add_argument(
        '--end_page',
        help='Номер страницы, на которой закончится скачивание',
        type=int,
        default=None
    )
    parser.add_argument(
        '--dest_folder',
        help='Путь к каталогу с результатами парсинга',
        type=str,
        default=''
    )
    parser.add_argument(
        '--skip_imgs',
        help='Пропустить скачивание обложек книг',
        action='store_true'
    )
    parser.add_argument(
        '--skip_txt',
        help='Пропустить скачивание текстов книг',
        action='store_true'
    )
    parser.add_argument(
        '--json_path',
        help='Путь к .json-файлу с информацией о книгах',
        type=str,
        default=''
    )
    args = parser.parse_args()
    return args


def main():
    args = get_command_line_args()

    book_urls = parse_all_book_urls(args.start_page, args.end_page)

    books_details = []
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

        if not args.skip_txt:
            books_dir = os.path.join(args.dest_folder, 'books')
            os.makedirs(books_dir, exist_ok=True)

            text_url = urljoin(book_url, book_details['text_relative_url'])
            filename = f"{i}. {book_details['title']}"
            try:
                text_response = ensure_request(text_url)
                save_txt(text_response.text, filename, books_dir)
            except requests.HTTPError:
                print(f'Текст книги по ссылке {book_url} не доступен.')
                continue

        if not args.skip_imgs:
            images_dir = os.path.join(args.dest_folder, 'images')
            os.makedirs(images_dir, exist_ok=True)

            image_url = urljoin(book_url, book_details['image_relative_url'])
            try:
                download_image(image_url, images_dir)
            except requests.HTTPError:
                print(f'Обложка книги по ссылке {book_url} не доступна.')

        books_details.append(book_details)

    if args.json_path:
        os.makedirs(args.json_path, exist_ok=True)
        book_json_path = os.path.join(args.json_path, 'books.json')
    elif args.dest_folder:
        os.makedirs(args.dest_folder, exist_ok=True)
        book_json_path = os.path.join(args.dest_folder, 'books.json')
    else:
        book_json_path = 'books.json'
    with open(book_json_path, 'w') as json_file:
        json.dump(books_details, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
