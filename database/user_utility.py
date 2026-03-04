from flask import session
from database.connection import databaseConfig


# ================= CATEGORY =================
def show_category(category, min_price=None, max_price=None):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT *
        FROM products
        WHERE LOWER(category) = LOWER(%s)
        AND active = 1
    """
    values = [category]

    if min_price:
        sql += " AND price >= %s"
        values.append(min_price)

    if max_price:
        sql += " AND price <= %s"
        values.append(max_price)

    cursor.execute(sql, tuple(values))
    items = cursor.fetchall()

    cursor.close()
    db.close()
    return items


# ================= SEARCH =================
def searchProductsForUser(query: str = ""):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT PRODUCTID, NAME, PRICE, STOCK, IMAGE_URL
        FROM products
        WHERE ACTIVE = 1
    """
    values = []

    if query:
        sql += " AND NAME LIKE %s"
        values.append(f"%{query}%")

    cursor.execute(sql, values)
    products = cursor.fetchall()

    cursor.close()
    db.close()
    return products


# ================= ORDERS =================
def myOrders(userid):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT
        ORDER_ID,
        PRODUCT_NAME,
        PRODUCT_PRICE,
        QUANTITY,
        TOTAL_PRICE,
        IMAGE_URL,
        ORDER_STATUS,
        PAYMENT_STATUS,
        CREATED_AT
        FROM ORDERS
        WHERE USER_ID = %s
        ORDER BY CREATED_AT DESC
    """

    cursor.execute(query, (userid,))
    orders = cursor.fetchall()

    print("ORDERS FROM DB:", orders)

    cursor.close()
    db.close()
    return orders

# ================= PLACE ORDER =================

def placeOrder(userid, fullname, phone, address, city, pincode, total_amount, cart_items,payment_method,payment_status):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    try:
        # 1️⃣ generate ORDER_ID
        cursor.execute("SELECT IFNULL(MAX(ORDER_ID), 0) + 1 AS oid FROM ORDERS")
        order_id = cursor.fetchone()["oid"]

        for item in cart_items:
            # 2️⃣ check stock first
            cursor.execute(
                "SELECT STOCK FROM PRODUCTS WHERE PRODUCTID = %s",
                (item["PRODUCTID"],)
            )
            product = cursor.fetchone()

            if not product or product["STOCK"] < item["QUANTITY"]:
                db.rollback()
                return False, f"Insufficient stock for {item['NAME']}"

            # 3️⃣ insert order row
            cursor.execute(
                """
                INSERT INTO ORDERS (
                    ORDER_ID, USER_ID, PRODUCT_ID, PRODUCT_NAME,
                    PRODUCT_PRICE, QUANTITY, IMAGE_URL,
                    PAYMENT_METHOD, PAYMENT_STATUS
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    (SELECT IMAGE_URL FROM PRODUCTS WHERE PRODUCTID = %s),
                    %s, %s
                )
                """,
                (
                    order_id,
                    userid,
                    item["PRODUCTID"],
                    item["NAME"],
                    item["PRICE"],
                    item["QUANTITY"],
                    item["PRODUCTID"],
                    payment_method,
                    payment_status
                )
            )

            # 4️⃣ reduce stock (safe)
            cursor.execute(
                """
                UPDATE PRODUCTS
                SET STOCK = STOCK - %s
                WHERE PRODUCTID = %s
                """,
                (item["QUANTITY"], item["PRODUCTID"])
            )

        # 5️⃣ clear cart ONLY after everything succeeds
        cursor.execute("DELETE FROM CART WHERE USERID = %s", (userid,))
        db.commit()

        return True, "Order placed successfully"

    except Exception as e:
        db.rollback()
        print("ORDER ERROR:", e)
        return False, "Order failed"

    finally:
        cursor.close()
        db.close()


# ================= PROFILE =================
def getUserProfile(user_id):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT USERID, NAME, EMAIL, PHONE_NUMBER, GENDER, PROFILE_IMAGE
        FROM USERS
        WHERE USERID = %s AND STATUS = 1
    """

    cursor.execute(query, (user_id,))
    user = cursor.fetchone()

    cursor.close()
    db.close()
    return user


# ================= INTERNAL CART HELPER =================
def getUserCartItems(user_id):
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)

    query = """
        SELECT 
            C.CARTID,
            C.PRODUCTID,
            P.NAME,
            P.IMAGE_URL,
            C.QUANTITY,
            C.PRICE,
            (C.QUANTITY * C.PRICE) AS TOTAL_PRICE
        FROM CART C
        JOIN PRODUCTS P ON C.PRODUCTID = P.PRODUCTID
        WHERE C.USERID = %s;
    """

    cursor.execute(query, (user_id,))
    results = cursor.fetchall()

    cursor.close()
    db_config.close()

    return results


def getProductById(productid:int):
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PRODUCTS WHERE PRODUCTID=%s;", (productid,))
    product = cursor.fetchone()
    cursor.close()
    db_config.close()
    return product

def getCartItem(user_id, product_id):
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)

    query = """
        SELECT * FROM CART
        WHERE USERID = %s AND PRODUCTID = %s;
    """

    cursor.execute(query, (user_id, product_id))
    result = cursor.fetchone()

    cursor.close()
    db_config.close()

    return result

def insertCartItem(user_id, product_id, price):
    db_config = databaseConfig()
    cursor = db_config.cursor()

    query = """
        INSERT INTO CART (USERID, PRODUCTID, QUANTITY, PRICE)
        VALUES (%s, %s, 1, %s);
    """

    cursor.execute(query, (user_id, product_id, price))
    db_config.commit()

    cursor.close()
    db_config.close()


# increase cart quantity
def increaseCartQuantity(user_id, product_id):
    db_config = databaseConfig()
    cursor = db_config.cursor()

    query = """
        UPDATE CART
        SET QUANTITY = QUANTITY + 1,
            UPDATED_AT = CURRENT_TIMESTAMP
        WHERE USERID = %s AND PRODUCTID = %s;
    """

    cursor.execute(query, (user_id, product_id))
    db_config.commit()

    cursor.close()
    db_config.close()



# ================= REMOVE FROM CART =================
def removeFromCart(user_id:int, product_id:int):
    db_config = databaseConfig()
    cursor = db_config.cursor()

    query = """
        DELETE FROM CART
        WHERE USERID = %s AND PRODUCTID = %s;
    """

    cursor.execute(query, (user_id, product_id))
    db_config.commit()

    cursor.close()
    db_config.close()

def updateCartQuantity(quantity:int, user_id:int, product_id:int):

    db_config = databaseConfig()
    cursor = db_config.cursor()

    query = """
        UPDATE CART
        SET QUANTITY = %s,
            UPDATED_AT = CURRENT_TIMESTAMP
        WHERE USERID = %s AND PRODUCTID = %s;
    """

    cursor.execute(query, (quantity, user_id, product_id))
    db_config.commit()
    cursor.close()
    db_config.close()


# ================= POPULAR PRODUCTS (HOME PAGE) =================

def getPopularProducts(limit=6):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT PRODUCTID, NAME, PRICE, IMAGE_URL, STOCK
    FROM PRODUCTS
    WHERE ACTIVE = 1
    ORDER BY PRODUCTID DESC
    LIMIT %s
    """
    cursor.execute(query, (limit,))
    return cursor.fetchall()