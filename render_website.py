import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

from jinja2 import Environment, FileSystemLoader, select_autoescape

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

rendered_page = template.render(
    book_cards=books_details
)

with open('index.html', 'w', encoding="utf8") as file:
    file.write(rendered_page)

server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
server.serve_forever()