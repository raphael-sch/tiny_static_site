import json
import os
import hashlib
from shutil import copytree, copy2
from urllib.parse import urlparse

from jsmin import jsmin
from rcssmin import cssmin

def get_meta_data(source_dir):
    with open(os.path.join(source_dir, 'meta.json')) as f:
        meta_data = json.load(f)

    for key in ['baseurl', 'add_index_html', 'branch']:
        env_key = 'RP_' + key.upper()
        meta_data[key] = _maybe_get_env_boolean(os.getenv(env_key, meta_data[key]))
        print('data:', key, meta_data[key])

    for key in meta_data['data']:
        env_key = 'RP_DATA_' + key.upper()
        meta_data['data'][key] = _maybe_get_env_boolean(os.getenv(env_key, meta_data['data'][key]))
        print('meta data:', key, meta_data['data'][key])
    return meta_data


def copy_meta_files(source_dir, compiled_dir, branch):
    meta_file_dir = os.path.join(source_dir, 'meta')

    htaccess_file = os.path.join(meta_file_dir, '.htaccess_' + branch)
    if os.path.isfile(htaccess_file):
        target_file = os.path.join(compiled_dir, '.htaccess')
        print('copy meta file from {} to {}'.format(htaccess_file, target_file))
        copy2(htaccess_file, target_file)

    htpasswd_file = os.path.join(meta_file_dir, '.htpasswd_' + branch)
    if os.path.isfile(htpasswd_file):
        target_file = os.path.join(compiled_dir, '.htpasswd')
        print('copy meta file from {} to {}'.format(htpasswd_file, target_file))
        copy2(htpasswd_file, target_file)

    form_php_file = os.path.join(meta_file_dir, 'form.php')
    if os.path.isfile(form_php_file):
        target_file = os.path.join(compiled_dir, 'form.php')
        print('copy meta file from {} to {}'.format(form_php_file, target_file))
        copy2(form_php_file, target_file)


def _maybe_get_env_boolean(str_value):
    if type(str_value) != str:
        return str_value
    if str_value.lower() == 'false':
        return False
    if str_value.lower() == 'true':
        return True
    return str_value


def get_url_for_func(baseurl, content, add_index_html=True):
    pulled_routes = set()
    for data in content.values():
        if 'pulled' in data:
            pulled_routes.add(data['pulled'])

    def url_for(route, filename='index.html'):
        if route not in content:
            raise ValueError('route not found in content')
        if content[route].get('no_render', False):
            if 'forward' in content[route]:
                route = content[route]['forward']
            elif route not in pulled_routes:
                raise ValueError('route flagged as no render')

        if filename == 'index.html' and not add_index_html:
            return os.path.join(baseurl, route)
        else:
            return os.path.join(baseurl, route, filename)
    return url_for


def get_assets_url_for_func(source_assets_dir, assets_url):
    def assets_url_for(*route, filename=None, md5=False):
        if filename:
            p = os.path.join(assets_url, *route, filename)
            if md5:
                source_path = os.path.join(source_assets_dir, *route, filename)
                p += _get_md5_arg(source_path)
        else:
            assert not md5
            p = os.path.join(assets_url, *route)
        return p
    return assets_url_for


def get_image_url_for_func(assets_url, thumbnail_paths=set()):
    def image_url_for(*route, filename, thumbnail=False):
        raw_filename, file_ending = os.path.splitext(filename)
        assert file_ending in ['.png', '.jpeg', '.jpg']

        if not thumbnail:
            return os.path.join(assets_url, *route, filename)

        if thumbnail is True:
            size = (300, 300)
        else:
            size = thumbnail
        thumbnail_paths.add((os.path.join(*route, filename), tuple(size)))
        thumbnail_filename = raw_filename + '_thumbnail_{}x{}.png'.format(*size)
        return os.path.join(assets_url, 'thumbnails', *route, thumbnail_filename)

    return image_url_for, thumbnail_paths


