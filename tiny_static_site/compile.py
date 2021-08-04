import os
import sys
from os import path
import json

import jinja2
from bs4 import BeautifulSoup

from .utils import get_url_for_func, get_assets_url_for_func, get_image_url_for_func
from .utils import get_build_title_func, get_base_domain
from .utils import is_active_route
from .utils import get_parse_url_filter
from .utils import get_meta_data, copy_meta_files, copy_assets, unzip_assets

assert sys.version_info >= (3, 8)
debug = False


def run():
    if 'debug' in sys.argv:
        global debug
        debug = True

    source_dir = 'source'
    compiled_dir = 'compiled'
    os.makedirs(compiled_dir, exist_ok=True)
    meta_data = get_meta_data(source_dir)
    print('baseurl', meta_data['baseurl'])
    copy_meta_files(source_dir, compiled_dir, meta_data['branch'])

    base_path = path.abspath(compiled_dir)
    assets_url = os.path.join(meta_data['baseurl'], 'assets')
    assets_dir = os.path.join(base_path, 'assets')
    content_dir = path.join(source_dir, 'content')
    templates_dir = path.join(source_dir, 'templates')

    if 'sass' in sys.argv:
        from .compile_sass import compile_sass
        compile_sass(sass_file=meta_data['sass_file'])

    meta_data['assets_dir'] = assets_dir
    content = collect_content(content_dir)
    print('routes', content.keys())
    url_for_func = get_url_for_func(meta_data['baseurl'], content, add_index_html=meta_data['add_index_html'])
    image_url_for_func, thumbnail_paths = get_image_url_for_func(assets_url)

    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=templates_dir))
    jinja_env.globals.update(url_for=url_for_func)
    jinja_env.globals.update(assets_url_for=get_assets_url_for_func(assets_url))
    jinja_env.globals.update(image_url_for=image_url_for_func)
    jinja_env.globals.update(is_active_route=is_active_route)
    jinja_env.globals.update(build_title=get_build_title_func(meta_data))
    jinja_env.globals.update(get_base_domain=get_base_domain)
    jinja_env.filters['parse_url'] = get_parse_url_filter(assets_url)
    templates = jinja_env

    for route, data in content.items():
        if data.get('no_render', False):
            continue
        meta_data['active_route'] = route
        render_page(compiled_dir, templates, meta_data, route, data)

    if 'thumb' in sys.argv:
        from .compile_thumbnails import create_thumbnails
        create_thumbnails(source_assets_dir=os.path.join(source_dir, 'assets'),
                          thumbnail_paths=thumbnail_paths,
                          size=meta_data['thumbnail_size'])

    copy_assets(source_dir=source_dir,
                content_dir=content_dir,
                assets_dir=assets_dir,
                content=content,
                skip_assets=meta_data['skip_assets'] if 'skip_copy' in sys.argv else None)
    unzip_assets(assets_dir, meta_data['unzip_assets'])


def collect_content(content_dir):
    content = dict()
    for route in os.listdir(content_dir):
        if not os.path.isdir(path.join(content_dir, route)):
            continue
        page_data_file = path.join(content_dir, route, 'page.json')
        with open(page_data_file) as f:
            page = json.load(f)
        page['route_origin'] = route
        assert 'title' in page  # origin pages need titles
        _collect_content(page, route, content, content_dir)
    return content


def _collect_content(page, route, content, content_dir):
    assert 'template' in page or page.get('no_render', False)  # pages need template or is no_render
    if debug:
        print('collect content for route: {}'.format(route))
    if 'data_json' in page:
        data_json_file = os.path.join(content_dir, page['route_origin'], 'data', page['data_json'])
        with open(data_json_file) as f:
            data_json = json.load(f)
        if 'data' in page:
            data_json.update(page['data'])
        page['data'] = data_json

    page['route'] = route

    if 'tabs' in page:
        tabs = list()
        for tab in page['tabs']:
            tab['route'] = os.path.join(route, tab['route'])
            tab['parent'] = page
            tab['template'] = page['tabs_template']
            tabs.append(tab)
            content[tab['route']] = tab
        page['tabs'] = tabs

    content[route] = page
    for loop_index, item in enumerate(page.get('items', []), start=1):
        item['loop_index'] = loop_index

        if not item.get('no_render', False):
            item['template'] = _get_item_template(page, item)

        item['title'] = _get_item_title(page, item)

        item['route'] = _get_item_route(page, item)
        item_route = os.path.join(route, item['route'])

        item['route_origin'] = page['route_origin']
        item['parent'] = page
        _collect_content(page=item, route=item_route, content=content, content_dir=content_dir)


def _get_item_template(page, item):
    if 'template' not in item:
        if 'items_template' not in page:
            raise ValueError('item needs a template or parent needs a items_template attribute')
        else:
            template = page['items_template']
    else:
        template = item['template']
    return template


def _get_item_route(page, item):
    loop_index = item['loop_index']
    if 'route' not in item:
        if 'items_route' in page:
            items_route = page['items_route']
        else:
            items_route = '{loop_index}'
        route = items_route
    else:
        route = item['route']
    return route.format(loop_index=loop_index)


def _get_item_title(page, item):
    loop_index = item['loop_index']
    if 'title' not in item:
        if 'items_title' in page:
            items_title = page['items_title']
        else:
            items_title = '{loop_index}'
        title = items_title
    else:
        title = item['title']
    return title.format(loop_index=loop_index)


def render_page(output_dir, templates, meta_data, route, data):
    template = templates.get_template(data['template'])

    if meta_data['start_page'] == route:
        render_html(output_dir, '', template, data, meta_data)

    render_html(output_dir, route, template, data, meta_data)


def render_html(output_dir, route, template, page_data, meta_data):
    output_dir = path.join(output_dir, route)
    os.makedirs(output_dir, exist_ok=True)
    output_file = path.join(output_dir, 'index.html')
    data = dict(meta=meta_data, page=page_data)
    html = template.render(data)
    soup = BeautifulSoup(html, features="html.parser")
    pretty_html = soup.prettify()
    with open(output_file, 'w') as f:
        f.write(pretty_html)
    print(output_file)
