import asyncio
from aiohttp import web
from . import Response
import json
import asyncpg.exceptions
from .users import validate_api_key

track_routes = web.RouteTableDef()

@track_routes.view('/tracks/{id}')
@track_routes.view('/tracks')
class Track(web.View):
    
    async def get(self):
        valid, result, user_id = await validate_api_key(self.request)
        if not valid:
            return Response.error(result)
        
        track_id = None
        if "id" in self.request.match_info:
            track_id = int(self.request.match_info['id'])

        async with ( self.request.app['db'].acquire() ) as conn:
            async with conn.transaction():
                if not track_id:
                    results = await conn.fetch('''
                        SELECT id as trck_id, name, album_id, created, updated
                        FROM tracks, 
                            (SELECT id as albm_id
                            FROM albums
                            WHERE user_id=$1) as A
                        WHERE album_id = a.albm_id
                    ''', user_id)
                else :
                    results = await conn.fetch('''
                        SELECT id as trck_id, name, album_id, created, updated
                        FROM tracks, 
                            (SELECT id as albm_id
                            FROM albums
                            WHERE user_id=$1) as A
                        WHERE album_id = a.albm_id AND id=$2
                    ''', user_id, track_id)
                
                result_arr = []
                for row in results:
                    result_arr.append({
                        "id": str(row['trck_id']),
                        "name": row['name'],
                        "album_id": str(row['album_id']),
                        "created" : str(row['created']),
                        "updated" : str(row['updated'])
                    } )
                return Response.data(result_arr)

    async def post(self):
        valid, result, user_id = await validate_api_key(self.request)
        if not valid:
            return Response.error(result)

        query = self.request.rel_url.query

        if not 'name' in query or not 'album_id' in query:
            return Response.error("No track name or album_id provided.")
        
        album_id = int(query['album_id'])
        track_name = query['name']

        async with (self.request.app['db'].acquire()) as conn:
            async with conn.transaction():
                result = await conn.fetchrow('''
                    SELECT id
                    FROM albums
                    WHERE id = $1 AND user_id = $2; 
                ''', album_id, user_id)

                if result is None:
                    return Response.error("no such album in your collection")

                await conn.execute('''
                    INSERT INTO tracks (name, album_id) VALUES ($1, $2)
                ''', track_name, album_id)
                return Response.success()
        
    async def delete(self):
        valid, result, user_id = await validate_api_key(self.request)

        if not valid:
            return Response.error(result)
        
        query = self.request.rel_url.query

        if not 'id' in query:
            if not 'id' in self.request.match_info:
                return Response.error("No track id provided to delete.")
            else:
                track_id = int(self.request.match_info['id'])
        else:
            track_id = int(query['id'])

        async with (self.request.app['db'].acquire()) as conn:
            async with conn.transaction():
                result = await conn.fetchrow('''
                    WITH T as (SELECT album_id
                        FROM tracks
                        WHERE id = $1)
                    SELECT user_id
                    FROM albums, T
                    WHERE id=T.album_id
                ''', track_id)

                if not result['user_id'] == user_id:
                    return Response.error("Not enought priviledges to delete this track.")

                await conn.execute('''
                    DELETE FROM tracks
                    WHERE id=$1;
                ''', track_id)

                return Response.success()

    async def put(self):
        valid, result, user_id = await validate_api_key(self.request)
        if not valid:
            return Response.error(result)
        
        query = self.request.rel_url.query

        if not 'id' in query:
            if not 'id' in self.request.match_info:
                return Response.err("No track id provided to edit.")
            else:
                track_id = int(self.request.match_info['id'])
        else:
            track_id = int(query['id'])
        
        async with (self.request.app['db'].acquire()) as conn:
            async with conn.transaction():
                result = await conn.fetchrow('''
                    SELECT name, album_id
                    FROM tracks
                    WHERE id = $1;
                ''', track_id)

                if 'name' in query:
                    track_name = query['name']
                else:
                    track_name = result['name']
                
                if 'album_id' in query:
                    album_id = int(query['album_id'])
                else:
                    album_id = result['album_id']

                await conn.execute('''
                    UPDATE tracks
                    SET name = $1, album_id=$2
                    WHERE id = $3
                ''', track_name, album_id, track_id)

                return Response.success()
