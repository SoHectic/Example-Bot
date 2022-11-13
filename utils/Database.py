import pymysql
from utils.Logger import Logger

connection = pymysql.connect(
            host='raspberrypi',
            user='pi',
            password='',
            database='Queues',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

connection2 = pymysql.connect(
            host='raspberrypi',
            user='pi',
            password='',
            database='Guilds',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
i = 0

class Database:

    #########################################################################
    # Methods used to update, add, delete or create items related to queues #
    #########################################################################
    def updateSong(table, value, db:str = None):
        """Adds a song to the specified queue"""
        if db == None:
            Logger.log("The db was missing when trying to get information.")
        elif db == "queues":
            cxn = connection
        elif db == "guilds":
            cxn = connection2
        
        with connection.cursor() as cursor:
            sql = "INSERT INTO `{}` (id, song) VALUES (0, '{}')".format(table, value)
            connection.ping()
            cursor.execute(sql)
            connection.commit()
            connection.close()

    def delete(table, field, value, guildID, botID, db: str = None):
        """Remove a field from a table identified by guild and bot id"""
        if db == None:
            Logger.log("The db was missing when trying to get information.")
        elif db == "queues":
            cxn = connection
        elif db == "guilds":
            cxn = connection2
        
        with connection.cursor() as cursor:
            sql = "DELETE FROM `{}` WHERE `{}` = `{}` AND guild_id = {} AND bot_id = {}".format(table, field, value, guildID, botID)
            print(sql)
            connection.ping()
            cursor.execute(sql)
            connection.commit()
            connection.close()

    def load(tableName: str = None, db:str = None):
        """Loads the queue that is selected"""
        if db == None:
            Logger.log("The db was missing when trying to get information.")
        elif db == "queues":
            cxn = connection
        elif db == "guilds":
            cxn = connection2

        if not tableName:
            results = "You must add a queue name."
            return results
            
        with connection.cursor() as cursor:
            sql = "SELECT song FROM `{}`".format(tableName)
            connection.ping()
            cursor.execute(sql)
            results = cursor.fetchall()
            return results
    

    ###################
    # General Methods #
    ###################
    def get(field, table, guildID, botID, db:str = None):
        """Returns a fields info based off guild and bot id"""
        if db == None:
            Logger.log("The db was missing when trying to get information.")
        elif db == "queues":
            cxn = connection
        elif db == "guilds":
            cxn = connection2


        with cxn.cursor() as cursor:
            sql = "SELECT {} FROM `{}` WHERE guild_id={} AND bot_id={}".format(field, table, guildID, botID)
            cxn.ping()
            cursor.execute(sql)
            result = cursor.fetchall()
            cxn.close()
            return result

    def remove(table: str=None, db:str = None):
        """Drop the specified table"""
        if db == None:
            Logger.log("The db was missing when trying to get information.")
        elif db == "queues":
            cxn = connection
        elif db == "guilds":
            cxn = connection2

        if table == None:
            results = "You must add a table name"
            return results

        with connection.cursor() as cursor:
            sql = "DROP TABLE IF EXISTS `{}`".format(table)
            print(sql)
            connection.ping()
            cursor.execute(sql)
            connection.commit()
            connection.close()

    def create():
        pass


    ###################
    # Prefix Methods #
    ###################
    def createPrefix(guildId, clientId):
        """Creates a prefix entry for the specified guild and bot"""

        with connection2.cursor() as cursor:
            sql = "INSERT INTO guild_info (guild_id, prefix, bot_id) VALUES (%s,%s,%s)"
            connection2.ping()
            cursor.execute(sql, (guildId, "!", clientId))
            connection2.commit()

    def updatePrefix(prefix: str, guildId: int, clientId: int):
        """Updates the prefix for the specified guild and bot"""

        with connection2.cursor() as cursor:
            sql = "UPDATE guild_info SET prefix =%s WHERE (guild_id =%s AND bot_id =%s)"
            connection2.ping()
            cursor.execute(sql, (prefix, guildId, clientId))
            connection2.commit()

    def get_prefix(guildId, clientId):
        with connection2.cursor() as cursor:
            sql = "SELECT prefix FROM guild_info WHERE guild_id =%s AND bot_id =%s"
            connection2.ping()
            cursor.execute(sql, (guildId, clientId))
            results = cursor.fetchone()
            return results

