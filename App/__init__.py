# App package initialiser
#
# Deliberately empty of star-imports.
#
# The old pattern:
#
#   from .models import *
#   from .views import *
#   from .controllers import *
#   from .main import *
#
# caused a circular-import crash on startup:
#
#   App/__init__.py          starts loading App package
#     → from .views import * → views/index.py
#       → from App.controllers import …  → controllers/__init__.py
#         → from .box import …  → controllers/box.py
#           → from App.models import Box   ← FAILS
#                                            App.models is still being
#                                            initialised; Box not yet defined
#
# Each sub-package (models, views, controllers, main) is imported explicitly
# by the code that needs it (e.g. App.main, wsgi.py) rather than being
# re-exported from this file.  This keeps the import graph acyclic and lets
# Python fully initialise each module before anything else references it.
