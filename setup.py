import logging

from setuptools import setup, find_packages

readme_file = 'README.md'

try:
    import pypandoc

    long_description = pypandoc.convert(readme_file, to='rst')
except ImportError:
    logging.warning('pypandoc module not found, long_description will be the raw text instead.')
    with open(readme_file, encoding='utf-8') as fp:
        long_description = fp.read()

setup(
    name='wxpy',
    version='0.0.5',
    packages=find_packages(),
    package_data={
        '': ['*.md'],
    },
    include_package_data=True,
    install_requires=[
        'itchat>=1.2.26'
    ],
    url='https://github.com/youfou/wxpy',
    license='Apache 2.0',
    author='Youfou',
    author_email='youfou@qq.com',
    description='微信个人号 API，基于 itchat，告别满屏 dict，更有 Python 范儿',
    long_description=long_description,
    keywords=[
        '微信',
        'WeChat',
        'API'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Communications :: Chat',
        'Topic :: Utilities',
    ]
)
