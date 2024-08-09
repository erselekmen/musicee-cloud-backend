import hvac
import aiomysql
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Vault configuration
vault_url = 'http://a6e62195f6e8c4599bc28b66962030ce-3eb8dbb9a66ef28b.elb.eu-central-1.amazonaws.com:8200'
vault_role = 'my-role'
vault_token = ''  # Replace this with the actual Vault token
mysql_host = '54.93.70.239'
mysql_port = 3306
mysql_database = 'musicee_db'
client = hvac.Client(url=vault_url, token=vault_token)

async def fetch_credentials(client, role):
    try:
        credentials = client.secrets.database.generate_credentials(name=role)
        db_username = credentials['data']['username']
        db_password = credentials['data']['password']
        lease_id = credentials['lease_id']
        lease_duration = credentials['lease_duration']
        return db_username, db_password, lease_id, lease_duration
    except Exception as e:
        logging.error(f"Error fetching credentials from Vault: {e}")
        return None, None, None, None


async def renew_lease(client, lease_id):
    try:
        response = client.sys.renew_lease(lease_id=lease_id)
        new_lease_duration = response['lease_duration']
        print(f"Lease renewed. New lease duration: {new_lease_duration} seconds")
        return new_lease_duration
    except Exception as e:
        print(f"Error renewing lease: {e}")
        return None

async def connect_to_mysql(host, port, user, password, database):
    try:
        connection = await aiomysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            db=database,
            cursorclass=aiomysql.DictCursor,  # Use DictCursor
            autocommit=True
        )
        logging.info(f"Connected to database: {database} at {host}:{port} with user {user}")
    except aiomysql.Error as err:
        logging.error(f"Error connecting to database: {err}")
        connection = None
    return connection



@app.on_event("startup")
async def startup_db_client():
    db_username, db_password, lease_id, lease_duration = await fetch_credentials(client, vault_role)
    app.mysql_connection = await connect_to_mysql(mysql_host, mysql_port, db_username, db_password, mysql_database)

    @repeat_every(seconds=lease_duration // 2)
    async def renew_mysql_lease():
        nonlocal db_username, db_password, lease_id, lease_duration
        new_lease_duration = await renew_lease(client, lease_id)
        if new_lease_duration is None:
            print("Fetching new credentials as the lease renewal failed or the lease expired.")
            db_username, db_password, lease_id, lease_duration = await fetch_credentials(client, vault_role)
            app.mysql_connection = await connect_to_mysql(mysql_host, mysql_port, db_username, db_password, mysql_database)
        else:
            lease_duration = new_lease_duration
            print(f"Lease renewed successfully for another {new_lease_duration} seconds")

    await renew_mysql_lease()


async def get_mysql_connection():
    if not hasattr(app, 'mysql_connection') or app.mysql_connection is None:
        db_username, db_password, lease_id, lease_duration = await fetch_credentials(client, vault_role)
        if db_username is None or db_password is None:
            logging.error("Failed to retrieve credentials from Vault")
            return None
        app.mysql_connection = await connect_to_mysql(mysql_host, mysql_port, db_username, db_password, mysql_database)
    return app.mysql_connection


