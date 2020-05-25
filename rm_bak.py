#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: AcidGo
Version: 0.0.1
Change Log:
    2018-02-01 0.0.1-alp:
        1. 实现对SAFE_DAYS 天数外的的所有增备进行删除，对SAFE_DAYS 天外的全备仅保留每月SAFE_XTR_DAY_OF_MONTH号的。
    2018-03-28 0.0.1:
        1. 经过验证，迭代为正式版本。
        2. 增加交互提醒功能，以便更好地确认配置参数。
"""


from __future__ import print_function
import os
import glob
import datetime
import time
import sys
import logging


def _is_lock(lock_file):
    if os.path.exists(lock_file):
        return True
    else:
        return False
    
def _lock(lock_file):
    with open(lock_file, "w") as file:
        file.write("This is lock file of rm_bak.py.\n")
        file.write("Do not remove this file.\n")
    logging.info("Script lock on {0!s}".format(lock_file))
        
def _unlock(lock_file):
    if os.path.exists(lock_file):
        os.unlink(lock_file)
        logging.info("Script lock is unlocked.")
    else:
        logging.error("Script lock is not exists when it would be remove.")
        
def script_lock(lock_file="/tmp/py-rm_bak.pid"):
    import atexit
    if not _is_lock(lock_file):
        logging.info("Script lock is not exists.Lock it.")
        _lock(lock_file)
        atexit.register(_unlock, lock_file)
    else:
        logging.error("Script lock is exists!Stop do it.")
        sys.exit(1)

def init_logger(file_or_path="log.log"):
    script_path = os.path.split(os.path.realpath(__file__))[0]
    file_or_path = os.path.join(script_path, file_or_path)
    logging.basicConfig(
        level = logging.DEBUG,
        format = "%(asctime)s [%(levelname)s] %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
        filename = file_or_path,
        filemode = "a"
    )
    return file_or_path
    
today = time.strftime("%Y-%m-%d", time.localtime())
log_name = "rm_bak.{0!s}.log".format(today)
script_path = init_logger(log_name)
logging.info("#"*80)
script_lock()

DEL_SLEEP_TIME = 0.5
SAFE_DAYS = 30
SAFE_XTR_DAY_OF_MONTH = [25,]
logging.info("Execute this script.")

out_ask = []
out_ask.append("Script path: {0!s}".format(script_path))
out_ask.append("DEL_SLEEP_TIME: {0!s}".format(DEL_SLEEP_TIME))
out_ask.append("SAFE_DAYS: {0!s}".format(SAFE_DAYS))
save_limit_date = (datetime.date.today() - datetime.timedelta(days=SAFE_DAYS)).strftime("%Y-%m-%d")
out_ask.append("Safe limit date is {0!s}.".format(save_limit_date))
out_ask.append("SAFE_XTR_DAY_OF_MONTH: {0!s}".format(SAFE_XTR_DAY_OF_MONTH))

if SAFE_DAYS < 30:
    logging.error("SAFE_DAYS is less 30.")
    sys.exit(1)

for i in out_ask:
    logging.info(i)
    print(i)
is_sure = input("Do you want to continue? (y/n)")
if is_sure.lower() not in ("y", "yes"):
    logging.info("Chose stop to execute this script.")
    print("Exit now.")
    sys.exit(0)
# logging.info("Script path: {0!s}".format(script_path))
# logging.info("DEL_SLEEP_TIME: {0!s}".format(DEL_SLEEP_TIME))
# logging.info("SAFE_DAYS: {0!s}".format(SAFE_DAYS))
# logging.info("SAFE_XTR_DAY_OF_MONTH: {0!s}".format(SAFE_XTR_DAY_OF_MONTH))


NOW_DATE = datetime.datetime.combine(datetime.date.today(), datetime.time())
logging.debug("NOW_DATE: {0!s}".format(NOW_DATE))

def _out_day(ctime):
    t = datetime.datetime.fromtimestamp(ctime)
    if NOW_DATE - t > datetime.timedelta(days=SAFE_DAYS):
        return True
    else:
        return False


def _get_arv_files(prefix):
    arv_files = [file for file in glob.glob("%s*.lzo" % prefix)]
    if len(arv_files) == 0:
        logging.error("Not found files by glob, Please check the prefix.")
        sys.exit(1)
    elif len(arv_files) < 300:
        logging.error("Arvchive lzo files less 300!STOP DO IT.")
        sys.exit(1)
    return arv_files

def _get_xtr_files(prefix):
    xtr_files = [file for file in glob.glob("%s*.tzo" % prefix)]
    if len(xtr_files) == 0:
        logging.error("Not found files by glob, Please check the prefix.")
        sys.exit(1)
    return xtr_files

def sort_files_desc(files_lst):
    def compare(x, y):
        stat_x = os.stat(x)
        stat_y = os.stat(y)
        return cmp(stat_x.st_ctime, stat_y.st_ctime)
    files_lst.sort(compare)
    return files_lst


def sniff_arv(prefix):
    arv_dict = {"safe": [], "bad": []}
    arv_files = _get_arv_files(prefix)
    for i in arv_files:
        if is_in_safe_days(i):
            arv_dict["safe"].append(i)
        else:
            arv_dict["bad"].append(i)
    arv_dict["safe"] = sort_files_desc(arv_dict["safe"])
    arv_dict["bad"] = sort_files_desc(arv_dict["bad"])
    return arv_dict


def sniff_xtr(prefix):
    xtr_dict = {"safe": [], "bad": []}
    xtr_files = _get_xtr_files(prefix)
    for i in xtr_files:
        if is_in_safe_days(i):
            xtr_dict["safe"].append(i)
        elif is_day_of_month(i):
        # elif is_day_of_month_2()(i):
            xtr_dict["safe"].append(i)
        else:
            xtr_dict["bad"].append(i)
    xtr_dict["safe"] = sort_files_desc(xtr_dict["safe"])
    xtr_dict["bad"] = sort_files_desc(xtr_dict["bad"])
    return xtr_dict

def is_in_safe_days(file):
    if not os.path.exists(file):
        logging.error("The file that is put in safe days lst is not exists.")
        sys.exit(1)
    elif not os.path.isfile(file):
        logging.error("The file that is put in safe days lst is not a file.")
        sys.exit(1)
    if _out_day(os.stat(file).st_ctime):
        return False
    return True

# 此处可以使用闭包来检验保留的月份是否为重复
def is_day_of_month(file):
    if not os.path.exists(file):
        logging.error("The file wheather is day of month is not exists.")
        sys.exit(1)
    if not os.path.isfile(file):
        logging.error("The file wheather is day of month is not a file.")
        sys.exit(1)
    file_time = os.stat(file).st_ctime
    month = datetime.datetime.fromtimestamp(file_time).month
    day = datetime.datetime.fromtimestamp(file_time).day
    if day in SAFE_XTR_DAY_OF_MONTH:
        return True
    return False
    
    
def is_day_of_month_2():
    d = {"month_lst": []}
    def test(file):
        if not os.path.exists(file):
            return True
        if not os.path.isfile(file):
            return True
        file_time = os.stat(file).st_ctime
        month = datetime.datetime.fromtimestamp(file_time).month
        day = datetime.datetime.fromtimestamp(file_time).day
        if day in SAFE_XTR_DAY_OF_MONTH:
            d["month_lst"].append(month)
            logging.info("month_lst: {0!s}".format(d["month_lst"]))
            return True
        elif len(d["month_lst"]) != 0 and d["month_lst"][-1] == month - 1:
            return False
        else:
            return True
    return test

    
            
def do_rm_file(files_lst):
    rm_size = 0
    for file in files_lst:
        if os.path.exists(file) and os.path.isfile(file):
            rm_size += os.path.getsize(file)
            file_ctime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.stat(file).st_ctime))
            os.unlink(file)
            logging.info("[unlink]{0!s} -> {1!s}".format(file_ctime, file))
            time.sleep(DEL_SLEEP_TIME)
    return rm_size
            

def main():
    arv_prefix = "/home/backup/ftp_backup/Archive-180-rds"
    xtr_prefix = "/home/backup/ftp_backup/NearLine-xtrabak_rds"
    logging.info("arv_prefix: {0!s}".format(arv_prefix))
    logging.info("xtr_prefix: {0!s}".format(xtr_prefix))
    
    arv_dict = sniff_arv(arv_prefix)
    xtr_dict = sniff_xtr(xtr_prefix)
    
    logging.info("@"*80)
    try:
        # rm bad arv
        rm_arv_size = do_rm_file(arv_dict["bad"])
        # rm bad xtr
        rm_xtr_size = do_rm_file(xtr_dict["bad"])
    except Exception as e:
        logging.error("Exception in rm function: {0!s}".format(e))
        logging.info("@"*80)
        sys.exit(1)
    logging.info("@"*80)
    for file in arv_dict["safe"]:
        file_ctime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.stat(file).st_ctime))
        logging.info("[safe] {0!s} -> {1!s}".format(file_ctime, file))
    for file in xtr_dict["safe"]:
        file_ctime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.stat(file).st_ctime))
        logging.info("[safe] {0!s} -> {1!s}".format(file_ctime, file))
    logging.info("rm arv size MB: {0!s}".format(rm_arv_size/(1024*1024)))
    logging.info("rm xtr size MB: {0!s}".format(rm_xtr_size/(1024*1024)))
    
if __name__ == "__main__":
    main()
    logging.info("The script is finished!!!")
