"""
This script assumes an empty database and loads the master data.
"""

import pandas
from lib import my_env
from lib import sqlstore
from lib.sqlstore import *

if __name__ == '__main__':
    cfg = my_env.init_env("qif", __file__)
    logging.info("Start Application")
    sql_eng = sqlstore.init_session(cfg["Main"]["db"])
    master = cfg["Main"]["master"]
    banks = {}
    accountfields = ["name", "number", "type", "code"]
    df = pandas.read_excel(master)
    for row in df.iterrows():
        xl = row[1].to_dict()
        bank = xl["bank"]
        try:
            bank_id = banks[bank]
        except KeyError:
            props = dict(name=bank)
            bank_rec = Bank(**props)
            sql_eng.add(bank_rec)
            sql_eng.flush()
            sql_eng.refresh(bank_rec)
            banks[bank] = bank_rec.id
            bank_id = banks[bank]
        props = dict(bank_id=bank_id)
        for fld in accountfields:
            if pandas.notnull(xl[fld]):
                props[fld] = xl[fld]
        account_rec = Account(**props)
        sql_eng.add(account_rec)
    sql_eng.commit()
    logging.info("End Application")
