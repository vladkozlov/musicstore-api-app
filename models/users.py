import asyncio
from aiohttp import web
from . import Response
import json
import asyncpg.exceptions
from uuid import UUID
import re

user_routes = web.RouteTableDef()

@user_routes.view('/user')
class User(web.View):
    async def get(self):
        valid, result, _ = await validate_api_key(self.request)
        if valid:
            return Response.data(result)
        else:
            return Response.error(result)

    async def post(self):
        query = self.request.rel_url.query

        if not 'email' in query or not 'first_name' in query or not 'last_name' in query:
            return Response.error("No email, or firstname, or lastname provided.")

        email = query['email']
        if not validate_email(email):
            return Response.error("email is not valid")

        first_name = query['first_name']
        last_name = query['last_name']
        
        async with ( self.request.app['db'].acquire() ) as conn:
            async with conn.transaction():
                try:
                    await conn.execute('''
                        INSERT INTO users(email, first_name, last_name) VALUES($1, $2, $3)
                    ''', email , first_name , last_name )

                    result = await conn.fetchrow('''
                        SELECT api_key from users where email=$1
                    ''', email)
                    return Response.data({'api_key':str(result['api_key'])})
                except asyncpg.exceptions.UniqueViolationError:
                    return Response.error("Email already exist")

    async def delete(self):    
        query = self.request.rel_url.query
        valid, result, _ = await validate_api_key(self.request)
        if not valid:
            return Response.error(result)

        api_key = query['api_key']
        async with ( self.request.app['db'].acquire() ) as conn:
            async with conn.transaction():
                await conn.execute('''
                    UPDATE users 
                    SET is_active = false
                    WHERE api_key=$1
                ''', api_key)
                return Response.data(result)

def validate_email(email_str):
    EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

    if not EMAIL_REGEX.match(email_str):
        return False
    return True 

async def validate_api_key(request):
    if not 'x-api-key' in request.headers:
        return (False, "no api key specified", None)

    try:
        api_key = UUID(request.headers['x-api-key'], version=4)
    except ValueError:
        return (False, "Mailformed api_key", None)

    async with(request.app['db'].acquire()) as conn:
        async with conn.transaction():
            result = await conn.fetchrow('''
                SELECT id, email, first_name, last_name, is_active
                FROM users
                WHERE api_key=$1
            ''', api_key)

            if not result: 
                return (False, "no such api key", None)
            
            if (result['is_active'] == False):
                return (False, "User api_key deactivated.", None)
            
            return (True, {
                "email":result['email'],
                "first_name":result['first_name'],
                "last_name":result['last_name'],
                }, result['id'])