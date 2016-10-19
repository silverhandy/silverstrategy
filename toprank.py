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
            if (self.rankBowl[0][1] < increase_rate):
                self.rankBowl.pop(0)
                self.rankBowl.append(element)

    def print_toprank_unit(self):
        for i in self.rankBowl:
            print("Day:", self.whichUnit, "unit:", i)
            print("Tuples: ", i[0], "-", i[1])

class toprank_strategy(strategy.base_strategy):
    def __init__(self):
        strategy.base_strategy.__init__(self)
        self.name = "toprank"
        self.unitDays = 0
        self.rankUnits = 0
        self.rankStocks = 0
        self.breakHighDays = 0
        self.breakHighList = []
        self.units = {}

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
        i = 32
        for eachStockId in info.index:
            i = i-1
            if i < 0:
                break
            if self.is_break_high(eachStockId, self.breakHighDays):
                #print("Break_high: ", eachStockId, info.ix[eachStockId])
                self.breakHighList.append(eachStockId)
            self.add_toprank_increase(eachStockId)

    def load_recent_stock_info(self):
        print("version of tushare: %s"% ts.__version__)
        self.load_parameters()
        #cd = ts.get_today_all()
        #rd = ts.get_hist_data('000063')
	    #rd.to_csv('./data/hist_all.csv')
        #rd.to_json('./data/hist_all.json', orient='records')
        self.toprank_loop_stocks()
        print("breakHighList: ", self.breakHighList)
        for i in range(0, self.rankUnits):
            self.units[i].print_toprank_unit()

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
            tr.load_recent_stock_info()
            sys.exit()

