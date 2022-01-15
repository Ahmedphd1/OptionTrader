from library import *

class strikeconditions():

    def __init__(self, dictionary, ticker):
        self.dictionary = dictionary
        self.ticker = ticker
        app.reqMarketDataType(int(config['appstate']['marketdata']))


    def calculatestrike(self):
        print(termcolor.colored('Trying to find option chain by: Strike', 'red', attrs=['blink']))
        for contracts in self.dictionary[4]:
            if int(tickerdetails[self.ticker][17]) == int(contracts.strike) and tickerdetails[self.ticker][10] == contracts.right and str(tickerdetails[self.ticker][18]) == str(contracts.lastTradeDateOrContractMonth):

                print(termcolor.colored(f'Found contract: Start saving to logfile... {contracts}', 'green', attrs=['blink']))

                with open(f'Logfiles/logfile{today.strftime("%Y-%m-%d")}.txt', "a") as f:
                    f.write(f"Ticker: {contracts.symbol} Strike: {contracts.strike} OptionType:  {contracts.right} Experation date: {contracts.lastTradeDateOrContractMonth} \n")
                f.close()
                return contracts
        print("No contracts found")


    def calculaterange(self):
        print(termcolor.colored('Trying to find option chain by: Range', 'blue', attrs=['blink']))

        self.contractlist = []
        self.volumelist = []

        myrange = optionrange(int(self.dictionary[17]), self.ticker)

        print(myrange[0])
        print(myrange[1])

        for contracts in self.dictionary[4]:
            if contracts.strike > myrange[1] and contracts.strike < myrange[0] and tickerdetails[self.ticker][10] == contracts.right and str(tickerdetails[self.ticker][18]) == str(contracts.lastTradeDateOrContractMonth):

                myvolume = app.get_volume_data(app.nextorderId, contracts, contracts.right)

                self.contractlist.append(contracts)
                self.volumelist.append(myvolume)

        if not self.contractlist:
            print("cannot find any contracts")
            return None

        if self.volumelist:
            indexofmax = self.volumelist.index(max(self.volumelist))

            mycontract = self.contractlist[indexofmax]

            print(
                termcolor.colored(f'Found contract: Start saving to logfile... {mycontract}', 'green', attrs=['blink']))

            with open(f'Logfiles/logfile{today.strftime("%Y-%m-%d")}.txt', "a") as f:
                f.write(
                    f"Ticker: {mycontract.symbol} Strike: {mycontract.strike} OptionType:  {mycontract.right} Experation date: {mycontract.lastTradeDateOrContractMonth} \n")
            f.close()

            return mycontract
        else:
            print("cannot find volume")

    def buyoption(self):

        strikecontract = self.calculatestrike()
        rangecontract = self.calculaterange()

        if strikecontract:

            try:
                mycontract = stock_contract_option_buy(strikecontract.symbol, strikecontract.exchange,
                                                       strikecontract.strike, strikecontract.right,
                                                       strikecontract.lastTradeDateOrContractMonth)

                mydatalist = app.get_option_data(app.nextorderId, mycontract)
                time.sleep(10)

                inputvariable = input(f"Do you want to: {str(self.dictionary[10])} a quantity of: "
                                      f"{str(self.dictionary[11])} of: {str(self.ticker)} at strike {str(strikecontract.right)} at expiration: "
                                      f" {str(strikecontract.lastTradeDateOrContractMonth)} at {str(self.dictionary[13])} ? yes = Y: no = N: ").lower()

                if inputvariable == "y":
                    buyoption(mycontract, round(float(mydatalist[0][1]), 2), int(self.dictionary[13]))
            except:
                print("could not find any live market data")

        elif rangecontract:

            try:
                mycontract = stock_contract_option_buy(rangecontract.symbol, rangecontract.exchange,
                                                       rangecontract.strike, rangecontract.right,
                                                       rangecontract.lastTradeDateOrContractMonth)

                ordernextid()
                mydatalist = app.get_option_data(app.nextorderId, mycontract)

                time.sleep(10)

                setticker(self.ticker)

                inputvariable = input(f"Do you want to: {str(self.dictionary[10])} a quantity of: "
                                      f"{str(self.dictionary[11])} of: {str(self.ticker)} at strike {str(rangecontract.right)} at expiration: "
                                      f" {str(rangecontract.lastTradeDateOrContractMonth)} at {str(self.dictionary[13])} ? yes = Y: no = N: ").lower()

                if inputvariable == "y":
                    buyoption(mycontract, round(float(mydatalist[0][1]), 2), int(self.dictionary[13]))
                elif inputvariable == "n":
                    updatelist(self.ticker)
            except:
                print("could not find any live market data")

        else:
            inputvariable = input("Do you want to Buy without option chain? yes = Y: no = N: ").lower()

            if inputvariable == "y":
                try:

                    mycontract = stock_contract_option_buy(self.ticker, self.dictionary[3],
                                                           int(self.dictionary[17]), self.dictionary[10],
                                                           self.dictionary[18])

                    ordernextid()
                    setticker(self.ticker)
                    mydatalist = app.get_option_data(app.nextorderId, mycontract)

                    time.sleep(10)

                    buyoption(mycontract, round(float(mydatalist[0][1]), 2))
                except:
                    print("could not buy the contract")

            elif inputvariable == "n":
                updatelist(self.ticker)