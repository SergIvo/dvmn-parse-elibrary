import json
import os
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def render_template(env, cards, output_file_path):
    template = env.get_template('template.html')
    rendered_page = template.render(book_cards=cards)

    with open(output_file_path, 'w', encoding="utf8") as file:
        file.write(rendered_page)


def process_book_cards(media_directory):
    with open(os.path.join(media_directory, 'books.json'), 'r') as json_file:
        books_details = json.load(json_file)

    relative_media_dir = os.path.join('..', media_directory)
    for book in books_details:
        image_real_name = ''.join(book['image_relative_url'].split('/'))
        image_path = os.path.join(relative_media_dir, 'images', image_real_name)
        book['image_relative_url'] = quote(image_path)

        text_real_name = f"{books_details.index(book)}. {book['title']}.txt"
        text_path = os.path.join(relative_media_dir, 'books', text_real_name)
        book['text_relative_url'] = quote(text_path)

    return books_details


def on_reload():
    os.makedirs('pages', exist_ok=True)

    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    media_directory = 'media'
    book_cards = process_book_cards(media_directory)
    paginated_book_cards = list(chunked(book_cards, 20))

    page_base_path = 'pages/index{}.html'
    for page_number, one_page_cards in enumerate(paginated_book_cards):
        book_card_pairs = list(chunked(one_page_cards, 2))
        render_template(env, book_card_pairs, page_base_path.format(page_number + 1))


if __name__ == '__main__':
    on_reload()

    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root='./pages')
