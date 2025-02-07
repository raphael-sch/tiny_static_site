from setuptools import setup

setup(
    name='tiny-static-site',
    version='0.0.1',
    entry_points={
        'console_scripts': ['compile_tiny_static_site=tiny_static_site.compile:run'],
    },
    packages=['tiny_static_site'],
    python_requires=">=3.8",
    install_requires=[
        'MarkupSafe==2.0.1',
        'Jinja2==2.11.3',
        'jinja2-ansible-filters==1.3.2',
        'beautifulsoup4==4.9.3',
        "Pillow==8.3.2",
        "jsmin==3.0.0",
        "rcssmin==1.0.6",
        "minify-html==0.7.0"
    ],
    extras_require={
        'sass': ["libsass==0.20.1"],
    },
    url='',
    license='',
    author='raphael',
    author_email='raphael@schumann.pub',
    description='Tiny Static Site Generator'
)
