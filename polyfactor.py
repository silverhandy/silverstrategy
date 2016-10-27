#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 可以自己import我们平台支持的第三方python模块，比如pandas、numpy等。
import math
import numpy as np
import pandas as pd
import talib
# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    context.number=12
    context.rate_num = 100
    #context.TIME_PERIOD = 14
    #context.HIGH_RSI = 70
    #context.LOW_RSI = 30
    context.SMAPERIOD = 5
    #context.SMAPERIOD1 = 10
    #context.SHORTPERIOD = 12
    #context.LONGPERIOD = 26
    #context.SMOOTHPERIOD = 9
    #context.OBSERVATION = 100
    get_parameter(context,None)
    scheduler.run_weekly(get_parameter,weekday=1)
    scheduler.run_daily(handle_bar)

# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def get_parameter(context,bar_dict):
    #获取基本面数据
    fundamental_df = get_fundamentals(
        query(fundamentals.eod_derivative_indicator.pe_ratio,fundamentals.eod_derivative_indicator.pb_ratio,fundamentals.financial_indicator.return_on_invested_capital,fundamentals.financial_indicator.inc_revenue,fundamentals.financial_indicator.inc_profit_before_tax
        ).filter(
            fundamentals.eod_derivative_indicator.pb_ratio>0
        ).filter(
            fundamentals.eod_derivative_indicator.pe_ratio>0
        ).filter(
            fundamentals.financial_indicator.return_on_invested_capital>-99
        ).filter(
            fundamentals.financial_indicator.inc_revenue>-99
        ).filter(
            fundamentals.financial_indicator.inc_profit_before_tax>-99
        )
    )
    df=fundamental_df.T
    pe_rank = df.pe_ratio.rank()
    pb_rank = df.pb_ratio.rank()
    roic_rank = df.return_on_invested_capital.rank(ascending=False)
    ir_rank = df.inc_revenue.rank(ascending=False)
    ipbt_rank = df.inc_profit_before_tax.rank(ascending=False)
    pe_rate = pe_rank/(len(df)/context.rate_num)
    pb_rate = pb_rank/(len(df)/context.rate_num)
    roic_rate = roic_rank/(len(df)/context.rate_num)
    ir_rate = ir_rank/(len(df)/context.rate_num)
    ipbt_rate = ipbt_rank/(len(df)/context.rate_num)
    for i in range(len(df)):
        pe_rate.iloc[i-1] = math.ceil(pe_rate.iloc[i-1])
        pb_rate.iloc[i-1] = math.ceil(pb_rate.iloc[i-1])
        roic_rate.iloc[i-1] = math.ceil(roic_rate.iloc[i-1])
        ir_rate.iloc[i-1] = math.ceil(ir_rate.iloc[i-1])
        ipbt_rate.iloc[i-1] = math.ceil(ipbt_rate.iloc[i-1])
    all_rate = pe_rate + pb_rate + roic_rate + ir_rate + ipbt_rate
    a = pd.DataFrame({'rate':all_rate})
    a_sort = a.sort(columns = 'rate')
    a_sort = a_sort.head(context.number)
    context.to_buy=a_sort.T.columns.values
    
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑

    # bar_dict[order_book_id] 可以拿到某个证券的bar信息
    # context.portfolio 可以拿到现在的投资组合状态信息

    # 使用order_shares(id_or_ins, amount)方法进行落单

    # TODO: 开始编写你的算法吧！

    stocks = set(context.to_buy)
    holdings = set(get_holdings(context))
    to_buy = stocks - holdings
    holdings = set(get_holdings(context))
    to_sell = holdings - stocks
    for stock in to_sell:
        if bar_dict[stock].is_trading:
            order_target_percent(stock , 0)
    to_buy = get_trading_stocks(to_buy, context, bar_dict)
    buy_rsi = []
    for stock in to_buy:
        prices = history(context.SMAPERIOD+1,'1d','close')[stock].values
        avg = talib.SMA(prices,context.SMAPERIOD)
        if avg[-1] < prices[-1]:
            buy_rsi.append(stock)
    if len(buy_rsi) >0:
        #cash = context.portfolio.cash
        #average_value = 0.98 * cash / len(buy_rsi)
        for stock in buy_rsi:
            if bar_dict[stock].is_trading:
                #order_value(stock ,average_value)
                order_target_percent(stock,0.08)

def get_trading_stocks(to_buy, context, bar_dict):
    trading_stocks = []
    for stock in to_buy:
        if bar_dict[stock].is_trading:
            trading_stocks.append(stock)
    
    print("Trading stocks:", trading_stocks)
    return trading_stocks

def get_holdings(context):
    positions = context.portfolio.positions
    
    holdings = []
    for position in positions:
        if positions[position].quantity > 0:
            holdings.append(position)
    
    print("Holding stocks:", holdings)
    return holdings
