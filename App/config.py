import os


def load_config(app, overrides):
    if os.path.exists(os.path.join("./App", "custom_config.py")):
        app.config.from_object("App.custom_config")
    else:
        app.config.from_object("App.default_config")
    app.config.from_prefixed_env()

    # Normalise legacy "postgres://" scheme that SQLAlchemy 1.4+ rejects.
    # This catches URIs injected via the FLASK_SQLALCHEMY_DATABASE_URI env var
    # as well as those already set by default_config / custom_config.
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("postgres://"):
        app.config["SQLALCHEMY_DATABASE_URI"] = uri.replace(
            "postgres://", "postgresql://", 1
        )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["PREFERRED_URL_SCHEME"] = "https"
    app.config["UPLOADED_PHOTOS_DEST"] = "App/uploads"
    app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
    app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
    app.config["JWT_COOKIE_SECURE"] = True #temp
    app.config["JWT_ACCESS_COOKIE_SAMESITE"] = "Lax"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["FLASK_ADMIN_SWATCH"] = "darkly"
    for key in overrides:
        app.config[key] = overrides[key]
