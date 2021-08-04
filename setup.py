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
        'Jinja2==2.11.3',
        'beautifulsoup4==4.9.3'
    ],
    extras_require={
        'sass': ["libsass==0.20.1"],
        'thumbnail': ["Pillow==8.3.1"],
    },
    url='',
    license='',
    author='raphael',
    author_email='raphael@schumann.pub',
    description='Tiny Static Site Generator'
)
