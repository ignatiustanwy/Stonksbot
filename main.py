import telegram.ext as ext
import pandas_datareader as reader
import datetime
from datetime import timedelta
from etherscan import Etherscan
from pycoingecko import CoinGeckoAPI


coingecko = CoinGeckoAPI()

with open('etherscan.txt', 'r') as file:
    ETHERAPI = file.read()

ether = Etherscan(ETHERAPI)

with open('token.txt', 'r') as file:
    API = file.read()

updater = ext.Updater(API, use_context=True)

notices = {}


def start(update, context):
    update.message.reply_text(
        "Welcome to Stonks bot ! Use /help for instructions.")
    user = update.message.chat_id
    notices[user] = []


def help(update, context):
    update.message.reply_text(
        """/stock_price -> Get current stock price.\nEnter in the following format: \n/stock_price {ticker} OR \n/stock_price {name} for cryptocurrencies\n
/set_alerts -> Set alerts when stock reaches desired price. Enter in the following format: 
/set_alerts {stock} {< / >} {price} OR \n                     {name} {< / >} {price} for cryptocurrencies\n
/market_open -> Tracks the opening hours of the major stock markets.  \n
/check_gas -> Gets current gas price for Ethereum transactions. \n
/display_alerts -> Displays outstanding alerts. \n
/remove_alert -> Removes an outstanding alert.\nEnter in the following format: \n/remove_alert {number}. Number is shown in /display_alerts 
    """)


def stock_price(update, context):
    input = str.upper(context.args[0])
    try:
        ticker = reader.DataReader(input, 'yahoo')
        price = ticker.iloc[-1]['Close']
    except KeyError:
        ticker = str.lower(input)
        try:
            price = coingecko.get_price(ids=input, vs_currencies='usd')[ticker]['usd']
        except KeyError:
            price = 'No such ticker/name'
    if price == 'No such ticker/name':
        update.message.reply_text(price)
    else:
        update.message.reply_text(f"The current price of {input} is {price}.")

    # receive = False


def display_alerts(update, context):
    response = 'Your current alerts are: \n\n'
    id = 1
    user = update.message.chat_id
    for alert in notices[user]:
        response += f"{id}. {alert[0]} {alert[1]} {alert[2]} \n"
        id += 1

    update.message.reply_text(response)


def remove_alert(update, context):
    removal = int(context.args[0])
    del notices[removal - 1]

    new_response = "Successfully removed."
    update.message.reply_text(new_response)


def set_alerts(update, context):
    def istickervalid(ticker):
        try:
            reader.DataReader(ticker, 'yahoo')
            return True
        except:
            ticker = str.lower(ticker)
            if len(coingecko.get_price(ids=ticker, vs_currencies='usd')) != 0:
                return True
            else:
                return False

    def issignvalid(sign):
        if sign == "<" or sign == ">" or sign == "<=" or sign == ">=" or sign == "=":
            return True
        else:
            return False

    def ispricevalid(price):
        try:
            float(price)
            return True
        except:
            return False

    if len(context.args) == 3:
        ticker = str.upper(context.args[0])
        sign = str(context.args[1])
        price = str(context.args[2])

        if not istickervalid(ticker):
            update.message.reply_text('Failed. No such ticker/name.')
        if not issignvalid(sign):
            update.message.reply_text('Failed. Please key in a valid sign ("<", ">", "<=", ">=", "=").')
        if not ispricevalid(price):
            update.message.reply_text('Failed. Please key in your targeted price in the correct format.')

        if istickervalid(ticker) and issignvalid(sign) and ispricevalid(price):
            user = update.message.chat_id
            notices[user].append((ticker, sign, price))
            try:
                response = f"Success. The current price of {ticker} is {float(reader.DataReader(ticker,'yahoo').iloc[-1]['Close'])}."
                update.message.reply_text(response)
            except:
                ticker = str.lower(ticker)
                response = f"Success. The current price of {ticker} is {float(coingecko.get_price(ids=ticker, vs_currencies='usd')[ticker]['usd'])}."
                update.message.reply_text(response)
        # changed
            for alert in notices[user]:
                context.job_queue.run_repeating(stocknotif, interval=15, first=5, context=[alert[0], alert[1], alert[2],
                                                                                           update.message.chat_id])
    else:
        update.message.reply_text('Failed. Please enter it in the correct format.')


