from ibapi.client import EClient, SetOfString, SetOfFloat, TickerId, OrderId
from ibapi.order_state import OrderState
from ibapi.wrapper import EWrapper, inspect, TickType, TickTypeEnum
from ibapi.contract import Contract
from ibapi.order_condition import Create, OrderCondition
from ibapi.order import *
import threading
import time
from random import randrange
import json
from configparser import ConfigParser
import termcolor
import sys
import datetime
import os.path
from os import path

today = datetime.date.today()

file = "config.ini"
config = ConfigParser()
config.read(file)

accountsummery = {}

tickerdetails = {}

currentticker = None

conditioner = 0

marketdatalist = []

volumelist = []

alonevolumelist = []

callorput = None


class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.contract_details = {}  # Contract details will be stored here using reqId as a dictionary key

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        print('The next valid order id is: ', self.nextorderId)

    def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId,
                    whyHeld, mktCapPrice):
        pass
        # print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining,
        #       'lastFillPrice', lastFillPrice)

    def openOrder(self, orderId, contract, order, orderState):
        pass
        # print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action,
        #       order.orderType, order.totalQuantity, orderState.status)

    def execDetails(self, reqId, contract, execution): #create a stop loss order through the order exec function
        # print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId,
        #       execution.orderId, execution.shares, execution.lastLiquidity)

        with open(f'Orderfiles/orders{today.strftime("%Y-%m-%d")}.txt', "a") as f:
            f.write(f"Contract bought:  {contract.symbol}, with shares: {execution.shares} and price {execution.price}")
        f.close()

        if tickerdetails[contract.symbol]:
            print(termcolor.colored('Excluding ticker from monitoring', 'blue', attrs=['blink']))
            tickerdetails.pop(contract.symbol)

    def tickPrice(self, reqId, tickType, price, attrib):

        if conditioner == 1:
            thisticker = getticker()
            if tickerdetails[thisticker][0] == 0:
                tickerdetails[thisticker][0] = float(round(price, 2))
                print(termcolor.colored(f'Appending first price for: {thisticker} price: {price} Decrease: Not enough', 'blue', attrs=['blink']))
            elif calculatechange(float(price), tickerdetails[thisticker][0]) <= float(tickerdetails[thisticker][7]):
                mychange = calculatechange(float(price), tickerdetails[thisticker][0])
                print(f"Original Ticker price is: {tickerdetails[thisticker][0]} Current ticker price: {price} Changedifference is: {mychange}%")

                tickerdetails[thisticker][1] = 1

    def accountSummary(self, reqId: int, account: str, tag: str, value: float, currency: str):
        accountsummery[tag] = value

    def contractDetails(self, reqId: int, contractDetails):
        global conditioner
        # print("contractDetails: ", reqId, " ", contractDetails.contract, "\n")

        if conditioner == 1:
            tickerdetails[getticker()][4].append(contractDetails.contract)
            with open(f'Orderfiles/logconract.txt', "a") as f:
                f.write(f"Ticker: {contractDetails.contract.symbol} strike: {contractDetails.contract.strike} right: {contractDetails.contract.right} \n")
            f.close()
        else:
            self.contract_details[reqId] = contractDetails

    def get_contract_details(self, reqId, contract):
        self.contract_details[reqId] = None
        self.reqContractDetails(reqId, contract)
        # Error checking loop - breaks from loop once contract details are obtained
        for err_check in range(50):
            if not self.contract_details[reqId]:
                time.sleep(0.1)
            else:
                break
        # Raise if error checking loop count maxed out (contract details not obtained)
        if err_check == 49:
            raise Exception('error getting contract details')
        # Return contract details otherwise
        return app.contract_details[reqId].contract

    def tickOptionComputation(self, reqId: TickerId, tickType: TickType, tickAttrib: int, impliedVol: float,delta: float, optPrice: float,
                              pvDividend: float, gamma: float, vega: float, theta: float,undPrice: float):
        super().tickOptionComputation(reqId, tickType, tickAttrib, impliedVol, delta, optPrice, pvDividend, gamma, vega,theta, undPrice)

        if tickerdetails[getticker()][12] == 'ASK' and tickType == 11:
            print("This is option price: {}".format(optPrice))

            object = f"{delta} {optPrice} {impliedVol}"
            marketdatalist.append(object.split())

        elif tickerdetails[getticker()][12] == 'BID' and tickType == 10:
            print("This is option price: {}".format(optPrice))

            object = f"{delta} {optPrice} {impliedVol}"
            marketdatalist.append(object.split())

    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        super().tickSize(reqId, tickType, size)
        global callorput

        # if callorput == 'C' and tickType == 27:
        #     print("This is open interest for call: {}".format(size))
        #
        #     volumelist.append(size)
        # elif callorput == 'P' and tickType == 28:
        #     print("This is open interest for put: {}".format(size))
        #
        #     volumelist.append(size)

        if callorput == 'C' and tickType == 8:
            print("This is volume for call: {}".format(size))

            volumelist.append(size)

        elif callorput == 'P' and tickType == 8:
            print("This is volume for put: {}".format(size))

            volumelist.append(size)


    def get_volume_data(self, reqId, contract, ordertype):
        global callorput
        global volumelist

        volumelist.clear()
        setordertype(ordertype)

        mycontract = stock_contract_option_buy(contract.symbol, "SMART", contract.strike, contract.right,contract.lastTradeDateOrContractMonth)

        self.reqMktData(reqId, mycontract, "", False, False, [])

        time.sleep(10)

        for err_check in range(50):
            if not volumelist:
                time.sleep(0.1)
            else:
                time.sleep(4)
                break
        # Raise if error checking loop count maxed out (contract details not obtained)
        if err_check == 49:
            raise Exception('error getting contract details')
        # Return contract details otherwise
        return volumelist[0]

    def get_option_data(self, reqId, contract):
        global marketdatalist

        marketdatalist.clear()

        self.reqMktData(reqId, contract, "", False, False, None)

        time.sleep(10)

        for err_check in range(50):
            if not marketdatalist:
                time.sleep(0.1)
            else:
                time.sleep(4)
                break
        # Raise if error checking loop count maxed out (contract details not obtained)
        if err_check == 49:
            raise Exception('error getting contract details')
        # Return contract details otherwise
        return marketdatalist

    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState):

        super().openOrder(orderId, contract, order, orderState)

        if contract.symbol in tickerdetails:
            tickerdetails.pop(contract.symbol)

