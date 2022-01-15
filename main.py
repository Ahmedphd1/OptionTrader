from library import *
import termcolor
import sys
from strikeclass import strikeconditions
import winsound

today = datetime.date.today()

inputvariable = None
import threading

# connect application
startclient()
print(termcolor.colored('Client started', 'green', attrs=['blink']))

# Check account credentials
accountfunction()

print(termcolor.colored('Updating files', 'green', attrs=['blink']))
newfiles()

#request historical market data - because market is closed now. But you can change it anytime
app.reqMarketDataType(int(config['appstate']['marketdata']))
print(termcolor.colored('Connected to market data', 'cyan', attrs=['blink']))

createstockdictionary()

time.sleep(5)

checkportfolio()

frequency = 1000  # Set Frequency To 2500 Hertz
duration = 1500  # Set Duration To 1000 ms == 1 second


while(True):
    ticker = monitorstock()

    if config['appstate']['appstate'] == "1":

        winsound.Beep(frequency, duration)

        inputvariable = input("Do you want to buy? Y/N: ").lower()

        time.sleep(2)

        if inputvariable == "y":
            try:
                requestdetails(ticker)

                time.sleep(2)

                conditionobject = strikeconditions(tickerdetails[ticker], ticker)

                conditionobject.buyoption()
                time.sleep(10)

                updatelist(ticker)

                tickerdetails[ticker][1] = 0
                tickerdetails[ticker][0] = 0

                accountfunction()
            except:
                print("No option contract has been found. Going to Monitor")
        elif inputvariable == "n":
            updatelist(ticker)
            tickerdetails[ticker][1] = 0
            tickerdetails[ticker][0] = 0
            tickerdetails[ticker][21] = 0
            print("Continue to monitoring stocks")
    elif config['appstate']['appstate'] == "0":
        try:
            conditionobject = strikeconditions(tickerdetails[ticker], ticker)

            conditionobject.buyoption()
            time.sleep(10)

            updatelist(ticker)
            accountfunction()
        except:
            print("No option contract has been found. Going to minitor")

