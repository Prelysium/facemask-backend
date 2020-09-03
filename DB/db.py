import sqlite3
from sqlite3 import Error
from config import config_import as conf

DB_CONF = conf.get_config_data_by_key("db")
DB_FILE_PATH = DB_CONF["DB_FILE_PATH"]
COUNTER_TABLE = DB_CONF["COUNTER_TABLE"]
ID_COLUMN = DB_CONF["ID_COLUMN"]
COUNT_COLUMN = DB_CONF["COUNT_COLUMN"]
ID_IN = DB_CONF["ID_IN"]
ID_OUT = DB_CONF["ID_OUT"]
SELECT_TEMPLATE = DB_CONF["SELECT_TEMPLATE"]


def initialize_database():
    """
    Initialize the database file,
        counter table and
        set starting values as 0 for in/out counters
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE_PATH)
        c = conn.cursor()
        # create counter table
        c.execute(
            "CREATE TABLE {} ([{}] str UNIQUE, [{}] INTEGER)".format(
                COUNTER_TABLE, ID_COLUMN, COUNT_COLUMN
            )
        )
        # insert in/out counts with value 0
        c.execute(
            'insert into {} values ("{}", 0), ("{}", 0)'.format(
                COUNTER_TABLE, ID_IN, ID_OUT
            )
        )

        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def reset_counters():
    """Resets occupancy counters to 0"""
    db = CounterDB()
    db.update_in(0)
    db.update_out(0)


class CounterDB:
    """
    Opens a connection to the sqlite database and implements functionality
    to get/update infromation in the COUNTER table

    Attributes:
        conn : Connection to database
    """

    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE_PATH)

    def __del__(self):
        self.conn.close()

    def in_count(self):
        """
        Get the number of people that went inside the given space

        Returns:
            (int): Total number of people that went in
        """
        c = self.conn.cursor()
        count_in_query = c.execute(
            SELECT_TEMPLATE.format(COUNT_COLUMN, COUNTER_TABLE, ID_COLUMN, ID_IN)
        )
        count_in = count_in_query.fetchall()[0][0]
        return count_in

    def out_count(self):
        """
        Get the number of people that left the given space

        Returns:
            (int): Total number of people that went out
        """
        c = self.conn.cursor()
        count_out_query = c.execute(
            SELECT_TEMPLATE.format(COUNT_COLUMN, COUNTER_TABLE, ID_COLUMN, ID_OUT)
        )
        count_out = count_out_query.fetchall()[0][0]
        return count_out

    def in_current(self):
        """
        Get the current number of people inside the given space

        Returns:
            (int): Current number of people inside the given space
        """
        return self.in_count() - self.out_count()

    def update_in(self, count_in):
        """
        Update information in database about the total number of people that
        went inside the given space

        Args:
            count_in (int): Number to update database with
        """
        c = self.conn.cursor()
        c.execute(
            "update {} set {}={} where {}='{}'".format(
                COUNTER_TABLE, COUNT_COLUMN, count_in, ID_COLUMN, ID_IN
            )
        )
        self.conn.commit()

    def update_out(self, count_out):
        """
        Update information in database about the total number of people that
        went out of the given space

        Args:
            count_out (int): Number to update database with
        """
        # in_count = self.in_count()
        # if count_out > in_count:
        #     count_out = in_count

        c = self.conn.cursor()
        c.execute(
            "update {} set {}={} where {}='{}'".format(
                COUNTER_TABLE, COUNT_COLUMN, count_out, ID_COLUMN, ID_OUT
            )
        )
        self.conn.commit()