def stocknotif(context):
    ticker = context.job.context[0]
    sign = context.job.context[1]
    price = context.job.context[2]
    chat_id = context.job.context[3]

    ping = False
    try:
        current_price = reader.DataReader(ticker, 'yahoo').iloc[-1]['Close']
    except:
        ticker = str.lower(ticker)
        current_price = coingecko.get_price(ids=ticker, vs_currencies='usd')[ticker]['usd']

    if sign == '>=':
        if float(current_price) >= float(price):
            ping = True
    elif sign == '<=':
        if float(current_price) <= float(price):
            ping = True
    elif sign == '<':
        if float(current_price) < float(price):
            ping = True
    elif sign == '>':
        if float(current_price) > float(price):
            ping = True
    elif sign == '=':
        if float(current_price) == float(price):
            ping = True

    if ping:
        response = f'Target price for {ticker} at {price} reached. The current price is {current_price}.'
        notices[chat_id].remove((str.upper(ticker), sign, price)) # new
        context.job.schedule_removal()
        context.bot.send_message(chat_id=chat_id, text=response)


def market_open(update, context):
    def seconds_to_response(diff_time):
        time_diff_in_s = diff_time.total_seconds()
        days = divmod(time_diff_in_s, 86400)
        hours = divmod(days[1], 3600)  # Use remainder of days to calc hours
        minutes = divmod(hours[1], 60)  # Use remainder of hours to calc minutes
        seconds = divmod(minutes[1], 1)  # Use remainder of minutes to calc seconds

        calc = f"{market}: {int(days[0])} day(s), {int(hours[0])} hour(s), {int(minutes[0])} minute(s), {int(seconds[0])} second(s) \n"
        return calc

    TIMINGS = {"SGX": {"OPEN": timedelta(hours=1), "CLOSE": timedelta(hours=9)},
               "TKX": {"OPEN": timedelta(hours=0), "CLOSE": timedelta(hours=6)},
               "HKEX": {"OPEN": timedelta(hours=1), "CLOSE": timedelta(hours=9)},
               "NYSE": {"OPEN": timedelta(hours=14, minutes=30), "CLOSE": timedelta(hours=21)},
               "NASDAQ": {"OPEN": timedelta(hours=14, minutes=30), "CLOSE": timedelta(hours=21)},
               "LSE": {"OPEN": timedelta(hours=8), "CLOSE": timedelta(hours=16, minutes=30)},
               "TSX": {"OPEN": timedelta(hours=14, minutes=30), "CLOSE": timedelta(hours=20, minutes=40)},
               }

    time = update.effective_message.date
    sg_time = time + datetime.timedelta(hours=8)
    sg_time = sg_time.__str__()[:-6]
    strtime = time.__str__()[:-6]
    sec = int(strtime[-2:])
    min = int(strtime[-5:-3])
    hr = int(strtime[-8:-6])
    time_intimedelta = timedelta(hours=hr, minutes=min, seconds=sec)
    # 0 = monday, 6 = sunday
    day_of_week = time.today().weekday()

    response = f"Time now is {sg_time} GMT +8. \n \nTime till the following markets open: \n"

    for market in TIMINGS.keys():
        open = TIMINGS[market]["OPEN"]
        close = TIMINGS[market]["CLOSE"]

        time_diff = open - time_intimedelta
        if day_of_week >= 5:
            if day_of_week == 5:
                time_diff += timedelta(hours=48)
            else:
                time_diff += timedelta(hours=24)
            response += seconds_to_response(time_diff)
        elif open <= time_intimedelta <= close:
                response += f"{market}: OPEN\n"
        else:
            if time_diff < timedelta():
                time_diff += timedelta(hours=24)
            elif day_of_week == 4:
                time_diff += timedelta(hours=72)

            # changing time_delta to hrs,mins,seconds
            response += seconds_to_response(time_diff)

    update.message.reply_text(response)


def check_gas(update, context):
    eth_price = coingecko.get_price(ids='ethereum', vs_currencies='usd')['ethereum']['usd']

    response = f"ETH price: {eth_price} USD\n\n\n"
    gas_db = ether.get_gas_oracle()
    low = gas_db["SafeGasPrice"]
    average = gas_db["ProposeGasPrice"]
    high = gas_db["FastGasPrice"]

    response += f"Low:           {low}  (>10 minutes) \n" \
                f"Average:   {average}  (3 minutes)\n" \
                f"High:          {high}  (30 seconds)"

    update.message.reply_text(response)


updater.dispatcher.add_handler(ext.CommandHandler("start", start))
updater.dispatcher.add_handler(ext.CommandHandler("help", help))
updater.dispatcher.add_handler(ext.CommandHandler("stock_price", stock_price))
updater.dispatcher.add_handler(ext.CommandHandler("set_alerts", set_alerts))
updater.dispatcher.add_handler(ext.CommandHandler("market_open", market_open))
updater.dispatcher.add_handler(ext.CommandHandler("check_gas", check_gas))
updater.dispatcher.add_handler(ext.CommandHandler("display_alerts", display_alerts))
updater.dispatcher.add_handler(ext.CommandHandler("remove_alert", remove_alert))

updater.start_polling()
updater.idle()
