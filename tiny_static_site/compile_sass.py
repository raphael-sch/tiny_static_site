import sass


def compile_sass(sass_file, css_output_file='source/assets/css/styles.css'):
    print('compile sass')
    s = sass.compile(filename=sass_file)
    with open(css_output_file, 'w') as f:
        f.write(s)
