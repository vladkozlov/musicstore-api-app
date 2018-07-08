from models import users, albums, tracks  

def setup_routes(app):
    #USERS
    app.router.add_get(     '/users',   users.get_handler)
    app.router.add_post(    '/users',   users.post_handler)
    app.router.add_delete(  '/users',   users.delete_handler)

    #ALBUMS
    app.router.add_get(     '/albums',  albums.get_handler)
    app.router.add_post(    '/albums',  albums.post_handler)
    app.router.add_delete(  '/albums',  albums.delete_handler)
    app.router.add_put(     '/albums',  albums.put_handler)
    # albums variable context access
    app.router.add_get(     '/albums/{id}',  albums.get_handler)
    app.router.add_delete(  '/albums/{id}',  albums.delete_handler)
    app.router.add_put(     '/albums/{id}',  albums.put_handler)

    #TRACKS
    app.router.add_get(     '/tracks',  tracks.get_handler)
    app.router.add_post(    '/tracks',  tracks.post_handler)
    app.router.add_put(     '/tracks',  tracks.put_handler)
    app.router.add_delete(  '/tracks',  tracks.delete_handler)
    #tracks variable context access
    app.router.add_get(     '/tracks/{id}',  tracks.get_handler)
    app.router.add_delete(  '/tracks/{id}',  tracks.delete_handler)
    app.router.add_put(     '/tracks/{id}',  tracks.put_handler)