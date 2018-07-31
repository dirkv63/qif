"""
This script will extract information for a specific account and publish the information in excel.
"""
import argparse
import sys
from lib import my_env
from lib import sqlstore
from lib.sqlstore import *
from lib import write2excel
from sqlalchemy.orm.exc import *

if __name__ == '__main__':
    # Configure command line arguments
    parser = argparse.ArgumentParser(
        description="Account report"
    )
    parser.add_argument('-c', '--code', type=str, required=True,
                        help='Please provide the account code.')
    args = parser.parse_args()
    cfg = my_env.init_env("qif", __file__)
    logging.info("Arguments: {a}".format(a=args))
    sql_eng = sqlstore.init_session(cfg["Main"]["db"])

    tranfields = ["id", "master_id", "date", "payee", "category", "memo", "action", "name", "reconciled", "amount"]
    balance = 0
    res = []
    # Find Account ID
    code = args.code
    try:
        account_rec = sql_eng.query(Account).filter_by(code=code).one()
    except MultipleResultsFound:
        logging.critical("Multiple lines for Account code {code}".format(code=code))
        sys.exit(1)
    except NoResultFound:
        logging.critical("No lines for Account code {code}".format(code=code))
        sys.exit(1)

    account_id = account_rec.id
    trans = sql_eng.query(Transaction).filter((Transaction.account_id == account_id) |
                                              (Transaction.transfer_id == account_id)).order_by(Transaction.date,
                                                                                                Transaction.id).all()
    for tran_rec in trans:
        tran = object_as_dict(tran_rec)
        # Add balance for every account that is not split account
        row = {}
        for fld in tranfields:
            row[fld] = tran[fld]
        if not tran["master_id"]:
            balance += row["amount"]
        row["balance"] = balance
        res.append(row)

    # Update balance in account table
    account_rec.balance = balance
    sql_eng.commit()

    # Then write Report
    xl = write2excel.Write2Excel()
    xl.init_sheet(code)
    xl.write_content(res)

    fn = os.path.join(cfg["Main"]["reportdir"], "{code}.xlsx".format(code=code))
    xl.close_workbook(fn)
