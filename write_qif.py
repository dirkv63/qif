"""
This script will write a qif file for loading into GnuCash. The filename defines the account.

Issue list:
- split account need to be added.
"""

import argparse
import sys
from lib import my_env
from lib import sqlstore
from lib.sqlstore import *
from sqlalchemy.orm.exc import *


def get_amount(item):
    """
    Remove commas from amount and convert to float.

    :param item: Line containing amount

    :return:
    """
    if len(item) == 1:
        amount = "0"
    else:
        amount = item[1:].replace(",", "")
    return float(amount)


def get_date(item):
    """
    Date is in format d/m'yy. Return date in string format and handles the Y2K problem.

    :param item:

    :return:
    """
    if item.count("/") == 2:
        [d, m, yr] = item[1:].split("/")
        return "19{yr}-{m:02d}-{d:02d}".format(yr=yr, m=int(m), d=int(d))
    else:
        [dm, yr] = item[1:].split("'")
        [d,m] = dm.split("/")
        return "20{yr}-{m:02d}-{d:02d}".format(yr=yr, m=int(m), d=int(d))

def get_cat(item):
    try:
        return "transfer_id", accounts[item[2:-1]]
    except KeyError:
        return "category", item[1:]

if __name__ == '__main__':
    # Configure command line arguments
    parser = argparse.ArgumentParser(
        description="Write QIF file"
    )
    parser.add_argument('-c', '--code', type=str, required=True,
                        help='Please provide the account code.')
    args = parser.parse_args()
    cfg = my_env.init_env("qif", __file__)
    logging.info("Arguments: {a}".format(a=args))
    sql_eng = sqlstore.init_session(cfg["Main"]["db"])
    tx2qif = my_env.tx2qif
    split2qif = my_env.split2qif

    # Get account information
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
    account_type = account_rec.type
    account_qif = account_rec.qiftype
    accounts = {}
    if account_type == "effect":
        tx2qif["amount"] = "$"
        account_recs = sql_eng.query(Account).all()
        for rec in account_recs:
            accounts[str(rec.id)] = rec.name


    # Get outfile
    loaddir = cfg["Main"]["loaddir"]
    fn = os.path.join(loaddir, "{code}.qif".format(code=code))
    fh = open(fn, "w")
    # Write type
    fh.write("!Type:{qif}\n".format(qif=account_qif))

    # Get all GnuCash transaction records for this account
    trans = sql_eng.query(Gnutx).filter_by(account_id=account_id).all()
    # new_tx flag is used to understand difference with split transaction. Do not write block delimiter for split tx.
    # First traansaction also is not a new transaction.
    first_tx = True
    for rec in trans:
        trans_dict = object_as_dict(rec)
        if trans_dict["master_id"]:
            # Get Category, memo and amount
            for fld in split2qif:
                if trans_dict[fld]:
                    line = "{qifid}{val}\n".format(qifid=split2qif[fld], val=trans_dict[fld])
                    fh.write(line)
        else:
            if first_tx:
                first_tx = False
            else:
                fh.write("^\n")
            for fld in tx2qif:
                if trans_dict[fld]:
                    if fld == "transfer_id":
                        line = "L[{val}]\n".format(val=accounts[str(trans_dict[fld])])
                    else:
                        line = "{qifid}{val}\n".format(qifid=tx2qif[fld], val=trans_dict[fld])
                    fh.write(line)
    fh.write("^\n")
    fh.close()
