# coding: utf-8
from __future__ import unicode_literals

import inspect

from wxpy.compatible import PY2


def _ipython(local, banner):
    from IPython.terminal.embed import InteractiveShellEmbed
    from IPython.terminal.ipapp import load_default_config

    InteractiveShellEmbed.clear_instance()
    shell = InteractiveShellEmbed.instance(
        banner1=banner,
        user_ns=local,
        config=load_default_config()
    )
    shell()


def _bpython(local, banner):
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    import bpython

    bpython.embed(locals_=local, banner=banner)


def _python(local, banner):
    import code

    try:
        # noinspection PyUnresolvedReferences
        import readline
    except ImportError:
        pass
    else:
        import rlcompleter
        readline.parse_and_bind('tab:complete')
    if PY2:
        banner = banner.encode('utf-8')

    code.interact(local=local, banner=banner)


def embed(local=None, banner='', shell=None):
    """
    | 进入交互式的 Python 命令行界面，并堵塞当前线程
    | 支持使用 ipython, bpython 以及原生 python

    :param str shell:
        | 指定命令行类型，可设为 'ipython'，'bpython'，'python'，或它们的首字母；
        | 若为 `None`，则按上述优先级进入首个可用的 Python 命令行。
    :param dict local: 设定本地变量环境，若为 `None`，则获取进入之前的变量环境。
    :param str banner: 设定欢迎内容，将在进入命令行后展示。
    """

    import inspect

    if not local:
        local = inspect.currentframe().f_back.f_locals

    if isinstance(shell, str):
        shell = shell.strip().lower()
        if shell.startswith('b'):
            shell = _bpython
        elif shell.startswith('i'):
            shell = _ipython
        elif shell.startswith('p') or not shell:
            shell = _python

    for _shell in shell, _ipython, _bpython, _python:
        try:
            _shell(local=local, banner=banner)
        except (TypeError, ImportError):
            continue
        except KeyboardInterrupt:
            break
        else:
            break


def get_arg_parser():
    import argparse

    ap = argparse.ArgumentParser(
        description='Run a wxpy-ready python console.')

    ap.add_argument(
        'bot', type=str, nargs='*',
        help='One or more variable name(s) for bot(s) to init (default: None).')

    ap.add_argument(
        '-c', '--cache', action='store_true',
        help='Cache session(s) for a short time, or load session(s) from cache '
             '(default: disabled).')

    ap.add_argument(
        '-q', '--console_qr', type=int, default=False, metavar='width',
        help='The width for console_qr (default: None).')

    ap.add_argument(
        '-l', '--logging_level', type=str, default='INFO', metavar='level',
        help='Logging level (default: INFO).')

    ap.add_argument(
        '-s', '--shell', type=str, default=None, metavar='shell',
        help='Specify which shell to use: ipython, bpython, or python '
             '(default: the first available).')

    ap.add_argument(
        '-v', '--version', action='store_true',
        help='Show version and exit.')

    return ap


def shell_entry():
    import re

    import logging
    import wxpy

    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()

    if args.bot:
        def get_logging_level():
            logging_level = args.logging_level.upper()
            for level in 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET':
                if level.startswith(logging_level):
                    return getattr(logging, level)
            else:
                return logging.INFO

        logging.basicConfig(level=get_logging_level())

        try:
            bots = dict()
            for name in args.bot:
                if not re.match(r'\w+$', name):
                    continue
                cache_path = 'wxpy_{}.pkl'.format(name) if args.cache else None
                bots[name] = wxpy.Bot(cache_path=cache_path, console_qr=args.console_qr)
        except KeyboardInterrupt:
            return

        banner = 'from wxpy import *\n'

        for k, v in bots.items():
            banner += '{}: {}\n'.format(k, v)

        module_members = dict(inspect.getmembers(wxpy))

        embed(
            local=dict(module_members, **bots),
            banner=banner,
            shell=args.shell
        )
    elif args.version:
        print(wxpy.version_details)
    else:
        arg_parser.print_help()
