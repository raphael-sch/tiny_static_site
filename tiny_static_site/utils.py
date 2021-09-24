import json
import os
import zipfile
import hashlib
from shutil import copytree, copy2
from urllib.parse import urlparse


def get_meta_data(source_dir):
    with open(os.path.join(source_dir, 'meta.json')) as f:
        meta_data = json.load(f)

    meta_data['skip_assets'] = meta_data.get('skip_assets', [])
    meta_data['unzip_assets'] = meta_data.get('unzip_assets', [])

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


def _maybe_get_env_boolean(str_value):
    if type(str_value) != str:
        return str_value
    if str_value.lower() == 'false':
        return False
    if str_value.lower() == 'true':
        return True
    return str_value


def get_url_for_func(baseurl, content, add_index_html=True):
    def url_for(route, filename='index.html'):
        if route not in content:
            raise ValueError('route not found in content')
        if content[route].get('no_render', False):
            if 'forward' in content[route]:
                route = content[route]['forward']
            else:
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
                md5_str = hashlib.md5(open(source_path, 'rb').read()).hexdigest()
                p += '?v=' + str(md5_str)[:10]
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


def copy_assets(source_dir, content_dir, assets_dir, content, skip_assets=None):
    os.makedirs(assets_dir, exist_ok=True)
    source_assets_dir = os.path.join(source_dir, 'assets')

    if skip_assets:
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


def unzip_assets(assets_dir, zip_files):
    for zip_file in zip_files:
        path_to_zip_file = os.path.join(assets_dir, zip_file)
        if os.path.exists(path_to_zip_file):
            path_to_unzip = os.path.dirname(path_to_zip_file)
            print('unzip asset', path_to_zip_file)
            with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                zip_ref.extractall(path_to_unzip)
            os.remove(path_to_zip_file)
