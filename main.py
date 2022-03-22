import os
import datetime
import plotly.express as px
import pandas as pd
import requests
import kaleido
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


def do_frame(dates, divs, ticker):
    df = pd.DataFrame(dict(
        dates=dates,
        divs=divs
    ))
    fig = px.line(df, x="dates", y="divs", title=f'{ticker}')
    fig.write_image(f'{ticker}.png')


def scrape_dividends(ticker):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/99.0.4844.51 Safari/537.36'
    }
    today_timestamp = int(datetime.datetime.today().timestamp())
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}' \
          '?formatted=true&crumb=.8T6s.f5qy0&lang=en-US&region=US&includeAdjustedClose=true&interval=1d&' \
          f'period1=-999999999&period2={today_timestamp}&events=capitalGain%7Cdiv%7Csplit&useYfid=true&' \
          'corsDomain=finance.yahoo.com'
    try:
        response = requests.get(url, headers=headers)
        json = response.json()
        result_ = json['chart']['result'][0]
        if 'events' in result_ and 'dividends' in result_['events']:
            return result_['events']['dividends']
        else:
            return None
    except TypeError:
        return None


def get_charts(update: Update, context: CallbackContext) -> None:
    ticker = update.message.text.upper()
    print(ticker)
    dividends = scrape_dividends(ticker)
    if dividends is not None:
        dates = []
        divs = []
        for _, v in dividends.items():
            timestamp_ = v['date']
            if timestamp_ < 0:
                dates.append(datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=timestamp_))
            else:
                dates.append(datetime.datetime.utcfromtimestamp(timestamp_))
            divs.append(v['amount'])

        do_frame(dates, divs, ticker)
        context.bot.sendDocument(update.effective_chat.id, document=open(f'{ticker}.png', 'rb'))
        os.remove(f'{ticker}.png')
    else:
        update.message.reply_text(f'There is no ticker {ticker} or it doesn\'t have dividends')


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def main():
    updater = Updater('5205653266:AAHWY7doMXfi89tO2NSpW_lua5PD6oHzV9w')

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, get_charts))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
