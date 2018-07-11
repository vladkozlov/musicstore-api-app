import asyncio
from aiohttp import web
from . import responses
import json
import asyncpg.exceptions
from .users import validate_api_key

album_routes = web.RouteTableDef()

@album_routes.view('/albums/{id}')
@album_routes.view('/albums')
class Album(web.View):

    async def get(self):
        valid, result, user_id = await validate_api_key(self.request)
        if not valid:
            return Response.error(result)
        
        album_id = None
        if "id" in self.request.match_info:
            album_id = int(self.request.match_info['id'])

        async with ( self.request.app['db'].acquire() ) as conn:
            async with conn.transaction():
                await conn.set_type_codec(
                    'json',
                    encoder=json.dumps,
                    decoder=json.loads,
                    schema='pg_catalog'
                )
                
                if not album_id:
                    results = await conn.fetch('''
                        SELECT id, name, metadata::json, created, updated
                        FROM albums
                        WHERE user_id = $1;
                    ''', user_id)
                else:
                    results = await conn.fetch('''
                        SELECT id, name, metadata::json, created, updated
                        FROM albums
                        WHERE user_id=$1 AND id=$2
                    ''', user_id, album_id)

                result_arr = []
                for row in results:
                    result_arr.append({
                        "id": str(row['id']),
                        "name": str(row['name']),
                        "metadata": row['metadata'],
                        "created" : str(row['created']),
                        "updated" : str(row['updated'])
                    } )
                return Response.data(result_arr)
    
    async def post(self):
        valid, result, user_id = await validate_api_key(self.request)
        if not valid :
            return Response.error(result)
        
        query = self.request.rel_url.query

        if not 'name' in query or not 'metadata' in query:
            return Response.error("No name or metadata provided")
        
        name = query['name']
        metadata = query['metadata']

        valid, result = await validate_metadata(metadata)
        if not valid:
            return Response.error(result)
        
        async with (self.request.app['db'].acquire()) as conn:
            async with conn.transaction():
                await conn.execute('''
                    INSERT INTO albums(name, user_id, metadata) VALUES($1, $2, $3);
                ''', name, user_id, metadata)

                return Response.success()

    async def delete(self):
        valid, result, user_id = await validate_api_key(self.request)
        if not valid:
            return Response.error(result)
        
        query = self.request.rel_url.query

        if not 'id' in query:
            if not 'id' in self.request.match_info:
                return Response.error("No album id provided")
            else:
                album_id = int(self.request.match_info['id'])
        else:
            album_id = int(query['id'])
        
        async with (self.request.app['db'].acquire()) as conn:
            async with conn.transaction():
                result = await conn.fetchrow('''
                    SELECT id
                    FROM albums
                    WHERE user_id = $1 AND id =$2;
                ''', user_id, album_id)

                if not 'id' in result:
                    return Response.error("No such album in your collection.")

                await conn.execute('''
                    DELETE FROM tracks
                    WHERE album_id = $1;
                ''', album_id)
                await conn.execute('''
                    DELETE FROM albums
                    WHERE id = $1;
                ''', album_id)
                return Response.success()
    
    async def put(self):
        valid, result, user_id = await validate_api_key(self.request)
        if not valid:
            return Response.error(result)
    
        query = self.request.rel_url.query
        if not 'id' in query:
            if not 'id' in self.request.match_info:
                return Response.error("No album id provided.")
            else:
                album_id = int(self.request.match_info['id'])
        else:
            album_id = int(query['id'])

        async with (self.request.app['db'].acquire()) as conn:
            async with conn.transaction():
                result = await conn.fetchrow('''
                    SELECT name, metadata
                    FROM albums
                    WHERE id = $1;
                ''', album_id)
                
                if not 'name' in result:
                    return Response.error("No album with id "+str(album_id) + " found")

                if 'name' in query:
                    album_name = query['name']
                else:
                    album_name = result['name']
                
                if 'metadata' in query:
                    valid, result = await validate_metadata(query['metadata'])
                    if not valid:
                        return Response.error(result)

                    album_metadata = json.dumps(resp)
                else:
                    album_metadata = result['metadata']

                await conn.execute('''
                    UPDATE albums
                    SET name=$1, metadata=$2
                    WHERE id = $3;
                ''', album_name, album_metadata, album_id)

                return Response.success()

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
            return (False, "error parsing JSON")

        try:
            jsonschema.validate(json_obj, metadata_scheme)
            return (True, {
                    "release_year" : json_obj['release_year'],
                    "awards": json_obj['awards'],
                    "publisher": json_obj['publisher'],
                    "ost": json_obj['ost'] if 'ost' in json_obj else []
                })
        except jsonschema.exceptions.ValidationError as ex:
            return (False, "Json validation failed")
        except jsonschema.exceptions.SchemaError as ex:
            return (False, "Server error")