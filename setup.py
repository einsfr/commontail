from setuptools import setup

from commontail import __version__

setup(
    name='commontail',
    version=__version__,
    packages=['commontail'],
    url='https://github.com/einsfr/commontail',
    license='MIT',
    author='Alex',
    author_email='alex@efswdev.ru',
    description='Common components for wagtail projects',

    install_requires=[
        'django>=3.2,<3.3',
        'lxml>=4.6,<4.7',
        'wagtail>=2.13,<2.14',
    ],

    python_requires='>=3.7',
)
