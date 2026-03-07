# blue prints are imported
# explicitly instead of using *
from .admin import setup_admin
from .auth import auth_views
from .file import file_views
from .index import index_views
from .location import location_views
from .user import user_views

views = [user_views, index_views, auth_views, file_views, location_views]
# blueprints must be added to this list
