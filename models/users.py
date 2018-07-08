import asyncio
from aiohttp.web import Response, Request
import json
import asyncpg.exceptions
from uuid import UUID

async def get_handler( request ): #нужна валидация!!
    is_valid, result, _ = await validate_api_key(request)
    if not is_valid:
        return Response(
            status= 200,
            body=json.dumps(result),
            content_type='application/json'
        )
    
    return Response(
        status= 200,
        body = json.dumps(result),
        content_type='application/json'
    )


async def post_handler(request): #нужна валидация!!
    query = request.rel_url.query

    if not 'email' in query or not 'first_name' in query or not 'last_name' in query:
        return Response(
            status=200,
            body= json.dumps({"err":"No email, or firstname, or lastname provided."}),
            content_type='application/json'
        )

    email = query['email']
    first_name = query['first_name']
    last_name = query['last_name']

    async with ( request.app['db'].acquire() ) as conn:
        async with conn.transaction():
            try:
                result = await conn.execute('''
                    INSERT INTO users(email, first_name, last_name) VALUES($1, $2, $3)
                ''', email , first_name , last_name )
                result = await conn.fetchrow('''
                    SELECT api_key from users where email=$1
                ''', email)
                
                return Response(status=201, body=json.dumps({
                        'api_key': str(result['api_key'])
                    }), content_type='application/json')
            except asyncpg.exceptions.UniqueViolationError as ex:
                return Response(
                    status=200, 
                    body=json.dumps({
                        'error': "Email already exist."
                    }), content_type='application/json')

async def delete_handler(request):
    query = request.rel_url.query
    is_valid, result, _ = await validate_api_key(request)
    if not is_valid:
        return Response(
            status=200, 
            body=json.dumps(result), content_type='application/json')

    api_key = query['api_key']
    async with ( request.app['db'].acquire() ) as conn:
        async with conn.transaction():
            await conn.execute('''
                UPDATE users 
                SET is_active = false
                WHERE api_key=$1
            ''', api_key)
            return Response(status=200, body=json.dumps({
                    'status': True
                }), content_type='application/json')


async def validate_api_key(request):
    query = request.rel_url.query

    if not 'api_key' in query:
        return (False, {"err":"no api key"}, None)

    try:
        api_key = UUID(query['api_key'], version=4)
    except ValueError:
        return (False, {"err": "Mailformed api_key"})
    

    async with(request.app['db'].acquire()) as conn:
        async with conn.transaction():
            result = await conn.fetchrow('''
                SELECT id, email, first_name, last_name, is_active
                FROM users
                WHERE api_key=$1
            ''', api_key)

            if result == None: 
                return (False, {"err":"no such api key"}, None)
            
            if (result['is_active'] == False):
                return (False, {"err":"User api_key deactivated."}, None)
            
            return (True, {
                "email":result['email'],
                "first_name":result['first_name'],
                "last_name":result['last_name'],
                }, result['id'])