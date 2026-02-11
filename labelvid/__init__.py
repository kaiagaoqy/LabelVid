__appname__ = "LabelVid"

try:
    from importlib.metadata import version

    __version__ = version("labelvid")
except Exception:
    __version__ = "0.0.0"