app = IBapi()
if config['appstate']['clientstate'] == "0":
    print("running demo")
    app.connect('127.0.0.1', 7497, 123)  # live = 7496: demo = 7497
elif config['appstate']['clientstate'] == "1":
    print("running live")
    app.connect('127.0.0.1', 7496, 123)  # live = 7496: demo = 7497

def stock_contract_option(symbol, exchange):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'OPT'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    contract.primaryExchange = exchange

    return contract

def stock_contract_option_delta(symbol, exchange):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'OPT'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    contract.primaryExchange = exchange
    contract.strike = int(tickerdetails[symbol][17])
    contract.right = tickerdetails[symbol][10]
    contract.lastTradeDateOrContractMonth = tickerdetails[symbol][18]
    contract.includeExpired = True

    return contract

def stock_contract_option_buy(symbol, exchange, strike, right, expired):
    try:
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'OPT'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        contract.primaryExchange = exchange
        contract.strike = strike
        contract.right = str(right)
        contract.lastTradeDateOrContractMonth = str(expired)
        contract.multiplier = "100"
        contract.includeExpired = True

        return contract
    except:
        print("couldnt create contract for option")

def stock_contract(symbol, exchange):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    contract.primaryExchange = exchange
    return contract

def buyoption(contract, price, increased):

    print(termcolor.colored('Buying contract', 'yellow', attrs=['blink']))

    print(price)

    try:
        # Create order object
        mainorder = Order()
        mainorder.orderId = app.nextorderId
        mainorder.action = tickerdetails[contract.symbol][11]
        mainorder.totalQuantity = tickerdetails[contract.symbol][8]
        mainorder.orderType = 'LMT'
        OPTION_PRICE = price + (price * float(tickerdetails[contract.symbol][14]) / 100)
        mainorder.lmtPrice = round(OPTION_PRICE, 2)



        # appending and submitting the order
        mainorder.transmit = False

        # Create order object
        childorder = Order()
        childorder.orderId = mainorder.orderId + 1
        childorder.action = "SELL" if mainorder.action == "BUY" else "BUY"
        childorder.totalQuantity = int(tickerdetails[contract.symbol][8])
        childorder.orderType = "LMT"
        childorder.lmtPrice = round(OPTION_PRICE * increased, 2)
        childorder.parentId = mainorder.orderId

        # appending and submitting the order
        print(f"order details buy: Ticker: {contract.symbol} Action: {mainorder.action} Quantity:  {mainorder.totalQuantity} OrderType: {mainorder.orderType} Price: {mainorder.lmtPrice}")
        print(f"order details Take profit: Ticker: {contract.symbol} Action: {childorder.action} Quantity:  {childorder.totalQuantity} OrderType: {childorder.orderType} Price: {childorder.lmtPrice}")

        inputvariable = input("Do you want to Transmit order? yes = Y: no = N: ").lower()

        if inputvariable == "y":
            childorder.transmit = True
        elif inputvariable == "n":
            childorder.transmit = False

        mylist = [mainorder, childorder]

        tickerdetails[contract.symbol][1] = 0
        tickerdetails[contract.symbol][0] = 0

        for brackets in mylist:
            print(f"submitting order: Ticker: {contract.symbol} Action: {brackets.action} Quantity:  {brackets.totalQuantity} OrderType: {brackets.orderType} Price: {brackets.lmtPrice}")
            app.placeOrder(brackets.orderId, contract, brackets)
            ordernextid()

            print(termcolor.colored(f'Saving order to file', 'green', attrs=['blink']))
            with open(f'Orderfiles/orders{today.strftime("%Y-%m-%d")}.txt', "a") as f:
                f.write(f"Ticker: {contract.symbol} Action: {brackets.action} Quantity:  {brackets.totalQuantity} OrderType: {brackets.orderType} Price: {brackets.lmtPrice} \n")
            f.close()

            tickerdetails.pop(contract.symbol)

    except:
        print("something went wrong:")

