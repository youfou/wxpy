import inspect


def _bpython(local, banner):
    import bpython

    bpython.embed(locals_=local, banner=banner)


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

    code.interact(local=local, banner=banner)


def embed(local=None, banner='', shell=None):
    """
    进入交互式的 Python 命令行，支持使用 bpython，ipython，以及原生 python。

    :param str shell:
        | 指定命令行类型，可设为 `'bpython'`，`'ipython'`，`'python'`，或它们的首字母；
        | 若为 `None`，则按上述优先级进入首个可用的 Python 命令行。
    :param dict local: 设定本地变量环境，若为 `None`，则获取进入之前的变量环境。
    :param str banner: 设定欢迎内容，将在进入命令行后展示。
    """

    if local is None:
        local = inspect.currentframe().f_back.f_locals

    if isinstance(shell, str):
        shell = shell.strip().lower()
        if shell.startswith('b'):
            shell = _bpython
        elif shell.startswith('i'):
            shell = _ipython
        elif shell.startswith('p') or not shell:
            shell = _python

    for _shell in shell, _bpython, _ipython, _python:
        try:
            _shell(local=local, banner=banner)
        except (TypeError, ImportError):
            continue
        else:
            break


def cli():
    # Todo: 实现
    pass
