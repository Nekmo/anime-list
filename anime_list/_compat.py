import six


if six.PY3:
    from html import unescape
    from urllib.parse import unquote
    from urllib.parse import quote
else:
    from urllib import quote
    from urllib import unquote