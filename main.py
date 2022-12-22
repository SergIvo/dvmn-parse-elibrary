import os
from urllib.parse import urljoin, urlsplit, unquote
from argparse import ArgumentParser

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_text(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response.text


def download_file(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def parse_book_page(page_html):
    soup = BeautifulSoup(page_html, 'lxml')
    book_details = dict()

    author_and_title_tag = soup.find('div', attrs={'id': 'content'}).find('h1')
    title, _ = author_and_title_tag.text.split('::')
    book_details['title'] = title.strip()
    book_details['author'] = author_and_title_tag.a.text

    image_tag = soup.find('div', attrs={'class': 'bookimage'}).find('img')
    image_relative_url = image_tag['src']
    base_url = 'https://tululu.org/'
    book_details['image_url'] = urljoin(base_url, image_relative_url)

    comments_tags = soup.find_all('div', attrs={'class': 'texts'})
    book_details['comments'] = [tag.span.text for tag in comments_tags]

    genre_tags = soup.find('span', attrs={'class': 'd_book'}).find_all('a')
    book_details['genres'] = [tag.text for tag in genre_tags]
    return book_details


def download_txt(url, filename, folder='books'):
    text = download_text(url)
    safe_filename = sanitize_filename(filename)
    filepath = os.path.join(folder, f'{safe_filename}.txt')
    with open(filepath, 'w') as file:
        file.write(text)
    return filepath


def download_image(url, folder='images'):
    image = download_file(url)
    url_parts = urlsplit(url)
    filename = unquote(url_parts.path)
    safe_filename = sanitize_filename(filename)
    filepath = os.path.join(folder, safe_filename)
    if not os.path.exists(filepath):
        with open(filepath, 'wb') as file:
            file.write(image)
    return filepath


def main(start_id, end_id):
    books_dir = 'books'
    os.makedirs(books_dir, exist_ok=True)
    images_dir = 'images'
    os.makedirs(images_dir, exist_ok=True)

    base_book_url = 'https://tululu.org/b{}/'
    base_text_url = 'https://tululu.org/txt.php?id={}'
    for book_id in range(start_id, end_id):
        try:
            book_url = base_book_url.format(book_id)
            book_page_html = download_text(book_url)
        except requests.HTTPError:
            print(f'Описание книги {book_id} не доступно.')
            continue

        book_details = parse_book_page(book_page_html)
        filename = f"{book_id}. {book_details['title']}"

        try:
            text_url = base_text_url.format(book_id)
            download_txt(text_url, filename, books_dir)
        except requests.HTTPError:
            print(f'Текст книги {book_id} не доступен.')
            continue

        download_image(book_details['image_url'], images_dir)
        print(f"Название: {book_details['title']} \nАвтор: {book_details['author']}")


if __name__ == '__main__':
    parser = ArgumentParser(description='Программа скачивает книги с сайта tululu.org в указанном интервале')
    parser.add_argument('-s', '--start_id', help='ID книги, с которой начнется скачивание', type=int, default=1)
    parser.add_argument('-e', '--end_id', help='ID книги, на которой закончится скачивание', type=int, default=11)
    args = parser.parse_args()

    main(args.start_id, args.end_id)
