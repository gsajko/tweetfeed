import sqlite3

class Database(object):
    path_to_db = "???"
    def __init__(self):
        self.conn = sqlite3.connect(path_to_db)
        self.c = self.conn.cursor()

    def check_table_exist(self, table_name):
    # TODO change hardcoded table name 
        try:
            self.c.execute(
                """SELECT * FROM information_schema.tables WHERE table_name = 'profiles' """
            )
            return True
        except:
            return False


    def create_table_profiles(self):
        try:
            self.c.execute(
                """CREATE TABLE profiles(id integer PRIMARY KEY, screen_name text NOT NULL, name text NOT NULL, description text NOT NULL, location text NOT NULL)"""
            )
            return True
        except:
            return False