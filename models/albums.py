import jsonschema
import json
from aiohttp.web import Response, Request
from .users import validate_api_key

async def get_handler(request):
    valid, result, user_id = await validate_api_key(request)
    if not (valid):
        return Response(
            status= 200,
            body = json.dumps(result),
            content_type='application/json'
        )

    async with ( request.app['db'].acquire() ) as conn:
        async with conn.transaction():
            await conn.set_type_codec(
                'json',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog'
            )

            results = await conn.fetch('''
                SELECT id, name, metadata::json, created, updated
                FROM albums
                WHERE user_id = $1;
            ''', user_id)
            result_arr = []
            for row in results:
                result_arr.append({
                    "id": str(row['id']),
                    "name": str(row['name']),
                    "metadata": row['metadata'],
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
    if not valid :
        return Response(
            status=200,
            body= json.dumps(result),
            content_type='application/json'
        )
    
    query = request.rel_url.query

    if not 'name' in query or not 'metadata' in query:
        return Response(
            status=200,
            body= json.dumps({"err":"No name or metadata provided"}),
            content_type='application/json'
        )
    
    name = query['name']
    metadata = query['metadata']

    valid, result = await validate_metadata(metadata)
    if not valid:
        return Response(
            status=200,
            body=json.dumps(result),
            content_type="application/json"
        )
    
    async with (request.app['db'].acquire()) as conn:
        async with conn.transaction():
            await conn.execute('''
                INSERT INTO albums(name, user_id, metadata) VALUES($1, $2, $3);
            ''', name, user_id, metadata)
            return Response(
                status=200,
                body=json.dumps({
                    "status": "ok"
                }),
                content_type="application/json"
            ) 

async def delete_handler(request):
    valid, result, user_id = await validate_api_key(request)
    if not valid:
        return Response(
            status=200,
            body = json.dumps(result),
            content_type='application/json'
        )
    
    query = request.rel_url.query
    if not 'id' in query:
        return Response(
            status=200,
            body= json.dumps({
                "err": "No album id provided"
            }),
            content_type='application/json'
        )
    album_id = int(query['id'])
    
    async with (request.app['db'].acquire()) as conn:
        async with conn.transaction():
            result = await conn.fetchrow('''
                SELECT id
                FROM albums
                WHERE user_id = $1 AND id =$2;
            ''', user_id, album_id)

            if not 'id' in result:
                return Response(
                    status=200,
                    body=json.dumps({"err":"No such album in your collection."})
                )

            await conn.execute('''
                DELETE FROM tracks
                WHERE album_id = $1;
            ''', album_id)
            await conn.execute('''
                DELETE FROM albums
                WHERE id = $1;
            ''', album_id)
            return Response(
                status=200,
                body = json.dumps({
                    "status": "ok"
                }),
                content_type='application/json'
            )

async def put_handler(request):
    valid, result, user_id = await validate_api_key(request)
    if not valid:
        return Response(
            status=200,
            body=json.dumps(result),
            content_type='application/json'
        )
    query = request.rel_url.query
    if not 'id' in query:
        return Response(
            status=200,
            body=json.dumps({
                "err": "No album id provided."
            }),
            content_type='application/json'
        )
    album_id = int(query['id'])

    async with(request.app['db'].acquire()) as conn:
        async with conn.transaction():
            result = await conn.fetchrow('''
                SELECT name, metadata
                FROM albums
                WHERE id = $1;
            ''', album_id)
            
            if not 'name' in result:
                return Response(
                    status=200,
                    body=json.dumps({
                        "err":"No album with id "+str(album_id) + " found"
                    }),
                    content_type='application/json'
                )

            if 'name' in query:
                album_name = query['name']
            else:
                album_name = result['name']
            
            if 'metadata' in query:
                valid, resp = await validate_metadata(query['metadata'])
                if not valid:
                    return Response(
                        status=200,
                        body=json.dumps(result),
                        content_type='application/json'
                    )
                album_metadata = json.dumps(resp)
            else:
                album_metadata = result['metadata']

            await conn.execute('''
                UPDATE albums
                SET name=$1, metadata=$2
                WHERE id = $3;
            ''', album_name, album_metadata, album_id)

            return Response(
                status=200,
                body=json.dumps({
                    "status":"ok"
                }),
                content_type='application/json'
            )

metadata_scheme = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title" : "MetadataField",
    "type" : "object",
    "properties": {
        "release_year": {
            "type":"number",
            "minimum" : 0
        },
        "awards" : {
            "type": "array",
            "items": {
                "type" : "string"
            }
        },
        "publisher" : {
            "type" : "string"
        },
        "ost": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "release_year",
        "awards",
        "publisher"
    ] 
}

async def validate_metadata(json_str):
    try:
        json_obj = json.loads(json_str)
    except BaseException:
        return (False, {"err": "error parsing JSON"})

    try:
        jsonschema.validate(json_obj, metadata_scheme)
        return (True, {
                "release_year" : json_obj['release_year'],
                "awards": json_obj['awards'],
                "publisher": json_obj['publisher'],
                "ost": json_obj['ost'] if 'ost' in json_obj else []
            })
    except jsonschema.exceptions.ValidationError as ex:
        return (False, {"err": "Json validation failed"})
    except jsonschema.exceptions.SchemaError as ex:
        return (False, {"err":"Server error"})

