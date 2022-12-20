import requests
import os


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_text(url, params):
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response)
    return response.text


def download_file(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content


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
    main()
