import os


def get_postgres_uri():
    host = os.environ.get("DB_HOST", "localhost")
    port = 5432
    password = os.environ.get("DB_PASSWORD")
    user = os.environ.get('DB_USER', 'allocation')
    db_name = "allocation"
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_api_url():
    host = os.environ.get('API_HOST', '127.0.0.1')
    port = 5000
    return f"http://{host}:{port}"
