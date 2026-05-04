import mysql.connector as SQLC

# database configuration
def databaseConfig():
    db_config = SQLC.connect(
    host='localhost',
    user='jawahar',
    password='1234',
    database='ecommerce1'
    )
    return db_config
