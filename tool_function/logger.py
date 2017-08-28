#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from PyQt5 import QtCore
from PyQt5.QtCore import qInstallMessageHandler


def handler(qt_msg_type, context, msg):
    msg = "{0}(line:{1}):{2}".format(context.file, context.line, msg)
    if qt_msg_type == QtCore.QtDebugMsg:
        logging.debug(msg)
    elif qt_msg_type == QtCore.QtInfoMsg or qt_msg_type == QtCore.QtSystemMsg:
        logging.info(msg)
    elif qt_msg_type == QtCore.QtWarningMsg:
        logging.warning(msg)
    elif qt_msg_type == QtCore.QtCriticalMsg:
        logging.critical(msg)
    elif qt_msg_type == QtCore.QtFatalMsg:
        logging.error(msg)
    else:
        logging.exception(msg)


def check_log_file(filename):
    file_size = os.path.getsize(filename)
    print("file_size:", file_size)
    if file_size > 1024*1024:
        log_dir = os.path.dirname(filename).replace("\\", "/")
        print(log_dir)
        from datetime import datetime
        new_name = filename.replace("app.log", "{}.log".format(datetime.now().strftime('%Y%m%d%H%M%S')))
        os.rename(filename, new_name)


def init(log_dir=r"logs", level=logging.ERROR):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    filename = "{}/app.log".format(log_dir.replace("\\", "/"))
    if os.path.exists(filename):
        check_log_file(filename)
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s %(filename)s[line:%(lineno)d] :: %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
        filename=filename,
        filemode='a')

    console = logging.StreamHandler()
    level = logging.DEBUG
    console.setLevel(level)
    formatter = logging.Formatter(fmt='%(levelname)s %(filename)s[line:%(lineno)d] :: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)

    qInstallMessageHandler(handler)


if __name__ == "__main__":
    init(level=logging.DEBUG)
    logging.debug("*"*1024*1022)


