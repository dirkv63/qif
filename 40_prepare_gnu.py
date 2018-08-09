"""
This script will prepare the GNU transaction table by removing double entries from the transactions table.
"""

from lib import my_env
from lib import sqlstore
from lib.sqlstore import *


if __name__ == '__main__':
    cfg = my_env.init_env("qif", __file__)
    logging.info("Start Application")
    sql_eng = sqlstore.init_session(cfg["Main"]["db"])

    # Get Account names and ids for reference in transactions
    accounts = {}
    acc_names = {}
    account_recs = sql_eng.query(Account).all()
    for rec in account_recs:
        accounts[rec.name] = rec
        acc_names[str(rec.id)] = rec.name

    for account in account_recs:
        tx = sql_eng.query(Transaction).filter_by(account_id=account.id).all()
        li = my_env.LoopInfo(account.name, 100)
        cat_account_name = "[{n}]".format(n=account.name)
        for rec in tx:
            li.info_loop()
            recdic = object_as_dict(rec)
            if account.type == "effect":
                # Convert transfer_id back to account
                if recdic["transfer_id"]:
                    recdic["category"] = "[{a}]".format(a=acc_names[str(recdic["transfer_id"])])
                gnutx = Gnutx(**recdic)
                sql_eng.add(gnutx)
            else:
                # Check if this is a transfer transaction: category is known account
                try:
                    tx_account = recdic["category"][1:-1]
                    dup_account = accounts[tx_account]
                except TypeError:
                    # Category not defined. Use payee.
                    recdic["category"] = recdic["payee"]
                    gnutx = Gnutx(**recdic)
                    sql_eng.add(gnutx)
                except KeyError:
                    # Category is not an account, so load the record
                    gnutx = Gnutx(**recdic)
                    sql_eng.add(gnutx)
                else:
                    # Category is an account - check if transaction has been loaded from other account.
                    # More than one record can exist, e.g. for more than 1 bancontact transaction on same day.
                    dup_rec = sql_eng.query(Gnutx).filter_by(account_id=dup_account.id, amount=recdic["amount"]*(-1),
                                                             date=recdic["date"],
                                                             category=cat_account_name).first()
                    if not dup_rec:
                        # Duplicate record not stored, so store this transaction now.
                        gnutx = Gnutx(**recdic)
                        sql_eng.add(gnutx)
        sql_eng.commit()
        li.end_loop()
