# blue prints are imported
# explicitly instead of using *
from .admin import setup_admin
from .auth import auth_views
from .box import box_views
from .file import file_views
from .index import index_views
from .loan import loan_views
from .location import location_views
from .user import user_views
from .loan import loan_views
from .barcode import barcode_views
from .patron import patron_views
 
views = [
    user_views,
    index_views,
    auth_views,
    file_views,
    location_views,
    box_views,
    loan_views,
    barcode_views,
    patron_views,
]
# blueprints must be added to this list