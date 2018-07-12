from aiohttp import web

def data(data):
    return web.json_response(data)

def error(msg):
    return web.json_response({"error" : msg})

def success():
    return web.json_response({"success": True})