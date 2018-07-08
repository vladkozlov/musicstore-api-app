import asyncpg

DSN = 'postgresql://{user}:{password}@{host}:{port}/{database}'

async def init_db(app):
    conf = app['config']['database']
    
    dsn_url = DSN.format(**conf)

    app['db'] = await asyncpg.create_pool(dsn=dsn_url)
