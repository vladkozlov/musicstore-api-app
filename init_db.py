import asyncio
import asyncpg
from settings import BASE_DIR, get_config
from models.albums import parseJsonToStr
import json

DSN = 'postgresql://{user}:{password}@{host}:{port}/{database}'

USER_CONFIG = get_config()
USER_DB_URL = DSN.format(**USER_CONFIG['postgres'])

async def setup_db(dsn_url):
    conn = await asyncpg.connect(dsn=dsn_url)
    await conn.execute('''
        DROP TABLE IF EXISTS users CASCADE;
        DROP TABLE IF EXISTS albums CASCADE;
        DROP TABLE IF EXISTS tracks CASCADE;
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    ''')

    # creating users
    await conn.execute('''
        CREATE TABLE users(
            id serial PRIMARY KEY,
            email varchar(30) UNIQUE,
            first_name varchar(30) not null,
            last_name varchar(30) not null,
            created timestamp not null DEFAULT now(),
            is_active bool not null DEFAULT true,
            api_key uuid DEFAULT uuid_generate_v4()
        );
    ''')

    # creating albums and baking update timestamp function
    await conn.execute('''
        CREATE TABLE albums(
            id serial PRIMARY KEY,
            name varchar(40) not null,
            user_id integer REFERENCES users(id),
            metadata jsonb,
            created timestamp not null DEFAULT now(),
            updated timestamp not null DEFAULT now()
        );
        
        CREATE OR REPLACE FUNCTION update_column_timestamp()   
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated = now();
            RETURN NEW;   
        END;
        $$ language 'plpgsql';

        CREATE TRIGGER update_album_timestamp
        BEFORE UPDATE ON albums 
        FOR EACH ROW EXECUTE PROCEDURE update_column_timestamp();
    ''')

    # creating tracks
    await conn.execute('''
        CREATE TABLE tracks(
            id serial PRIMARY KEY,
            name varchar(40),
            album_id integer REFERENCES albums(id),
            created timestamp not null DEFAULT now(),
            updated timestamp not null DEFAULT now()
        )
    ''')
    
    await conn.close()

async def insert_test_data(dsn_url):
    conn = await asyncpg.connect(dsn=dsn_url)
    await conn.execute('''
        INSERT INTO users(email, first_name, last_name) VALUES($1, $2, $3)
    ''', 'admin@music.store', 'Vasya', 'Pupkin')

    await conn.execute('''
        INSERT INTO users(email, first_name, last_name) VALUES($1, $2, $3)
    ''', 'lexa87@mail.ru', 'Lexa', 'Don')
    
    await conn.execute('''
        INSERT INTO albums(name, user_id, metadata) VALUES($1, $2, $3)
    ''', 'I BELIVE I CAN FLY', 2, parseJsonToStr('{\"release_year\": 1984,\"awards\": [\"Grammy\",\"MTV music awards\"],\"publisher\": \"Warner music\",\"ost\": [\"Silent hill\",\"Supernatural\"]}'))

    await conn.execute('''
        INSERT INTO tracks(name, album_id) VALUES($1, $2)
    ''', 'Fly - Girl', 1)

    await conn.close()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(setup_db(USER_DB_URL))
    asyncio.get_event_loop().run_until_complete(insert_test_data(USER_DB_URL))