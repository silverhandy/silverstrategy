#!/usr/bin/env python
# top rank stocks selection
__author__='Chen, Tingjie'
__mailbox__='silverhandy@hotmail.com'

import os, sys, re, getopt, json, datetime
from collections import OrderedDict
import tushare as ts
import pandas as pd
import strategy

class toprank_cell():
    def __init__(self, stockId, increaseRate):
        self._stockId = stockId
        self._increaseRate = increaseRate

    def get_stockId(self):
        return self._stockId

    def get_increase_rate(self):
        return self._increaseRate

class toprank_unit():
    def __init__(self, days, whichDay, rankStocks):
        self.unitDays = days
        self.whichUnit = whichDay
        self.rankStocks = rankStocks
        self.rankBowl = []

    def get_increase(self, x):
        i = self.whichUnit
        increase =  100*(x.iloc[i]['close']-x.iloc[i]['open'])/x.iloc[i]['open']
        return increase
        
    def add_toprank_increase_unit(self, stockId, df):
        if df is None:
            return
        if (len(df) < self.whichUnit+1):
            return
        increase_rate = self.get_increase(df)
        if (increase_rate <= 0):
            return
        cell = toprank_cell(stockId, increase_rate)
        if (len(self.rankBowl) < self.rankStocks):
            self.rankBowl.append(cell)
        else:
            self.rankBowl.sort(key=lambda x:x.get_increase_rate())
            #self.print_toprank_unit()
            if (self.rankBowl[0].get_increase_rate() < increase_rate):
                #print("\n************* Unit:", self.whichUnit, "Pop:", self.rankBowl[0][1], "Append:", element[1])
                self.rankBowl.pop(0)
                self.rankBowl.append(cell)

    def find_and_pop_unit(self, stockId):
        weightIncrease = 0.0
        for i in self.rankBowl:
            if stockId == i.get_stockId():
                weightIncrease += i.get_increase_rate()/(self.whichUnit+1)
                self.rankBowl.pop(self.rankBowl.index(i))
                break
        return weightIncrease

    def is_bowl_empty(self):
        return 0 == len(self.rankBowl)

    def get_first_stockId(self):
        return self.rankBowl[0].get_stockId()

    def print_toprank_unit(self):
        for i in self.rankBowl:
            print("Day:", self.whichUnit, "unit:", i)

class toprank_strategy(strategy.base_strategy):
    def __init__(self):
        strategy.base_strategy.__init__(self)
        self.name = "toprank"
        self.unitDays = 0
        self.rankUnits = 0
        self.rankStocks = 0
        self.breakHighDays = 0
        self.breakHighThrone = []
        self.units = {}
        self.rankCrown = []

    def load_parameters(self):
        with open('toprank.json', 'r') as f:
            data = json.load(f)
        self.unitDays = data["unitDays"]
        self.rankUnits = data["rankUnits"]
        self.rankStocks = data["rankStocks"]
        self.breakHighDays = data["breakHighDays"]
        for i in range(0, self.rankUnits):
            self.units[i] = toprank_unit(self.unitDays, i, self.rankStocks)

    def pick_date_from_days(self, days):
        end_day = datetime.date(datetime.date.today().year, datetime.date.today().month, \
datetime.date.today().day)
        days = days*7/5
        start_day = end_day - datetime.timedelta(days)
        start_day = start_day.strftime("%Y-%m-%d")
        end_day = end_day.strftime("%Y-%m-%d")
        return (start_day, end_day)

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

    def add_toprank_increase(self, stockId):
        (start_day, end_day) = self.pick_date_from_days(self.unitDays*self.rankUnits)
        #print("increase: stockId", stockId, "start_day", start_day, "end_day", end_day)
        df = ts.get_h_data(stockId, start=start_day, end=end_day)
        #print("Dataframe: \n", df)
        for i in range(0, self.rankUnits):
       	    self.units[i].add_toprank_increase_unit(stockId, df)

    def toprank_loop_stocks(self):
        info = super().get_stock_basics()
        i = 50
        for eachStockId in info.index:
            i = i-1
            if (i < 0): break
            if self.is_break_high(eachStockId, self.breakHighDays):
                #print("Break_high: ", eachStockId, info.ix[eachStockId])
                self.breakHighThrone.append(eachStockId)
            self.add_toprank_increase(eachStockId)

    def load_recent_stock_info(self):
        self.load_parameters()
        self.toprank_loop_stocks()
        print("\n############# LenofHighThrone:", len(self.breakHighThrone), "breakHighThrone:", self.breakHighThrone)
        #for i in range(0, self.rankUnits):
        #    self.units[i].print_toprank_unit()

    def find_and_pop_toprank_unit(self, stockId):
        weightIncrease = 0.0
        for i in range(0, self.rankUnits):
            weightIncrease += self.units[i].find_and_pop_unit(stockId)
        return weightIncrease

    def merge_toprank_crown(self):
        for i in range(0, self.rankUnits):
            while(not self.units[i].is_bowl_empty()):
                stockId = self.units[i].get_first_stockId()
                weightIncrease = self.find_and_pop_toprank_unit(stockId)
                perl = toprank_cell(stockId, weightIncrease)
                self.rankCrown.append(perl)

    def eliminate_without_break_high(self):
        for i in self.rankCrown:
            if i.get_stockId() not in self.breakHighThrone:
                self.rankCrown.pop(self.rankCrown.index(i))

    def select_toprank_stocks(self):
        self.load_recent_stock_info()
        self.merge_toprank_crown()
        self.eliminate_without_break_high()
        self.rankCrown.sort(key=lambda x:-x.get_increase_rate())
        print("$$$$$$$$$$$ rankCrown:", self.rankCrown)

    def get_fundamental_all(self, year, quarter):
        super().get_stock_basics()
        super().get_fundamental_info(strategy.fundaType.performance, year, quarter)
        super().get_fundamental_info(strategy.fundaType.profit, year, quarter)
        super().get_fundamental_info(strategy.fundaType.operation, year, quarter)
        super().get_fundamental_info(strategy.fundaType.growth, year, quarter)
        super().get_fundamental_info(strategy.fundaType.debtpaying, year, quarter)
        super().get_fundamental_info(strategy.fundaType.cashflow, year, quarter)

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "hsf:")
    tr = toprank_strategy()
    for op, value in opts:
        if op == "-f":
            div = value.find(',')
            year = int(value[0:div])
            quarter = int(value[div+1:])
            print("Parse date year:", year, "quarter:", quarter)
            tr.get_fundamental_all(year, quarter)
            sys.exit()
        elif op == "-s":
            print("Selecting toprank stocks...")
            tr.select_toprank_stocks()
            sys.exit()
        elif op == "-h":
            print("python3 topranks.py -s # select toprank stocks")
            print("python3 topranks.py -f 2015,4 # get fundamental info")
            print("version of tushare: %s"% ts.__version__)
            print("version of pandas: %s"% pd.__version__)
            sys.exit()

