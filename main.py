import requests


def download_text(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def download_file(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    url = "https://tululu.org/txt.php?id=32168"
    text = download_text(url)
    with open('book.txt', 'w') as file:
        file.write(text)


