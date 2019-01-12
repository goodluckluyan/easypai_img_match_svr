# -*- coding:utf-8 -*-
import pymysql
import mylog
from Config import cfg

class DatabaseOpt:
    def __init__(self, host, username, passwd, dbname):
        self.dbhost = host
        self.dbuser = username
        self.dbpasswd = passwd
        self.db = dbname
        self.db_cnn = None

    def __del__(self):
        if self.db_cnn != None:
            self.db_cnn.close()

    def cnn_db(self):
        try:
            # 打开数据库连接
            self.db_cnn = pymysql.connect(self.dbhost, self.dbuser, self.dbpasswd, self.db)
            return True
        except pymysql.Error as e:
            mylog.logger.info('execut sql happen error(%s)!' % e)
            return False


    def exesql(self, sql, row):
        if self.db_cnn is None:
            return 1
        # 使用cursor()方法获取操作游标
        cursor = self.db_cnn.cursor()
        ret = 0
        try:
            # 执行sql语句
            self.db_cnn.ping(reconnect=True)
            mylog.logger.info("execut sql:%s" % sql)
            cursor.execute(sql)
            # 提交到数据库执行
            self.db_cnn.commit()
            record = cursor.fetchall()
            if len(record) > 0:
                row.append(list(record))
            mylog.logger.info("execut sql succuess!")
        except pymysql.Error as e:
            # 如果发生错误则回滚
            self.db_cnn.rollback()
            mylog.logger.info('execut sql happen error(%s)!' % e)
            ret = 1

        return ret

#db = DatabaseOpt("211.159.160.241", "root", "123456", "easypai")
db = DatabaseOpt(cfg.DB_Host, cfg.DB_User, cfg.DB_Password, cfg.DB_Name)

if __name__ == '__main__':
    db.cnn_db()
    row = []
    sql = 'select * from MatchSession ;'
    db.exesql(sql, row)
    for i in row[0]:
        print(i)