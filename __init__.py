# Use PyMySQL as the MySQL driver (pure Python, no system libraries needed).
# If you prefer mysqlclient, install it and this block is simply skipped.
try:
    import MySQLdb  # noqa: F401
except ImportError:
    try:
        import pymysql

        pymysql.version_info = (2, 2, 1, "final", 0)  # satisfy Django's version check
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass
