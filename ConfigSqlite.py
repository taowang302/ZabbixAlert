import sqlite3
import os

class SqliteOprate():
    def __init__(self,sqlite_file, log):
        self.sqlite_file = sqlite_file
        self.log = log
        self.conn = self.get_conn()
        self.cursor = self.conn.cursor()

    def get_conn(self):
        if os.path.exists(self.sqlite_file):
            conn = sqlite3.connect(self.sqlite_file)
            return conn
        else:
            self.log.info("db file not exist, so create")
            return self.init_sqlite(self.sqlite_file)

    def init_sqlite(self, sqlite_file):
        conn = sqlite3.connect(sqlite_file)
        c = conn.cursor()
        c.execute('''CREATE TABLE SIHUAMONITOR
           (NAME           TEXT    NOT NULL,
           CODE CHAR(50) PRIMARY KEY      NOT NULL,
           DELAY        INT);''')
        conn.commit()
        return conn

    def check_exist(self, code):
        return_value = self.conn.execute("SELECT CODE FROM SIHUAMONITOR WHERE CODE='{}'".format(code)).fetchone()
        return return_value


    def insert(self, name, code, delay, mode=1):
        if mode:
            print(name, code, delay)
            if self.check_exist(code):
                self.update(delay=delay,code=code,name=name)
                return 1
            else:
                self.cursor.execute("INSERT INTO SIHUAMONITOR (NAME,CODE,DELAY) VALUES ('{}','{}',{})".format(name, code, delay))
                self.conn.commit()
                return 0
        else:
            self.cursor.execute("INSERT INTO SIHUAMONITOR (NAME,CODE,DELAY) VALUES ('{}','{}',{})".format(name, code, delay))
            self.conn.commit()
            return 0

    def update(self,code, delay, name):
        if self.check_exist(code):
            self.cursor.execute("UPDATE SIHUAMONITOR SET DELAY={} WHERE CODE='{}'".format(delay, code))
            self.conn.commit()
            return 1
        else:
            self.insert(name, code, delay,mode=0)
            return 0

    def delete(self,code):
        if self.check_exist(code):
            self.cursor.execute("DELETE FROM SIHUAMONITOR WHERE CODE='{}'".format(code))
            self.conn.commit()
            return 1
        else:
            return 0

    def get_code(self):
        code = self.cursor.execute("SELECT CODE FROM SIHUAMONITOR")
        return code.fetchall()

    def get_value(self,code):
        delay_time = self.cursor.execute("select DELAY from SIHUAMONITOR where CODE='{}'".format(code)).fetchone()
        self.log.debug("get delay:{}".format(delay_time))
        if delay_time:
            self.log.debug("return {} ==> {}".format(code, delay_time[0]))
            return int(delay_time[0])
        else:
            return 0

if __name__ == "__main__":
    sql = SqliteOprate("test.db")
    # print(sql.get_value("test"))
    sql.insert(name="测试", code="test", delay=10)
    print(sql.get_value("test"))