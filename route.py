from models import users, albums, tracks  

def setup_routes(app):
    app.router.add_get(     '/users',   users.get_handler)
    app.router.add_post(    '/users',   users.post_handler)
    app.router.add_delete(  '/users',   users.delete_handler)

    app.router.add_get(     '/albums',  albums.get_handler)
    app.router.add_post(    '/albums',  albums.post_handler)
    app.router.add_delete(  '/albums',  albums.delete_handler)
    app.router.add_put(     '/albums',  albums.put_handler)

    app.router.add_get(     '/tracks',  tracks.get_handler)
    app.router.add_post(    '/tracks',  tracks.post_handler)
    app.router.add_put(     '/tracks',  tracks.put_handler)
    app.router.add_delete(  '/tracks',  tracks.delete_handler)
