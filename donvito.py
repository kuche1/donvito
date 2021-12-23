#!/usr/bin/env python3

import requests
import tempfile
import subprocess
import shlex
import sys
import re

import bs4


BASE_URL = 'https://pizzadonvito.com/'
PAGE_URL = BASE_URL + '/bg/page/indexdetails@menu_id=15&page_num={}'
FIRST_PAGE = PAGE_URL.format(1)


class Pizza:
    def __init__(s, name, ings, weight, size, price, image_link):
        s.name = name
        s.ings = ings
        s.weight = weight
        s.size = size
        s.price = price
        s.value = weight / price
        s.image_link = image_link

        s.image_cached = False
        s.image_path = None

    def __repr__(s):
        return f'''{s.value} -> {s.name}
\t{s.size=}
\t{s.ings=}
\t{s.weight=}
\t{s.price=}
\t{s.image_link=}
'''

    def contains(s, ing):
        return ing in s.ings

    def show_info(s):
        print(s)

    def show_image(s):
        if not s.image_cached:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(get_response(s.image_link))
                s.image_path = f.name
        display_image(s.image_path)
    

def display_image(path):
    # viu icat
    DISPLAY_PROGRAM = 'viu'
    ret_code = subprocess.call(shlex.join([DISPLAY_PROGRAM, path]), shell=True)
    if ret_code != 0:
        try:
            subprocess.call(shlex.join([DISPLAY_PROGRAM, '--version']))
        except FileNotFoundError:
            print(f'program not found: {DISPLAY_PROGRAM}')
            print("please install, possible solutions:")
            print(f"\tsudo pacman -S --needed {DISPLAY_PROGRAM}")
            print(f"\tsudo apt install {DISPLAY_PROGRAM}")
            sys.exit(1)
        raise Exception("this should never happen")

get_response_cache = {}
def get_response(url):
    if url in get_response_cache:
        return get_response_cache[url]
    page = requests.get(url)
    assert page.ok
    content = page.content
    get_response_cache[url] = content
    return content

def get_number_of_pages(url):
    resp = get_response(url)
    soup = bs4.BeautifulSoup(resp, "lxml")
    pages = soup.find(class_='pagination')
    pages = pages.text.split('\n')
    while '' in pages: pages.remove('')
    assert pages[0] == '«'
    pages = pages[1:]
    assert pages[-1] == '»'
    pages = pages[:-1]

    page_num = int(pages[-1])
    return page_num


def main():

    pages = get_number_of_pages(FIRST_PAGE)
    print(f'Pages: {pages}')
    print()

    all_pizzas = []

    for page_num in range(1, pages+1):

        page = get_response(PAGE_URL.format(page_num))
    
        soup = bs4.BeautifulSoup(page, "lxml")

        #pizzas = soup.find_all(class_='product-box-info')
        pizzas = soup.find_all(class_='product-box clearfloat')

        for pizza_ind, pizza in enumerate(pizzas):
            image = pizza.find(class_='product-box-image').img.get('src')
            image_link = BASE_URL + image
        
            name = pizza.find(class_='product-box-title').text.strip()

            snw = pizza.find(class_='p-size').text
            #assert re.findall(r'^\d+ кг. \d+ см.:$', snw) != []
            weight, size = re.findall(r'\d+', snw) # TODO make this robust
            weight = float(weight)
            size = float(size)
            assert weight == 2
            assert size == 60

            price = pizza.find(class_='product-price').text.strip()
            price = re.findall(r'\d+\.\d+', price)
            assert len(price) == 1
            price = float(price[0])

            ings = pizza.find(class_='text').text

            pizzas[pizza_ind] = Pizza(name, ings, weight, size, price, image_link)

        all_pizzas.extend(pizzas)

    pizzas = all_pizzas

    pizzas.sort(reverse=True, key=lambda p:p.value)

    ind = 0
    ind_change = 1
    while True:
        pizza = pizzas[ind]

        pizza.show_info()
        pizza.show_image()

        com = input()
        if com == 'n':
            ind += 1
            if ind >= len(pizzas):
                ind = len(pizzas) - 1
        elif com == 'p':
            ind -= 1
            if ind < 0:
                ind = 0
        elif com == 's':
            ind = 0
        else:
            print(f'unknown command: {com}')

main()
