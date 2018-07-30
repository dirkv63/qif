"""
This script will find all qif files in qif dump directory, then send each file to process_qif for load in transaction
table.
"""

# Allow lib to library import path.
import os
import logging
from lib import my_env
from lib.my_env import run_script
from lib import sqlstore
from lib.sqlstore import *
from sqlalchemy.orm.exc import *



cfg = my_env.init_env("qif", __file__)
logging.info("Start Application")
script = "report_account"
(fp, filename) = os.path.split(__file__)
sql_eng = sqlstore.init_session(cfg["Main"]["db"])
code_query = sql_eng.query(Account)
accounts = sql_eng.query(Account).filter(Account.type != "effect").all()
for account in accounts:
    code = account.code
    logging.info("Run script: {s}.py -c {code}".format(s=script, code=code))
    run_script(fp, "{s}.py".format(s=script), "-c", code)
logging.info("End Application")
