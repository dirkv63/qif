"""
This script will find all qif files in qif dump directory, then send each file to process_qif for load in transaction
table.
"""

# Allow lib to library import path.
import os
import logging
from lib import my_env
from lib.my_env import run_script


cfg = my_env.init_env("qif", __file__)
logging.info("Start Application")
scandir = cfg["Main"]["qifdump"]
(fp, filename) = os.path.split(__file__)
script = "process_qif"
filelist = [file for file in os.listdir(scandir)]
for file in filelist:
    fn = os.path.join(scandir, file)
    logging.info("Run script: {s}.py -f {fn}".format(s=script, fn=fn))
    run_script(fp, "{s}.py".format(s=script), "-f", fn)
logging.info("End Application")
