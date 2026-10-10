from database.connection import get_db


def check_database_connection():
    """
    Check whether the application can successfully
    communicate with the MySQL database.
    """

    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 AS status")
            result = cursor.fetchone()

    return result