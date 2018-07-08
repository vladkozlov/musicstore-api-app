import json
from aiohttp.web import Response, Request
from .users import validate_api_key

async def get_handler(request):
    valid, result, user_id = await validate_api_key(request)
    if not valid:
        return Response(
            status=200,
            body= json.dumps(result),
            content_type= 'application/json'
        )
    
    async with ( request.app['db'].acquire() ) as conn:
        async with conn.transaction():
            results = await conn.fetch('''
                SELECT id as trck_id, name, album_id, created, updated
                FROM tracks, 
                    (SELECT id as albm_id
                    FROM albums
                    WHERE user_id=$1) as A
                WHERE album_id = a.albm_id
            ''', user_id)
            
            result_arr = []
            for row in results:
                result_arr.append({
                    "id": str(row['trck_id']),
                    "name": row['name'],
                    "album_id": str(row['album_id']),
                    "created" : str(row['created']),
                    "updated" : str(row['updated'])
                } )
            return Response(
                status=200,
                body = json.dumps(result_arr),
                content_type="application/json"
            )


async def post_handler(request):
    valid, result, user_id = await validate_api_key(request)
    if not valid:
        return Response(
            status=200,
            body= json.dumps(result),
            content_type='application/json'
        )
    query = request.rel_url.query

    if not 'name' in query or not 'album_id' in query:
        return Response(
            status=200,
            body=json.dumps({"err":"No track name or album_id provided."}),
            content_type='application/json'
        ) 
    album_id = int(query['album_id'])
    track_name = query['name']

    async with (request.app['db'].acquire()) as conn:
        async with conn.transaction():
            result = await conn.fetchrow('''
                SELECT id
                FROM albums
                WHERE id = $1 AND user_id = $2; 
            ''', album_id, user_id)

            if result is None:
                return Response(
                    status=200,
                    body=json.dumps({"err":"no such album in your collection"}),
                    content_type='application/json'
                )

            await conn.execute('''
                INSERT INTO tracks (name, album_id) VALUES ($1, $2)
            ''', track_name, album_id)
            return Response(
                status=200,
                body=json.dumps({"status":"ok"}),
                content_type='application/json'
            )

async def delete_handler(request):
    valid, result, user_id = await validate_api_key(request)
    if not valid:
        return Response(
            status=200,
            body= json.dumps(result),
            content_type='application/json'
        )
    query = request.rel_url.query

    if not 'id' in query:
        return Response(
            status=200,
            body=json.dumps({"err":"No track id provided to delete."}), 
            content_type='application/json'
        )
    track_id = int(query['id'])

    async with (request.app['db'].acquire()) as conn:
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
                return Response(
                    status=200,
                    body= json.dumps({"err":"Not enought priviledges to delete this track."}),
                    content_type='application/json'
                )

            await conn.execute('''
                DELETE FROM tracks
                WHERE id=$1;
            ''', track_id)

            return Response(
                status=200,
                body=json.dumps({"status":"ok"}),
                content_type='application/json'
            )

async def put_handler(request):
    valid, result, user_id = await validate_api_key(request)
    if not valid:
        return Response(
            status=200,
            body= json.dumps(result),
            content_type='application/json'
        )
    query = request.rel_url.query

    if not 'id' in query:
        return Response(
            status=200,
            body=json.dumps({"err":"No track id provided to edit."}), 
            content_type='application/json'
        )
    track_id = int(query['id'])
    
    async with (request.app['db'].acquire()) as conn:
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

            return Response(
                status=200,
                body=json.dumps({
                    "status":"ok"
                }),
                content_type='application/json'
            )