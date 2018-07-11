#from models import users, albums, tracks  
from models.users import user_routes
from models.albums import album_routes 
from models.tracks import track_routes

def setup_routes(app):
    app.router.add_routes(user_routes)
    app.router.add_routes(track_routes)
    app.router.add_routes(album_routes)