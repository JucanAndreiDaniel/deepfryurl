from setuptools import setup

setup(
    name='deepfryurl',
    version='0.2.0',
    description='Deepfry an image from url',
    url='https://github.com/JucanAndreiDaniel/deepfryurl',
    author='Jucan Andrei Daniel',
    author_email='andrei.jucan00@e-uvt.ro',
    packages=['deepfryurl'],
    install_requires=['pillow',
                      'numpy',
                      'progressbar',
                      'aiohttp']
    )
