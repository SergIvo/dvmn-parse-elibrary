import os

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.history:
        print(response.url, response.history)
        raise requests.HTTPError


def download_text(url, params=None):
    if params:
        response = requests.get(url, params=params)
    else:
        response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response.text


def download_file(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def get_title_and_author(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    author_and_title_tag = soup.find('div', attrs={'id': 'content'}).find('h1')
    title, _ = author_and_title_tag.text.split('::')
    title = title.strip()
    author = author_and_title_tag.a.text
    print(author, title)


def download_txt(url, filename, folder='books'):
    text = download_text(url)
    safe_filename = sanitize_filename(filename)
    filepath = os.path.join(folder, f'{safe_filename}.txt')
    with open(filepath, 'w') as file:
        file.write(text)
    return filepath


def main():
    books_dir = 'books'
    os.makedirs(books_dir, exist_ok=True)

    base_url = "https://tululu.org/txt.php"
    for book_id in range(1, 11):
        params = {'id': book_id}
        try:
            text = download_text(base_url, params)
            book_path = os.path.join(books_dir, f'id{book_id}.txt')
            with open(book_path, 'w') as file:
                file.write(text)
        except requests.HTTPError:
            print("Requested book doesn't exist.")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    url = 'https://tululu.org/txt.php?id=1'
    filepath = download_txt(url, 'Али/би', folder='books\\')
    print(filepath)
    filepath = download_txt(url, 'Али\\би', folder='txt\\')
    print(filepath)

