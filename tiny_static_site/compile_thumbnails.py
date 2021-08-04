import os

from PIL import Image


def create_thumbnails(source_assets_dir, thumbnail_paths, size):
    for path in thumbnail_paths:
        path = os.path.join(source_assets_dir, path)
        output_path = create_thumbnail(path, size)
        print('created thumbnail: {}'.format(output_path))


def create_thumbnail(image_path, size=(300, 300)):
    image = Image.open(image_path)
    image.thumbnail(size, Image.ANTIALIAS)
    background = Image.new('RGBA', size, (255, 255, 255, 0))
    background.paste(
        image, (int((size[0] - image.size[0]) / 2), int((size[1] - image.size[1]) / 2))
    )

    output_raw_path = image_path.split('.')[0]
    output_path = output_raw_path + '_thumbnail.png'

    background.save(output_path)

    return output_path
