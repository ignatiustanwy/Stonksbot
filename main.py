import telegram.ext as ext
import pandas_datareader as reader
import datetime
from datetime import timedelta
import pandas as pd

with open('token.txt','r') as file:
    API = file.read()

updater = ext.Updater(API, use_context = True)

# receive = None

def start(update, context):
    update.message.reply_text(
        "Welcome to Stonks bot ! Use /help for instructions.")

def help(update, context):
    update.message.reply_text(
        """/stock_price -> Get current stock price. For cryptocurrency, the ticker is 'COIN-USD'.
        Enter in the following format: \n/stock_price {ticker}\n
/set_alerts -> Set alerts when stock reaches desired price. Enter in the following format: 
/set_alerts {stock} {< / >} {price}\n
/market_open -> Tracks the opening hours of the following markets: SGX, NYSE, LSE.    
        """)

# def stock_price(update,context):
#     update.message.reply_text("Enter the ticker:")
#     # global receive
#     # receive = True

def stock_price(update,context):
    # global receive
    # if receive:
        input = str.upper(context.args[0])

        try:
            ticker = reader.DataReader(input, 'yahoo')
            price = ticker.iloc[-1]['Close']

        except:
            price = 'No such ticker'
        if price == 'No such ticker':
            update.message.reply_text(price)
        else:
            update.message.reply_text(f"The current price of {input} is {price}.")

        # receive = False


def set_alerts(update, context):
    if len(context.args) > 2:
        ticker = str.upper(context.args[0])
        sign = context.args[1]
        price = context.args[2]

        context.job_queue.run_repeating(stocknotif, interval = 5, first = 5, context = [ticker,sign,price,update.message.chat_id])
        response = f"Success. The current price of {ticker} is {reader.DataReader(ticker,'yahoo').iloc[-1]['Close']}."
    else:
        response = 'Failed. Please enter it in the correct format.'

    update.message.reply_text(response)

def stocknotif(context):
    ticker = context.job.context[0]
    sign = context.job.context[1]
    price = context.job.context[2]
    chat_id = context.job.context[3]

    ping = False
    current_price = reader.DataReader(ticker,'yahoo').iloc[-1]['Close']
    if sign == '>':
        if float(current_price) >= float(price):
            ping = True
    else:
        if float(current_price) <= float(price):
            ping = True

    if ping:
        response = f'Target price for {ticker} at {price} reached. The current price is {current_price}.'
        context.job.schedule_removal()
        context.bot.send_message(chat_id = chat_id, text = response)

def market_open(update,context):
    TIMINGS = {"SGX" : {"OPEN": timedelta(hours = 9), "CLOSE": timedelta(hours = 17)},
               "NYSE" : {"OPEN" : timedelta(hours = 22, minutes = 30), "CLOSE" : timedelta(hours = 5)},
               "LSE" : {"OPEN" : timedelta(hours = 16), "CLOSE" : timedelta(minutes = 30)}}

    time = update.effective_message.date
    sg_time = time + datetime.timedelta(hours = 8)
    sg_time = sg_time.__str__()[:-6]
    sec = int(sg_time[-2:])
    min = int(sg_time[-5:-3])
    hr = int(sg_time[-8:-6])
    sg_time_intimedelta = timedelta(hours=hr, minutes=min, seconds=sec)
    sg_time_date = sg_time[:10]
    sg_day = pd.Timestamp(sg_time_date).day_name()
    response = f"Time now is {sg_time} GMT +8. \n \nTime till the following markets open: \n"

    for market in TIMINGS.keys():
        open = TIMINGS[market]["OPEN"]
        close = TIMINGS[market]["CLOSE"]


        if open <= sg_time_intimedelta <= close:
            response = "OPEN"
        else:
            time_diff =  open - sg_time_intimedelta
        if time_diff < timedelta():
            time_diff += timedelta(hours = 24)
        if sg_day == "Friday":
            time_diff += timedelta(hours = 72)
        elif sg_day == "Saturday":
            time_diff += timedelta(hours = 48)
        elif sg_day == "Sunday""" :
            time_diff += timedelta(hours = 24)

        ##changing time_delta to hrs,mins,seconds
        time_diff_in_s = time_diff.total_seconds()
        days = divmod(time_diff_in_s, 86400)
        hours = divmod(days[1], 3600)  # Use remainder of days to calc hours
        minutes = divmod(hours[1], 60)  # Use remainder of hours to calc minutes
        seconds = divmod(minutes[1], 1)  # Use remainder of minutes to calc seconds

        response += f"{market}: {int(days[0])} days, {int(hours[0])} hours, {int(minutes[0])} minutes, " \
                    f"{int(seconds[0])} seconds \n"

    update.message.reply_text(response)


    # update.message.reply_text(f"Time between dates: {int(days[0])} days, {int(hours[0])} hours, {int(minutes[0])} minutes, "
    #                           f"{int(seconds[0])} seconds")




updater.dispatcher.add_handler(ext.CommandHandler("start",start))
updater.dispatcher.add_handler(ext.CommandHandler("help",help))
updater.dispatcher.add_handler(ext.CommandHandler("stock_price",stock_price))
# updater.dispatcher.add_handler(ext.MessageHandler(ext.Filters.regex(re.compile('stock_price')),
#                                                   check_stock_price))
updater.dispatcher.add_handler(ext.CommandHandler("set_alerts",set_alerts))
updater.dispatcher.add_handler(ext.CommandHandler("market_open",market_open))


updater.start_polling()
updater.idle()