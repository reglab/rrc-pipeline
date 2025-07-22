import sys
import traceback

import rich_click


def excepthook(type, value, tb):
    if issubclass(type, KeyboardInterrupt):
        sys.__excepthook__(type, value, tb)
        return
    else:
        traceback.print_exception(type, value, tb)


def command(*args, **kwargs):
    context_settings = kwargs.get("context_settings", {})
    if "show_default" not in context_settings:
        context_settings["show_default"] = True
    kwargs["context_settings"] = context_settings

    def decorator(f):
        sys.excepthook = excepthook
        return rich_click.command(*args, **kwargs)(f)

    return decorator


def group(*args, **kwargs):
    context_settings = kwargs.get("context_settings", {})
    if "show_default" not in context_settings:
        context_settings["show_default"] = True
    kwargs["context_settings"] = context_settings

    def decorator(f):
        sys.excepthook = excepthook
        return rich_click.group(*args, **kwargs)(f)

    return decorator


def __getattr__(name):
    return getattr(rich_click, name)
