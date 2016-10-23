#!/usr/bin/env python
# -*- coding: utf-8 -*-
# top rank stocks selection
__author__='Chen, Tingjie'
__mailbox__='silverhandy@hotmail.com'

import os, sys, re, getopt, json, datetime
from collections import OrderedDict
import tushare as ts
import pandas as pd
import strategy

class toprank_perl():
    def __init__(self, stockId, d2i):
        self._stockId = stockId
        self._IR = {}
        self._weightIR = 0
        self._d2i = d2i

    def get_stockId(self):
        return self._stockId

    def get_IR(self, day):
        return self._IR[day]

    def set_IR(self, day, IR):
        self._IR[day] = IR

    def calc_weight_IR(self):
        for i in self._IR.keys():
            weight = self._IR[i]/(i+1)
            if weight < 0:
                weight = self._d2i*weight
            self._weightIR += weight
        return self._weightIR

    def get_weight_IR(self):
        return self._weightIR

    def print_perl(self):
        print("Stock:", self._stockId, "weightIR:", self._weightIR)
        #print("IR:", self._IR)

class toprank_strategy(strategy.base_strategy):
    def __init__(self):
        strategy.base_strategy.__init__(self)
        self.name = "toprank"
        self.rankDays = 0
        self.daysBefore = 0
        self.breakHighDays = 0
        self.pe = 0
        self.d2i = 1
        self.breakHighThrone = []
        self.rankCrown = []
        self.industryRef = []
        self.stockRef = []

    def load_parameters(self, daysBefore):
        with open('toprank.json', 'r') as f:
            data = json.load(f)
        self.rankDays = data["rankDays"]
        self.breakHighDays = data["breakHighDays"]
        self.pe = data["pe"]
        self.d2i = data["d2i"]
        self.daysBefore = daysBefore

    def pick_date_from_days(self, days):
        today = datetime.date(datetime.date.today().year, datetime.date.today().month, \
datetime.date.today().day)
        end_day = today - datetime.timedelta(self.daysBefore)
        start_day = end_day - datetime.timedelta(days+2)
        start_day = start_day.strftime("%Y-%m-%d")
        end_day = end_day.strftime("%Y-%m-%d")
        return (start_day, end_day)

    def add_industry_ref(self, industryType):
        if industryType not in self.industryRef:
            self.industryRef.append(industryType)

    def load_stock_ref_pool(self):
        info = super().get_stock_basics(False)
        for index,row in info.iterrows():
            if super().get_industry_from_GBK(row.industry) in self.industryRef:
                if self.pe != 0 and row.pe > self.pe:
                    continue
                self.stockRef.append(index)
        #print("stock_ref_pool: Len", len(self.stockRef), "Stocks:", self.stockRef)

    def is_break_high(self, stockId, days):
        (start_day, end_day) = self.pick_date_from_days(days)
        #print("high: stockId", stockId, "days", days, "start_day", start_day, "end_day", end_day)
        df = ts.get_h_data(stockId, start=start_day, end=end_day)
        if df is None:
            return False
        period_high = df['high'].max()
        today_high = df.iloc[0]['high']
        if today_high >= period_high:
            return True
        else:
            return False

    def get_IR_from_df(self, df, day):
        IR =  100*(df.iloc[day]['close']-df.iloc[day]['open'])/df.iloc[day]['open']
        return IR

    def add_toprank_IR(self, stockId):
        (start_day, end_day) = self.pick_date_from_days(self.rankDays)
        #print("increase: stockId", stockId, "start_day", start_day, "end_day", end_day)
        df = ts.get_h_data(stockId, start=start_day, end=end_day)
        #print("Dataframe: \n", df)
        if df is None:
            return
        perl = toprank_perl(stockId, self.d2i)
        for i in range(0, self.rankDays):
            if i >= len(df):
                return
            IR = self.get_IR_from_df(df, i)
            perl.set_IR(i, IR)
        self.rankCrown.append(perl)

    def load_recent_stock_info(self):
        self.load_stock_ref_pool()
        for eachStockId in self.stockRef:
            if self.is_break_high(eachStockId, self.breakHighDays):
                #print("Break_high: ", eachStockId, info.ix[eachStockId])
                self.breakHighThrone.append(eachStockId)
            self.add_toprank_IR(eachStockId)
        #print("\n############# LenofHighThrone:", len(self.breakHighThrone), "breakHighThrone:", self.breakHighThrone)

    def rank_stock_by_weight_IR(self):
        for i in self.rankCrown:
            i.calc_weight_IR()
        self.rankCrown.sort(key=lambda x:-x.get_weight_IR())

    def eliminate_without_break_high(self):
        for i in self.rankCrown:
            self.rankCrown = filter(lambda x:x.get_stockId() in self.breakHighThrone, self.rankCrown)
            self.rankCrown = list(self.rankCrown)
            self.rankCrown = filter(lambda x:x.get_weight_IR() > 0, self.rankCrown)
            self.rankCrown = list(self.rankCrown)

    def select_toprank_stocks(self):
        self.add_industry_ref(strategy.industryType.semiconductor)
        #self.add_industry_ref(strategy.industryType.software)
        #self.add_industry_ref(strategy.industryType.communication)
        #self.add_industry_ref(strategy.industryType.finance)
        #self.add_industry_ref(strategy.industryType.component)
        self.load_recent_stock_info()
        self.rank_stock_by_weight_IR()
        self.eliminate_without_break_high()
        print("\nRankCrown on daysBefore", self.daysBefore, "Len:", len(self.rankCrown))
        for i in self.rankCrown:
            i.print_perl()

    def dummy_run(self):
        (start_day, end_day) = self.pick_date_from_days(self.rankDays)
        print("daysBefore:", self.daysBefore, "pick date:", start_day, "-", end_day)
        #df = ts.get_h_data('000063', start_day, end_day)
        #print("Dataframe: \n", df)

    def get_fundamental_all(self, year, quarter):
        super().get_stock_basics(True)
        super().get_fundamental_info(strategy.fundaType.performance, year, quarter, True)
        super().get_fundamental_info(strategy.fundaType.profit, year, quarter, True)
        super().get_fundamental_info(strategy.fundaType.operation, year, quarter, True)
        super().get_fundamental_info(strategy.fundaType.growth, year, quarter, True)
        super().get_fundamental_info(strategy.fundaType.debtpaying, year, quarter, True)
        super().get_fundamental_info(strategy.fundaType.cashflow, year, quarter, True)

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "hs:f:")
    for op, value in opts:
        if op == "-f":
            div = value.find(',')
            year = int(value[0:div])
            quarter = int(value[div+1:])
            print("Parse date year:", year, "quarter:", quarter)
            tr = toprank_strategy()
            tr.get_fundamental_all(year, quarter)
            sys.exit()
        elif op == "-s":
            days = int(value)
            print("Selecting toprank stocks before", days, "days ...")
            for i in range(0, days+1)[::-1]:
                tr = toprank_strategy()
                tr.load_parameters(i)
                tr.dummy_run()
                tr.select_toprank_stocks()
            sys.exit()
        elif op == "-h":
            print("python3 topranks.py -s 5 # select toprank stocks")
            print("python3 topranks.py -f 2015,4 # get fundamental info")
            print("version of tushare: %s"% ts.__version__)
            print("version of pandas: %s"% pd.__version__)
            sys.exit()

