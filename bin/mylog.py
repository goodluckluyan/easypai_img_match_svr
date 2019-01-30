#! /usr/bin/python
# encoding:utf-8

# 日志
import logging
import re
from logging.handlers import TimedRotatingFileHandler

logfile = "log"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
fh = TimedRotatingFileHandler( logfile, when='D', interval=1, backupCount=30)
fh.suffix = '%y-%m-%d.log'
fh.extMatch = re.compile("~\d{4}-\d{2}-\d{2}.log$")
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)
