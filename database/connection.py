import mysql.connector as SQLC

# database configuration
def databaseConfig():
    db_config = SQLC.connect(
        host='localhost',
        user = 'root',
        password='root',
        database = 'ecommerce1'
    )
    return db_config
