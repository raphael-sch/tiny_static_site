import os

from PIL import Image


def create_thumbnails(source_assets_dir, thumbnail_paths):
    thumbnails_dir = os.path.join(source_assets_dir, 'thumbnails')
    os.makedirs(thumbnails_dir, exist_ok=True)
    for filepath, size in thumbnail_paths:
        image_filepath = os.path.join(source_assets_dir, filepath)
        thumbnail_path = os.path.join(thumbnails_dir, os.path.dirname(filepath))
        output_path = create_thumbnail(image_filepath, thumbnail_path, size)
        print('created thumbnail: {}'.format(output_path))


def create_thumbnail(image_filepath, thumbnail_path, size):
    os.makedirs(thumbnail_path, exist_ok=True)
    image = Image.open(image_filepath)
    image.thumbnail(size, Image.ANTIALIAS)
    background = Image.new('RGBA', size, (255, 255, 255, 0))
    background.paste(
        image, (int((size[0] - image.size[0]) / 2), int((size[1] - image.size[1]) / 2))
    )

    image_filename = os.path.basename(image_filepath)
    image_filename, _ = image_filename.split('.', maxsplit=1)
    thumbnail_filename = image_filename + '_thumbnail_{}x{}.png'.format(*size)
    output_path = os.path.join(thumbnail_path, thumbnail_filename)

    background.save(output_path)

    return output_path
