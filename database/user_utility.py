from database.connection import databaseConfig


# ================= CATEGORY =================
def show_category(category, min_price=None, max_price=None):
    db = databaseConfig()
    cursor = db.cursor()

    sql = """
        SELECT *
        FROM products
        WHERE LOWER(category) = LOWER(?)
        AND active = 1
    """
    values = [category]

    if min_price:
        sql += " AND price >= ?"
        values.append(min_price)

    if max_price:
        sql += " AND price <= ?"
        values.append(max_price)

    cursor.execute(sql, tuple(values))
    items = cursor.fetchall()

    cursor.close()
    db.close()
    return items


# ================= SEARCH =================
def searchProductsForUser(query: str = ""):
    db = databaseConfig()
    cursor = db.cursor()

    sql = """
        SELECT PRODUCTID, NAME, PRICE, STOCK, IMAGE_URL
        FROM products
        WHERE ACTIVE = 1
    """
    values = []

    if query:
        sql += " AND LOWER(NAME) LIKE LOWER(?)"
        values.append(f"%{query}%")

    cursor.execute(sql, values)
    products = cursor.fetchall()

    print("SEARCH:", query)       # DEBUG
    print("RESULT:", products)   # DEBUG

    cursor.close()
    db.close()
    return products


# ================= ORDERS =================
def myOrders(userid):
    db = databaseConfig()
    cursor = db.cursor()

    query = """
        SELECT 
            o.ORDER_ID,
            o.PRODUCT_NAME,
            o.PRODUCT_PRICE,
            o.QUANTITY,
            o.TOTAL_PRICE,
            p.IMAGE_URL,   
            o.ORDER_STATUS,
            o.PAYMENT_STATUS,
            o.CREATED_AT
        FROM ORDERS o
        JOIN PRODUCTS p ON o.PRODUCT_ID = p.PRODUCTID
        WHERE o.USER_ID = ?
        ORDER BY o.CREATED_AT DESC
    """

    cursor.execute(query, (userid,))
    orders = cursor.fetchall()

    cursor.close()
    db.close()
    return orders


# ================= PLACE ORDER =================
def placeOrder(userid, fullname, phone, address, city, pincode,
               total_amount, cart_items, payment_method, payment_status):

    db = databaseConfig()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT COALESCE(MAX(ORDER_ID), 0) + 1 FROM ORDERS")
        order_id = cursor.fetchone()[0]

        for item in cart_items:

            cursor.execute(
                "SELECT STOCK FROM PRODUCTS WHERE PRODUCTID = ?",
                (item["PRODUCTID"],)
            )
            product = cursor.fetchone()

            if not product or product[0] < item["QUANTITY"]:
                db.rollback()
                return False, "Insufficient stock"

            cursor.execute("""
                INSERT INTO ORDERS (
                    ORDER_ID, USER_ID, PRODUCT_ID, PRODUCT_NAME,
                    PRODUCT_PRICE, QUANTITY, IMAGE_URL,
                    PAYMENT_METHOD, PAYMENT_STATUS
                )
                VALUES (?, ?, ?, ?, ?, ?, 
                    (SELECT IMAGE_URL FROM PRODUCTS WHERE PRODUCTID = ?),
                    ?, ?
                )
            """, (
                order_id,
                userid,
                item["PRODUCTID"],
                item["NAME"],
                item["PRICE"],
                item["QUANTITY"],
                item["PRODUCTID"],
                payment_method,
                payment_status
            ))

            cursor.execute("""
                UPDATE PRODUCTS
                SET STOCK = STOCK - ?
                WHERE PRODUCTID = ?
            """, (item["QUANTITY"], item["PRODUCTID"]))

        cursor.execute("DELETE FROM CART WHERE USERID = ?", (userid,))
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
    cursor = db.cursor()

    cursor.execute("""
        SELECT USERID, NAME, EMAIL, PHONE_NUMBER, PROFILE_IMAGE
        FROM USERS
        WHERE USERID = ? AND STATUS = 1
    """, (user_id,))

    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user


# ================= CART =================
def getUserCartItems(user_id):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
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
        WHERE C.USERID = ?
    """, (user_id,))

    results = cursor.fetchall()
    cursor.close()
    db.close()
    return results


def getProductById(productid):
    db = databaseConfig()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM PRODUCTS WHERE PRODUCTID=?", (productid,))
    product = cursor.fetchone()
    cursor.close()
    db.close()
    return product


def getCartItem(user_id, product_id):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM CART
        WHERE USERID = ? AND PRODUCTID = ?
    """, (user_id, product_id))

    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result


def insertCartItem(user_id, product_id, price):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO CART (USERID, PRODUCTID, QUANTITY, PRICE)
        VALUES (?, ?, 1, ?)
    """, (user_id, product_id, price))

    db.commit()
    cursor.close()
    db.close()


def increaseCartQuantity(user_id, product_id):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE CART
        SET QUANTITY = QUANTITY + 1
        WHERE USERID = ? AND PRODUCTID = ?
    """, (user_id, product_id))

    db.commit()
    cursor.close()
    db.close()


def removeFromCart(user_id, product_id):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM CART
        WHERE USERID = ? AND PRODUCTID = ?
    """, (user_id, product_id))

    db.commit()
    cursor.close()
    db.close()


def updateCartQuantity(quantity, user_id, product_id):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE CART
        SET QUANTITY = ?
        WHERE USERID = ? AND PRODUCTID = ?
    """, (quantity, user_id, product_id))

    db.commit()
    cursor.close()
    db.close()


def getPopularProducts(limit=6):
    db = databaseConfig()
    cursor = db.cursor()

    cursor.execute("""
        SELECT PRODUCTID, NAME, PRICE, IMAGE_URL, STOCK
        FROM PRODUCTS
        WHERE ACTIVE = 1
        ORDER BY PRODUCTID DESC
        LIMIT ?
    """, (limit,))

    return cursor.fetchall()