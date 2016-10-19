#!/usr/bin/env python
# top rank stocks selection
__author__='Chen, Tingjie'
__mailbox__='silverhandy@hotmail.com'

import os, sys, re, getopt, json, datetime
from collections import OrderedDict
import tushare as ts
import strategy

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
        element = (stockId, increase_rate)
        if (len(self.rankBowl) < self.rankStocks):
            self.rankBowl.append(element)
        else:
            self.rankBowl.sort(key=lambda x:x[1])
            #self.print_toprank_unit()
            if (self.rankBowl[0][1] < increase_rate):
                #print("\n************* Unit:", self.whichUnit, "Pop:", self.rankBowl[0][1], "Append:", element[1])
                self.rankBowl.pop(0)
                self.rankBowl.append(element)

    def find_and_pop_unit(self, stockId):
        weightIncrease = 0.0
        for i in self.rankBowl:
            if stockId == i[0]:
                weightIncrease += i[1]/(self.whichUnit+1)
                self.rankBowl.pop(self.rankBowl.index(i))
                break
        return weightIncrease

    def is_bowl_empty(self):
        return 0 == len(self.rankBowl)

    def get_first_stockId(self):
        return self.rankBowl[0][0]

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
        info = ts.get_stock_basics()
        #i = 50
        for eachStockId in info.index:
            #i = i-1
            #if (i < 0): break
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
                perl = (stockId, weightIncrease)
                self.rankCrown.append(perl)

    def eliminate_without_break_high(self):
        for i in self.rankCrown:
            if i[0] not in self.breakHighThrone:
                self.rankCrown.pop(self.rankCrown.index(i))

    def select_toprank_stocks(self):
        self.load_recent_stock_info()
        self.merge_toprank_crown()
        self.eliminate_without_break_high()
        self.rankCrown.sort(key=lambda x:-x[1])
        print("$$$$$$$$$$$ rankCrown:", self.rankCrown)

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "hp:")
    tr = toprank_strategy()
    for op, value in opts:
        if op == "-p":
            path = value
            print("Get file {0}".format(path))
            sys.exit()
        elif op == "-h":
            print("Usage: python topranks.py -p YOUR_FULL_PATH_NAME")
            print("version of tushare: %s"% ts.__version__)
            tr.select_toprank_stocks()
            sys.exit()

