"""
This script will prepare the GNU transaction table by removing double entries from the transactions table.
"""

from lib import my_env
from lib.my_env import run_script
from lib import sqlstore
from lib.sqlstore import *


cfg = my_env.init_env("qif", __file__)
logging.info("Start Application")
sql_eng = sqlstore.init_session(cfg["Main"]["db"])
(fp, filename) = os.path.split(__file__)
script = "write_qif"
account_recs = sql_eng.query(Account).all()
for rec in account_recs:
    code = rec.code
    logging.info("Run script: {s}.py -c {c}".format(s=script, c=code))
    run_script(fp, "{s}.py".format(s=script), "-c", code)
logging.info("End Application")
