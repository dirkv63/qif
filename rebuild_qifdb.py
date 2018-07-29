"""
This procedure will rebuild the sqlite database
"""

import logging
from lib import my_env
from lib import sqlstore

cfg = my_env.init_env("qif", __file__)
logging.info("Start application")
qif = sqlstore.DirectConn(cfg)
qif.rebuild()
logging.info("sqlite database qif rebuild")
logging.info("End application")
