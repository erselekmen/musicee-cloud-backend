import hvac
import mysql.connector
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

app = FastAPI()

# Vault configuration
vault_url = 'http://a6e62195f6e8c4599bc28b66962030ce-3eb8dbb9a66ef28b.elb.eu-central-1.amazonaws.com:8200'
vault_role = 'my-role'
vault_token = 'your-vault-token-here'  # Replace this with the actual Vault token
mysql_host = '54.93.70.239'
mysql_database = 'mysql'
client = hvac.Client(url=vault_url, token=vault_token)


def fetch_credentials(client, role):
    credentials = client.secrets.database.generate_credentials(name=role)
    db_username = credentials['data']['username']
    db_password = credentials['data']['password']
    lease_id = credentials['lease_id']
    lease_duration = credentials['lease_duration']
    return db_username, db_password, lease_id, lease_duration


def renew_lease(client, lease_id):
    try:
        response = client.sys.renew_lease(lease_id=lease_id)
        new_lease_duration = response['lease_duration']
        print(f"Lease renewed. New lease duration: {new_lease_duration} seconds")
        return new_lease_duration
    except Exception as e:
        print(f"Error renewing lease: {e}")
        return None


def connect_to_mysql(host, user, password, database):
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = connection.cursor()
        cursor.execute('SELECT DATABASE()')
        result = cursor.fetchone()
        print(f"Connected to database: {result[0]}")
        cursor.close()
        connection.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        connection = None
    return connection


@app.on_event("startup")
async def startup_db_client():
    db_username, db_password, lease_id, lease_duration = fetch_credentials(client, vault_role)
    app.mysql_connection = connect_to_mysql(mysql_host, db_username, db_password, mysql_database)

    @repeat_every(seconds=lease_duration // 2)  # This will run the function periodically
    def renew_mysql_lease():
        new_lease_duration = renew_lease(client, lease_id)
        if new_lease_duration is None:
            print("Fetching new credentials as the lease renewal failed or the lease expired.")
            db_username, db_password, lease_id, lease_duration = fetch_credentials(client, vault_role)
            app.mysql_connection = connect_to_mysql(mysql_host, db_username, db_password, mysql_database)
        else:
            print(f"Lease renewed successfully for another {new_lease_duration} seconds")

    renew_mysql_lease()
