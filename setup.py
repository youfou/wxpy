import re

from setuptools import find_packages, setup

with open('wxpy/__init__.py', encoding='utf-8') as fp:
    version = re.search(r"__version__\s*=\s*'([\d.]+)'", fp.read()).group(1)

with open('README.rst', encoding='utf-8') as fp:
    readme = fp.read()

setup(
    name='wxpy',
    version=version,
    packages=find_packages(),
    package_data={
        '': ['*.rst'],
    },
    include_package_data=True,
    install_requires=[
        'itchat>=1.2.27',
    ],
    url='https://github.com/youfou/wxpy',
    license='Apache 2.0',
    author='Youfou',
    author_email='youfou@qq.com',
    description='微信个人号 API，基于 itchat，告别满屏 dict，更有 Python 范儿',
    long_description=readme,
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
