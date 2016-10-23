#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, string
from enum import Enum
import tushare as ts

class industryType(Enum):
    null = 0
    semiconductor = 1
    communication = 2
    software = 3
    food = 4
    electric = 5
    realty = 6
    medicine = 7
    construction = 8
    bank = 9
    component = 10
    finance = 11

class fundaType(Enum):
    performance = 1
    profit = 2
    operation = 3
    growth = 4
    debtpaying = 5
    cashflow = 6

class funda_cell():
    def __init__(self, callback, savefile):
        self._callback = callback
        self._savefile = savefile

    def get_callback(self):
        return self._callback

    def get_savefile(self):
        return self._savefile

class base_strategy():
    def __init__(self):
        self.name = "base"
        self.fundaLib = {}
        self.fundaLib[fundaType.performance] = funda_cell(ts.get_report_data, "performance_report")
        self.fundaLib[fundaType.profit] = funda_cell(ts.get_profit_data, "profit_report")
        self.fundaLib[fundaType.operation] = funda_cell(ts.get_operation_data, "operation_report")
        self.fundaLib[fundaType.growth] = funda_cell(ts.get_growth_data, "growth_report")
        self.fundaLib[fundaType.debtpaying] = funda_cell(ts.get_debtpaying_data, "debtpaying_report")
        self.fundaLib[fundaType.cashflow] = funda_cell(ts.get_cashflow_data, "cashflow_report")

    def get_stock_basics(self, saveFile):
        info = ts.get_stock_basics()
        if saveFile:
            info.to_csv("./output/stock_basics.csv")
        return info

    def get_fundamental_info(self, type, year, quarter, saveFile):
        info = self.fundaLib[type].get_callback()(year, quarter)
        if saveFile:
            info.to_csv("./output/" + self.fundaLib[type].get_savefile() + "_%s_%s"%(str(year), str(quarter)) + ".csv")
        return info

    def get_industry_from_GBK(self, gbk):
        if gbk == u'半导体': return industryType.semiconductor
        elif gbk == u'通信设备': return industryType.communication
        elif gbk == u'软件服务': return industryType.software
        elif gbk == u'元器件': return industryType.component
        elif gbk == u'银行': return industryType.bank
        elif gbk == u'多元金融': return industryType.finance
        else: return industryType.null
