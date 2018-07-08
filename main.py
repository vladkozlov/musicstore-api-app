import logging
import sys

from aiohttp import web

from db import init_db
from route import setup_routes
from settings import APP_CFG, DB_CFG, get_config


async def init_app(args=None):
    app = web.Application()
    app['config'] = get_config(DB_CFG)
    
    app.on_startup.append(init_db)

    setup_routes(app)
    return app

def main(args):
    logging.basicConfig(level=logging.DEBUG)

    app = init_app(args)

    # loading app cfg
    config = get_config(APP_CFG)
    web.run_app(
        app,
        host = config['app']['host'],
        port = config['app']['port']
    )

if __name__ == '__main__':
    main(sys.argv[1:])
