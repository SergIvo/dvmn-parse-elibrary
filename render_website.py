import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    media_directory = 'media'
    with open(os.path.join(media_directory, 'books.json'), 'r') as json_file:
        books_details = json.load(json_file)

    for book in books_details:
        image_real_name = ''.join(book['image_relative_url'].split('/'))
        image_path = os.path.join(media_directory, 'images', image_real_name)
        book['image_relative_url'] = image_path

    template = env.get_template('template.html')
    rendered_page = template.render(book_cards=books_details)

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


if __name__ == '__main__':
    on_reload()

    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root='.')
