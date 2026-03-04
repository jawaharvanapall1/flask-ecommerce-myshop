from database.connection import databaseConfig


# check user exists or not
def checkUserExists(email:str):
    # database accesss
    db_config = databaseConfig()
    cursor = db_config.cursor()
    cursor.execute('select userid from users where email=%s;', (email,))
    
    if cursor.fetchone():
        cursor.close()
        db_config.close()
        return True
    else:
        cursor.close()
        db_config.close()
        return False
    
# insert user data into db
def addUser(name: str, email: str, phone_number: str, password: str, profile_image: str = None):
    db = databaseConfig()
    cursor = db.cursor()

    query = """
        INSERT INTO users
        (NAME, EMAIL, PHONE_NUMBER, PASSWORD, PROFILE_IMAGE)
        VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (name, email, phone_number, password, profile_image))
    db.commit()
    cursor.close()
    db.close()

    

# get password and role form database
def getUserDetails(email:str, role:str=None):
    # database accesss
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)
    user_details_query = "select userid, password, role from users where email = %s;"
    if role:
        user_details_query =  "select userid, password, role from users where email = %s and role = %s"
        cursor.execute(user_details_query, (email,role))
    else:
        cursor.execute(user_details_query, (email,))
    data = cursor.fetchone()
    cursor.close()
    db_config.close()
    return data

# get user details by id
def getUserDetailsByID(userid:int, role:str=None):
    # database accesss
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)
    user_details_query = "select * from users where userid = %s;"
    
    cursor.execute(user_details_query, (userid,))
    user = cursor.fetchone()
    cursor.close()
    db_config.close()
    return user


## Get all categories from database
def getCatagoriesFromDB():
    db_config = databaseConfig()
    cursor = db_config.cursor()
    cursor.execute('select distinct(category) from products;')
    category_list = cursor.fetchall()
    for i in range(len(category_list)):
        category_list[i] = category_list[i][0]
    cursor.close()
    db_config.close()
    return category_list


## Get all products from database
def getProductsFromDB(name='', category='', status=''):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM products WHERE 1=1"
    values = []
    # Filter by product name
    if name:
        query += " AND NAME LIKE %s" # "SELECT * FROM products WHERE 1=1 AND NAME LIKE %s"
        values.append(f"%{name}%")
    # Filter by category
    if category:
        
        query += " AND CATEGORY = %s"
        values.append(category)
        
    # Filter by status
    if status:
        query += " AND ACTIVE = %s"
        values.append(status)
    cursor.execute(query, values)
    products = cursor.fetchall()
    # print(products[:5])
    cursor.close()
    db.close()
    return products




def addProductToDB(name, description, category, price, stock, active, image_url):
    db = databaseConfig()
    cursor = db.cursor()

    product_insert_query = """
        INSERT INTO products
        (NAME, DESCRIPTION, CATEGORY, PRICE, STOCK, ACTIVE, IMAGE_URL)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(
        product_insert_query,
        (name, description, category, price, stock, active, image_url)
    )

    db.commit()
    cursor.close()
    db.close()
    

# Total products
def totalProductsCount():
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM products;")
    products_count = cursor.fetchone()[0]

    cursor.close()
    db.close()
    return products_count

## Total Orders
def totalOrdersCount():
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM ORDERS;")
    orders_count = cursor.fetchone()[0]

    cursor.close()
    db.close()
    return orders_count

# Pending Orders
def pendingOrdersCount():
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE ORDER_STATUS = %s;",
        ('pending',)
    )
    pending_count = cursor.fetchone()[0]

    cursor.close()
    db.close()
    return pending_count

# Total Users
def totalUsersCount():
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM users;")
    users_count = cursor.fetchone()[0]

    cursor.close()
    db.close()
    return users_count



# get orders 
def getOrders(orderid:int = "", product_name:str= "", from_date='', to_date = ""):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    query = """select ORDER_ID,product_name,ORDER_STATUS, total_price,CREATED_AT 
    from orders where 1=1"""
    values = []
    if orderid:
        query += " and ORDER_ID= %s"
        values.append(orderid)
    if product_name:
        query += " and product_name like %s"
        values.append(f"%{product_name}%")
    if from_date:
        query += " and  CREATED_AT > %s"
        values.append(from_date)
    if to_date:
        query += " and CREATED_AT < %s"
        values.append(to_date)
    query += " Order by CREATED_AT desc;"
    cursor.execute(query, values)
    orders = cursor.fetchall()
    cursor.close()
    db.close()
    return orders


def toggleProduct(pid, status):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE products SET ACTIVE=%s WHERE PRODUCTID=%s",
        (status, pid)
    )

    db.commit()
    cursor.close()
    db.close()


# get users info 
def usersDetails(name:str, email:str,role:str='user'):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    query = "SELECT USERID, NAME, EMAIL, PHONE_NUMBER, ROLE, CREATED_AT, PROFILE_IMAGE FROM USERS WHERE 1=1"
    values = []

    if name:
        query += " AND NAME LIKE %s"
        values.append(f"%{name}%")

    if email:
        query += " AND EMAIL LIKE %s"
        values.append(f"%{email}%")

    if role:
        query += " AND ROLE = %s"
        values.append(role)

    query += " ORDER BY CREATED_AT DESC"

    cursor.execute(query, values)
    users = cursor.fetchall()

    cursor.close()
    db.close()
    return users


# update admin profile in database
def updateAdminProfile(new_password:str,userid:int):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
            UPDATE USERS
            SET PASSWORD=%s
            WHERE USERID=%s
        """, (new_password, userid))
    db.commit()
    cursor.close()
    db.close()



# get product details bt id
def getProductDetailsByID(productid:int):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    # FETCH PRODUCT
    cursor.execute(
        "SELECT * FROM products WHERE PRODUCTID = %s",
        (productid,)
    )
    product = cursor.fetchone()
    return product

# update product info in database
def updateProductInfo(name, description, category,price, stock, active, productid):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)
    update_query = """
            UPDATE products SET NAME=%s, DESCRIPTION=%s, CATEGORY=%s, PRICE=%s, STOCK=%s, ACTIVE=%s
            WHERE PRODUCTID=%s;
        """

    cursor.execute(update_query, (name, description, category,price, stock, active, productid))
    db.commit()
    return True

## Deactivate product in database
def updateProductStatus(productid, status:int=0):
    db = databaseConfig()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE products SET ACTIVE = %s WHERE PRODUCTID = %s",
        (status, productid)
    )
    db.commit()
    cursor.close()
    db.close()
    return True



## get view user
def viewUserByAdmin(userid):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT USERID, NAME, EMAIL, ROLE, STATUS, CREATED_AT "
        "FROM users WHERE USERID = %s",
        (userid,)
    )

    user = cursor.fetchone()

    cursor.close()
    db.close()
    return user




