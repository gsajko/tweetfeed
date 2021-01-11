import sqlite3


# def conn_to_db(path_to_db):
#     try:
#         conn = sqlite3.connect(path_to_db)
#         c = conn.cursor()
#     except sqlite3.Error as error:
#         print("Error while connecting to sqlite", error)

# def check_table_exist(table_name, path_to_db):
#     #todo think this through. should I create class for this?
#     # change hardcoded table name 
#     c = conn_to_db(path_to_db)
#     try:
#         c.execute(
#             """SELECT * FROM information_schema.tables WHERE table_name = 'profiles' """
#         )
#         return True
#     except:
#         return False


# def create_table_profiles(path_to_db):
#     c = conn_to_db(path_to_db)
#     try:
#         c.execute(
#             """CREATE TABLE profiles(id integer PRIMARY KEY, screen_name text NOT NULL, name text NOT NULL, description text NOT NULL, location text NOT NULL)"""
#         )
#         return True
#     except:
#         return False


# def checkTableExists(dbcon, tablename):
#     dbcur = dbcon.cursor()
#     try:
#         dbcur.execute("SELECT * FROM {}".format(tablename))
#         return True
#     except cx_Oracle.DatabaseError as e:
#         x = e.args[0]
#         if x.code == 942: ## Only catch ORA-00942: table or view does not exist error
#             return False
#         else:
#             raise e
#     finally:
#         dbcur.close()