import requests
import os


def download_text(url, params):
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.text


def download_file(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    books_dir = 'books'
    os.makedirs(books_dir, exist_ok=True)

    base_url = "https://tululu.org/txt.php"
    for book_id in range(0, 10):
        params = {'id': book_id}
        book_path = os.path.join(books_dir, f'id{book_id}.txt')
        text = download_text(base_url, params)
        with open(book_path, 'w') as file:
            file.write(text)


