import os
from urllib.parse import urljoin, urlsplit, unquote

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.history:
        print(response.url, response.history)
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


def get_title_and_author(page_html):
    soup = BeautifulSoup(page_html, 'lxml')
    author_and_title_tag = soup.find('div', attrs={'id': 'content'}).find('h1')
    title, _ = author_and_title_tag.text.split('::')
    title = title.strip()
    author = author_and_title_tag.a.text
    return title, author


def get_book_image_url(page_html):
    soup = BeautifulSoup(page_html, 'lxml')
    image_tag = soup.find('div', attrs={'class': 'bookimage'}).find('img')
    image_relative_url = image_tag['src']
    base_url = 'https://tululu.org/'
    return urljoin(base_url, image_relative_url)


def get_book_comments(page_html):
    soup = BeautifulSoup(page_html, 'lxml')
    comments_tags = soup.find_all('div', attrs={'class': 'texts'})
    comments_texts = [tag.span.text for tag in comments_tags]
    return comments_texts


def get_book_genre(page_html):
    soup = BeautifulSoup(page_html, 'lxml')
    genre_tags = soup.find('span', attrs={'class': 'd_book'}).find_all('a')
    genres = [tag.text for tag in genre_tags]
    return genres


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


def main():
    books_dir = 'books'
    os.makedirs(books_dir, exist_ok=True)
    images_dir = 'images'
    os.makedirs(images_dir, exist_ok=True)

    base_book_url = 'https://tululu.org/b{}/'
    base_text_url = 'https://tululu.org/txt.php?id={}'
    for book_id in range(1, 11):
        try:
            book_url = base_book_url.format(book_id)
            book_page_html = download_text(book_url)
        except requests.HTTPError:
            print("Requested book doesn't exist.")
            continue

        title, _ = get_title_and_author(book_page_html)
        filename = f'{book_id}. {title}'

        try:
            text_url = base_text_url.format(book_id)
            #download_txt(text_url, filename, books_dir)
        except requests.HTTPError:
            print("Requested book doesn't exist.")
            continue

        image_url = get_book_image_url(book_page_html)
        #download_image(image_url, images_dir)
        comments = get_book_comments(book_page_html)
        genres = get_book_genre(book_page_html)
        print(genres)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

