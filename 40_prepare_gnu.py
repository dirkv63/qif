"""
This script will prepare the GNU transaction table by removing double entries from the transactions table.
"""

import argparse
import sys
from lib import my_env
from lib import sqlstore
from lib.sqlstore import *
from sqlalchemy.orm.exc import *


if __name__ == '__main__':
    cfg = my_env.init_env("qif", __file__)
    logging.info("Start Application")
    sql_eng = sqlstore.init_session(cfg["Main"]["db"])

    # Get Account names and ids for reference in transactions
    accounts = {}
    account_recs = sql_eng.query(Account).all()
    for rec in account_recs:
        accounts[rec.name] = rec

    for account in account_recs:
        tx = sql_eng.query(Transaction).filter_by(account_id=account.id).all()
        li = my_env.LoopInfo(account.name, 100)
        cat_account_name = "[{n}]".format(n=account.name)
        for rec in tx:
            li.info_loop()
            recdic = object_as_dict(rec)
            if account.type == "effect":
                gnutx = Gnutx(**recdic)
                sql_eng.add(gnutx)
            else:
                # Check if this is duplicate transaction
                try:
                    dup_account = accounts[recdic["category"]]
                except KeyError:
                    # Category is not an account, so load the record
                    gnutx = Gnutx(**recdic)
                    sql_eng.add(gnutx)
                else:
                    # Category is an account - check if record exist already
                    try:
                        dup_rec = sql_eng.query(Gnutx).filter_by(account_id=dup_account.id, amount=recdic["amount"]*(-1),
                                                                 date=recdic["date"],
                                                                 category=cat_account_name)
                        """
                        print("Query: {q}".format(q=str(dup_rec)))
                        print("account_id: {aid} - amount: {am} - date: {dt} - cat: [{cat}]".format(aid=dup_account.id,
                                                                                                  am=recdic["amount"]*(-1),
                                                                                                  dt=recdic["date"],
                                                                                                  cat=cat_account_name))
                        sys.exit()
                        """
                    except NoResultFound:
                        # Duplicate record not stored, do it now.
                        gnutx = Gnutx(**recdic)
                        sql_eng.add(gnutx)
        sql_eng.commit()
        li.end_loop()