def get_js_css_url_for_func(source_assets_dir, assets_dir, assets_url, js_css=None):
    os.makedirs(assets_dir, exist_ok=True)
    assert js_css in ['css', 'js']
    minifier = dict(css=cssmin, js=jsmin)[js_css]
    cache = dict()

    def js_css_url_for(*filenames):
        key = js_css + str(filenames)
        if key in cache:
            return cache[key]
        source_js_css_dir = os.path.join(source_assets_dir, js_css)
        compiled_js_css_dir = os.path.join(assets_dir, js_css)
        os.makedirs(compiled_js_css_dir, exist_ok=True)

        minified_strings = list()
        for filename in filenames:
            js_css_file = os.path.join(source_js_css_dir, filename)
            if os.path.isdir(js_css_file):
                copytree(js_css_file, os.path.join(compiled_js_css_dir, filename), dirs_exist_ok=True)
                continue

            with open(js_css_file) as js_css_file:
                if filename.split('.')[-2] == 'min':
                    minified = js_css_file.read()
                else:
                    minified = minifier(js_css_file.read())
            minified_strings.append(minified)

        output_filename = 'packed.min.' + js_css
        output_file_path = os.path.join(compiled_js_css_dir, output_filename)

        with open(output_file_path, 'w') as f:
            f.write('\n'.join(minified_strings))

        js_css_url = os.path.join(assets_url, js_css, output_filename)
        js_css_url += _get_md5_arg(output_file_path)

        cache[key] = js_css_url
        return js_css_url
    return js_css_url_for


def _get_md5_arg(path):
    md5_str = hashlib.md5(open(path, 'rb').read()).hexdigest()
    return '?v=' + str(md5_str)[:10]


def get_parse_url_filter(assets_url):
    def parse_url_filter(url_string):
        if url_string.startswith('assets:'):
            url_string = os.path.join(assets_url, url_string[7:])
        return url_string
    return parse_url_filter


def get_build_title_func(meta_data):
    def build_title(page):
        titles = []
        if 'title' in page:
            titles.append(page['title'])
        while 'parent' in page:
            titles.append(page['parent']['title'])
            page = page['parent']
        title = meta_data['title_separator'].join(titles)
        title += ' | '
        title += meta_data['title']
        return title
    return build_title


def is_active_route(active_route, link_route):
    return active_route.startswith(link_route)


def get_base_domain(url):
    d = urlparse(url).netloc
    if d.startswith('www.'):
        d = d[4:]
    return d


def copy_assets(content_dir, source_assets_dir, assets_dir, content):
    os.makedirs(assets_dir, exist_ok=True)

    skip_assets = ['js', 'css']
    skip_assets = [os.path.join(source_assets_dir, d) for d in skip_assets]

    def ignore_func(src, names):
        ignore_names = list()
        for name in names:
            file_path = os.path.join(src, name)
            if file_path in skip_assets:
                ignore_names.append(name)
                print('ignore', file_path)
        return ignore_names

    ignore = ignore_func if skip_assets else None

    copytree(source_assets_dir,
             assets_dir,
             ignore=ignore,
             dirs_exist_ok=True)

    for route, page in content.items():
        if page.get('assets', False):
            source_path = os.path.join(content_dir, page['route_origin'], 'assets')
            target_path = os.path.join(assets_dir, 'uploads', page['route_origin'])
            copytree(source_path, target_path, dirs_exist_ok=True)


def generate_address_image(source_assets_dir, args):
    if args is None:
        return None
    from PIL import Image, ImageDraw, ImageFont, ImageColor

    text = args['text']
    image_size = args.get('image_size', (100, 200))
    text_color = args.get('text_color', '#000000')
    background_color = args.get('background_color', '#ffffff')
    font = args.get('font', 'Ubuntu-R.ttf')
    font_size = args.get('font_size', 15)

    img = Image.new('RGB', image_size, color=ImageColor.getrgb(background_color))
    font = ImageFont.truetype(font, font_size)
    d = ImageDraw.Draw(img)
    d.text((1, 1), text, font=font, fill=ImageColor.getrgb(text_color))

    filename = 'a_image.png'
    filepath = os.path.join(source_assets_dir, 'images', filename)
    img.save(filepath)
    return filepath

