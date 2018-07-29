"""
This script will process a qif file.
"""

import argparse
# import os
import sys
from lib import my_env
from lib import sqlstore
from lib.sqlstore import *


def get_amount(item):
    """
    Remove commas from amount and convert to float.

    :param item: Line containing amount

    :return:
    """
    amount = item[1:].replace(",", "")
    return float(amount)


def get_date(item):
    """
    Date is in format d/m'yy. Return date in string format

    :param item:

    :return:
    """
    [dm, yr] = item[1:].split("'")
    [d,m] = dm.split("/")
    return "20{yr}-{m:02d}-{d:02d}".format(yr=yr, m=int(m), d=int(d))

def get_cat(item):
    return "category", item[1:]

if __name__ == '__main__':
    # Configure command line arguments
    parser = argparse.ArgumentParser(
        description="Load QIF file into database"
    )
    parser.add_argument('-f', '--filename', type=str, required=True,
                        help='Please provide the qif file to load.')
    args = parser.parse_args()
    cfg = my_env.init_env("qif", __file__)
    logging.info("Arguments: {a}".format(a=args))
    sql_eng = sqlstore.init_session(cfg["Main"]["db"])

    fh = open(args.filename, "r")
    qifdump = fh.read()
    chunks = qifdump.split("\n^\n")
    account_type = False
    li = my_env.LoopInfo("Transactions", 100)
    for chunk in chunks:
        if len(chunk) == 0:
            break
        lines = chunk.split("\n")
        props = dict(account_id=1)
        master_id = False
    tran = Transaction(**props)
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
        elif line[0] == "C":
            pass
            props["reconciled"] = "X"
        elif (line[0] == "M") or (line[0] == "E"):
            props["memo"] = line[1:]
        elif line[0] == "S":
            # This is the start of a split record
            # Write previous record and initialize current record
            tran = Transaction(**props)
            sql_eng.add(tran)
            if not master_id:
                # This is first split record, write master and remember ID
                sql_eng.flush()
                sql_eng.refresh(tran)
                props["master_id"] = tran.id
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
    sql_eng.add(tran)
    lc = li.info_loop()
    if (lc % 100) == 0:
        sql_eng.commit()
    li.end_loop()
    sql_eng.commit()