def checkconnectivity():
    print("Checking for connectivity")
    app.nextorderId = None

    # Check if the API is connected via orderid
    while True:
        if isinstance(app.nextorderId, int):
            print('connected')
            ordernextid()
            break
        else:
            print('waiting for connection')
            time.sleep(1)

def run_loop():
    print("running client")
    app.run()

def ordernextid():
    app.nextorderId += 1

def appthread():
    api_thread = threading.Thread(target=run_loop, daemon=True)
    api_thread.start()

def startclient():
    appthread()
    checkconnectivity()

def calculatechange(current, start):
    change = (current - start) / start * 100

    return change

def monitorstock():
    global currentticker
    global conditioner
    print(termcolor.colored('Starting monitor stock', 'magenta', attrs=['blink']))

    while(True):
        if tickerdetails:
            for key, value in tickerdetails.items():
                try:
                    ordernextid()
                    print(termcolor.colored('Stocks being monitored: {0}'.format(key), 'yellow', attrs=['blink']))
                    setticker(key)
                    conditioner = 1

                    app.reqMktData(app.nextorderId, stock_contract(key, "SMART"), '', True, False, [])
                    ordernextid()

                    time.sleep(int(tickerdetails[key][9]))
                    tickerdetails[key][21] += 1
                    conditioner = 0
                    if tickerdetails[key][1] == 1:
                        print(termcolor.colored(f'Monitoring stock finished: Price has decreased for ticker: {key}',
                                                'cyan', attrs=['blink']))
                        return key
                        break
                    elif tickerdetails[key][21] >= (int(tickerdetails[key][6]) * 3):
                        tickerdetails[key][1] = 0
                        tickerdetails[key][0] = 0
                        tickerdetails[key][21] = 0
                except:
                    print("could not monitor stock")

def optionrange(strike, symbol):

    if strike > 0 and int(tickerdetails[symbol][15]) > 0 or int(tickerdetails[symbol][16]) > 0:
        print("ERROR: strike is not 0 min/max is 0")
        return 0,0

    elif strike > 0:
        try:
            optionmin = strike - (int(tickerdetails[symbol][15]) * strike / 100)
            optionmax = strike - (int(tickerdetails[symbol][16]) * strike / 100)

            return int(optionmin), int(optionmax)
        except:
            print("cannot multiply by 0.0")

    if strike == 0:
        try:
            return 0,0
        except:
            print("cannot multiply by 0.0")
    elif strike == 0 and int(tickerdetails[symbol][15]) == 0 or int(tickerdetails[symbol][16]) == 0:
        print("ERROR: strike is 0 min/max is 0")
        return 0,0



