#!/usr/bin/env python

import sys, os, string
from enum import Enum
import tushare as ts

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
        self.fundaLib[fundaType.performance] = funda_cell(ts.get_report_data, "performance_report.csv")
        self.fundaLib[fundaType.profit] = funda_cell(ts.get_profit_data, "profit_report.csv")
        self.fundaLib[fundaType.operation] = funda_cell(ts.get_operation_data, "operation_report.csv")
        self.fundaLib[fundaType.growth] = funda_cell(ts.get_growth_data, "growth_report.csv")
        self.fundaLib[fundaType.debtpaying] = funda_cell(ts.get_debtpaying_data, "debtpaying_report.csv")
        self.fundaLib[fundaType.cashflow] = funda_cell(ts.get_cashflow_data, "cashflow_report.csv")

    def get_stock_basics(self):
        info = ts.get_stock_basics()
        info.to_csv("./output/stock_basics.csv")
        return info

    def get_fundamental_info(self, type, year, quarter):
        info = self.fundaLib[type].get_callback()(year, quarter)
        info.to_csv("./output/" + self.fundaLib[type].get_savefile())
        return info

