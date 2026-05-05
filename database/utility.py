from database.connection import databaseConfig


# ---------------- USER ---------------- #

def checkUserExists(email):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute('SELECT userid FROM users WHERE email=?', (email,))
    exists = cursor.fetchone()

    cursor.close()
    db.close()
    return bool(exists)


def addUser(name, email, phone_number, password, profile_image=None,role='user'):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO users (NAME, EMAIL, PHONE_NUMBER, PASSWORD, PROFILE_IMAGE, ROLE)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, email, phone_number, password, profile_image, role))

    db.commit()
    cursor.close()
    db.close()


def getUserDetails(email):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("SELECT userid, password, role FROM users WHERE email=?", (email,))
    data = cursor.fetchone()

    cursor.close()
    db.close()
    return data


def getUserDetailsByID(userid):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE userid=?", (userid,))
    user = cursor.fetchone()

    cursor.close()
    db.close()
    return user


# ---------------- CATEGORY ---------------- #

def getCatagoriesFromDB():
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("SELECT DISTINCT(category) FROM products")
    categories = [row[0] for row in cursor.fetchall()]

    cursor.close()
    db.close()
    return categories


# ---------------- PRODUCTS ---------------- #

def getProductsFromDB(name='', category='', status=''):
    db = databaseConfig()
    cursor = db.cursor()

    query = "SELECT * FROM products WHERE 1=1"
    values = []

    if name:
        query += " AND NAME LIKE ?"
        values.append(f"%{name}%")

    if category:
        query += " AND CATEGORY = ?"
        values.append(category)

    if status:
        query += " AND ACTIVE = ?"
        values.append(status)

    cursor.execute(query, values)
    products = cursor.fetchall()

    cursor.close()
    db.close()
    return products


def addProductToDB(name, description, category, price, stock, active, image_url):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO products
        (NAME, DESCRIPTION, CATEGORY, PRICE, STOCK, ACTIVE, IMAGE_URL)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, description, category, price, stock, active, image_url))

    db.commit()
    cursor.close()
    db.close()


def getProductDetailsByID(productid):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM products WHERE PRODUCTID=?", (productid,))
    product = cursor.fetchone()

    cursor.close()
    db.close()
    return product


def updateProductInfo(name, description, category, price, stock, active, productid):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE products
        SET NAME=?, DESCRIPTION=?, CATEGORY=?, PRICE=?, STOCK=?, ACTIVE=?
        WHERE PRODUCTID=?
    """, (name, description, category, price, stock, active, productid))

    db.commit()
    cursor.close()
    db.close()
    return True


def updateProductStatus(productid, status=0):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE products SET ACTIVE=? WHERE PRODUCTID=?",
        (status, productid)
    )

    db.commit()
    cursor.close()
    db.close()
    return True


# ---------------- COUNTS ---------------- #

def totalProductsCount():
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]

    cursor.close()
    db.close()
    return count


def totalOrdersCount():
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]

    cursor.close()
    db.close()
    return count


def pendingOrdersCount():
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE ORDER_STATUS=?",
        ('PENDING',)
    )
    count = cursor.fetchone()[0]

    cursor.close()
    db.close()
    return count


def totalUsersCount():
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    cursor.close()
    db.close()
    return count


# ---------------- ORDERS ---------------- #

def getOrders(orderid="", product_name="", from_date="", to_date=""):
    db = databaseConfig()
    cursor = db.cursor()

    query = """
        SELECT ORDER_ID, PRODUCT_NAME, ORDER_STATUS, TOTAL_PRICE, CREATED_AT
        FROM ORDERS
        WHERE 1=1
    """
    values = []

    if orderid:
        query += " AND ORDER_ID = ?"
        values.append(orderid)

    if product_name:
        query += " AND PRODUCT_NAME LIKE ?"
        values.append(f"%{product_name}%")

    if from_date:
        query += " AND CREATED_AT > ?"
        values.append(from_date)

    if to_date:
        query += " AND CREATED_AT < ?"
        values.append(to_date)

    query += " ORDER BY CREATED_AT DESC"

    cursor.execute(query, values)
    orders = cursor.fetchall()

    cursor.close()
    db.close()
    return orders


# ---------------- USERS (ADMIN) ---------------- #

def usersDetails(name="", email="", role="user"):
    db = databaseConfig()
    cursor = db.cursor()

    query = """
        SELECT USERID, NAME, EMAIL, PHONE_NUMBER, ROLE, CREATED_AT, PROFILE_IMAGE
        FROM USERS
        WHERE 1=1
    """
    values = []

    if name:
        query += " AND NAME LIKE ?"
        values.append(f"%{name}%")

    if email:
        query += " AND EMAIL LIKE ?"
        values.append(f"%{email}%")

    if role:
        query += " AND ROLE = ?"
        values.append(role)

    query += " ORDER BY CREATED_AT DESC"

    cursor.execute(query, values)
    users = cursor.fetchall()

    cursor.close()
    db.close()
    return users


def updateAdminProfile(userid, name=None, phone=None, new_password=None):
    db = databaseConfig()
    cursor = db.cursor()

    if new_password:
        cursor.execute(
            "UPDATE USERS SET PASSWORD=? WHERE USERID=?",
            (new_password, userid)
        )
    else:
        cursor.execute(
            "UPDATE USERS SET NAME=?, PHONE_NUMBER=? WHERE USERID=?",
            (name, phone, userid)
        )

    db.commit()
    cursor.close()
    db.close()


def viewUserByAdmin(userid):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
        SELECT USERID, NAME, EMAIL, ROLE, STATUS, CREATED_AT
        FROM USERS
        WHERE USERID = ?
    """, (userid,))

    user = cursor.fetchone()

    cursor.close()
    db.close()
    return user