def checkaccount(dictionary):

    print(f"Cushion: {float(dictionary['Cushion'])} (Minimum request is: {float(config['account']['cushion'])})")
    print(f"BuyingPower: {float(dictionary['BuyingPower'])} (Minimum request is: {float(config['account']['power_Spending'])})")
    print(f"EquitywithLoanValue: {float(dictionary['EquityWithLoanValue'])} (Minimum request is: {float(config['account']['capital_and_Loan'])})")
    print(f"Netliquidation: {float(dictionary['NetLiquidation'])} (Minimum request is: {float(config['account']['min_Liquidity'])})")

    if float(dictionary['Cushion']) >= float(config['account']['cushion']) and float(dictionary['EquityWithLoanValue']) >= float(config['account']['capital_and_Loan']) and float(dictionary['NetLiquidation']) >= float(config['account']['min_Liquidity']) and float(dictionary['BuyingPower']) >= float(config['account']['power_Spending']):
        print(termcolor.colored('Account validation succeeded', 'green', attrs=['blink']))
    else:
        print(termcolor.colored('Fatal error: Not enough capital! exiting....', 'red', attrs=['blink']))
        sys.exit()

def accountfunction():
    ordernextid()

    try:
        print(termcolor.colored('Starting account checking', 'blue', attrs=['blink']))
        app.reqAccountSummary(9001, "All", "NetLiquidation, EquityWithLoanValue, Cushion, BuyingPower ")
        time.sleep(4)
        checkaccount(accountsummery)
    except:
        print("could not check account info")
def createstockdictionary():
    print(termcolor.colored('Starting creating dictionary', 'magenta', attrs=['blink']))
    global conditioner
    for items in getstocks():
        ordernextid()
        checkfile = downloaddetails(items[0])

        if checkfile != False:
            print("is not false")

            try:
                time.sleep(1)
                tickerdetails[items[0]] = [0, 0, checkfile[1], checkfile[2], []]
                filldictionary(items, items[0])
            except:
                print("could not create dictionary")

        else:
            print("not in details file: {}".format(items[0]))
            try:
                myobject = app.get_contract_details(app.nextorderId, stock_contract(items[0], 'SMART'))
                time.sleep(4)
                uploaddetails(items[0], myobject.conId, myobject.exchange)

                tickerdetails[items[0]] = [0, 0, myobject.conId, myobject.exchange, []]
                filldictionary(items, items[0])
            except:
                print("could not create dictionary 2")

    print(termcolor.colored('Finished creating dictionary for: {0}'.format(items[0]), 'green', attrs=['blink']))


def setticker(symbol):
    global currentticker
    currentticker = symbol

def getticker():

    return currentticker

def checkportfolio():
    ordernextid()
    app.reqOpenOrders()

def getstocks():
    mylist = []

    my_file = open("stocks.txt", "r")
    for i, line in enumerate(my_file):
        if i >= 4:
            mylist.append(str(line).split(","))

    return mylist

def filldictionary(stocklist, symbol):

    for items in stocklist:
        try:
            tickerdetails[symbol].append(items)
        except:
            print("could not find any list")
    # appending the clock
    tickerdetails[symbol].append(0)

def downloaddetails(symbol):

    if path.exists("Orderfiles/contractdetails.txt") == False:
        print("not")
        with open('Orderfiles/contractdetails.txt', "w") as f:
            f.close()

    with open(f'Orderfiles/contractdetails.txt', "r") as f:
        try:
            lines = f.readlines()

            if lines:
                for l in lines:
                    if symbol in l:
                        print("Ticker is already in the file: getting information")
                        list = l.split(" ")
                        return list[1], list[3], list[5]

                return False
            else:
                return False
        except:
            print("could not download symbol")
def uploaddetails(symbol, conid, exchange): # value 2 and 3
    if path.exists("Orderfiles/contractdetails.txt") == True:

        try:
            with open(f'Orderfiles/contractdetails.txt', "a") as f:
                f.write(f"Ticker: {symbol} Conid: {conid} Exchange: {exchange} \n")
            f.close()
        except:
            print("could not upload data")

def newfiles():
    try:
        with open(f'Logfiles/logfile{today.strftime("%Y-%m-%d")}.txt', "w") as f:
            f.close()
        with open(f'Orderfiles/orders{today.strftime("%Y-%m-%d")}.txt', "w") as f:
            f.close()
    except:
        print("could not create files")

def requestdetails(symbol):
    global conditioner

    print("Requesting option chain for ticker")

    try:
        conditioner = 1
        time.sleep(1)

        setticker(symbol)
        app.reqContractDetails(app.nextorderId, stock_contract_option(symbol, 'SMART'))
        ordernextid()
        time.sleep(int(config['appstate']['timer']))
        conditioner = 0
    except:
        print("could not request contract details")


    print("Finished Requesting option chain for ticker")

def setordertype(ordertype):
    global callorput
    callorput = ordertype

def updatelist(symbol):

    tempdict = {}
    tempdict[symbol] = tickerdetails[symbol]
    tickerdetails.pop(symbol)
    tickerdetails[symbol] = tempdict[symbol]
