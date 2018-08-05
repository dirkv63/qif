"""
This script will write a qif file for loading into GnuCash. The filename defines the account.
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

    # Get outfile
    loaddir = cfg["Main"]["loaddir"]
    fn = sys.path.join(loaddir, "{code}.qif".format(code=code))
    fh = open(fn, "w")

    # Get Account names and ids for reference in transactions
    accounts = {}
    code, ext = basename.split(".")
    if account_type == "effect":
        # Effect account statements are not in bank account statements!
        account_recs = sql_eng.query(Account).all()
        for rec in account_recs:
            accounts[rec.name] = rec.id

    # Get all GnuCash transaction records for this account
    trans = sql_eng.query(Gnutx).filter_by(account_id=account_id)


    # sys.exit("Successful execution")
    qifdump = fh.read()
    chunks = qifdump.split("\n^\n")
    account_type = False
    li = my_env.LoopInfo("Transactions", 100)
    for chunk in chunks:
        if len(chunk) == 0:
            break
        lines = chunk.split("\n")
        props = dict(account_id=account_id)
        master_id = False
        for line in lines:
            if line[0] == "D":
                props["date"] = get_date(line)
            elif (line[0] == "T") or (line[0] == "$"):
                props["amount"] = get_amount(line)
            elif line[0] == "P":
                props["payee"] = line[1:]
            elif line[0] == "L":
                (fld, val) = get_cat(line)
                props[fld] = val
                master_id = False
            elif line[0] == "C":
                pass
                props["reconciled"] = "X"
            elif (line[0] == "M") or (line[0] == "E"):
                props["memo"] = line[1:]
            elif line[0] == "N":
                props["action"] = line[1:]
                # Action for effect only -  make amount negative if required
                if props["action"] in action_sub:
                    props["amount"] *= -1
            elif line[0] == "Y":
                props["name"] = line[1:]
            elif line[0] == "I":
                props["price"] = get_amount(line)
            elif line[0] == "Q":
                props["quantity"] = get_amount(line)
            elif line[0] == "O":
                props["commission"] = get_amount(line)
            elif line[0] == "S":
                # This is the start of a split record
                # Write previous record and initialize current record
                tran = Transaction(**props)
                sql_eng.add(tran)
                if not master_id:
                    # This is first split record, write master and remember ID
                    sql_eng.flush()
                    sql_eng.refresh(tran)
                    master_id = tran.id
                    props["master_id"] = master_id
                    (fld, val) = get_cat(line)
                    props[fld] = val
            elif line[0] == "!":
                if account_type:
                    logging.critical("Multiple Account type lines found: {l}".format(l=line))
                    sys.exit(1)
                else:
                    account_type = True
            else:
                logging.critical("Unexpected QIF line found: {l}".format(l=line))
                sys.exit(1)
        tran = Transaction(**props)
        sql_eng.add(tran)
        lc = li.info_loop()
        if (lc % 100) == 0:
            sql_eng.commit()
    li.end_loop()
    sql_eng.commit()
