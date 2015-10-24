"""
Application configuration.
"""

import tornado.web
from tornado.options import define, options
from routes import routes

SETTINGS = {
    'cookie_secret': "8goWPH9uTyO+9e2NzuaW6pbR6WKH1EbmrXIfxttXq00=",
    'xsrf_cookies': True,
    'login_url': '/login',
    'autoreload': True,
    'template_path':'templates/',
    'static_path':'assets/',
}

define("port", default=8000, help="run on the given port", type=int)

application = tornado.web.Application(handlers=routes, **SETTINGS)
