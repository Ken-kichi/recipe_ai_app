import urllib.parse
import os
import dotenv

from azure.identity import DefaultAzureCredential


def get_connection_uri():
    dotenv.load_dotenv()
    dbhost = os.environ['PGHOST']
    dbname = os.environ['PGDATABASE']
    dbuser = urllib.parse.quote(os.environ['PGUSER'])
    sslmode = os.environ['PGSSLMODE']
    password = os.environ['PGPASSWORD']

    credential = DefaultAzureCredential()

    db_uri = f"postgresql://{dbuser}:{password}@{dbhost}/{dbname}?sslmode={sslmode}"
    return db_uri
