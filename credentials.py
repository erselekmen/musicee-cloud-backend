import hvac
import mysql.connector
import time


def fetch_credentials(client, role):
    credentials = client.secrets.database.generate_credentials(name=role)
    db_username = credentials['data']['username']
    db_password = credentials['data']['password']
    return db_username, db_password


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


def main():
    vault_url = 'a6e62195f6e8c4599bc28b66962030ce-3eb8dbb9a66ef28b.elb.eu-central-1.amazonaws.com:8200'
    vault_role = 'my-role'
    vault_token = 'your-vault-token'
    mysql_host = '192.168.23.43'
    mysql_database = 'mysql'

    client = hvac.Client(url=vault_url, token=vault_token)

    while True:
        db_username, db_password = fetch_credentials(client, vault_role)

        connect_to_mysql(mysql_host, db_username, db_password, mysql_database)

        time.sleep(300)


if __name__ == '__main__':
    main()
