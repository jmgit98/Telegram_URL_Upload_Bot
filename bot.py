#!/usr/bin/env python3
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# the PTB
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
# the Telegram trackings
from botan import Botan

import subprocess
import math
import requests
import os
import json

ABUSIVE_SPAM = json.loads(requests.get("https://bots.shrimadhavuk.me/Telegram/API/AbusiveSPAM.php").text)

# the secret configuration specific things
from config import Config
# the Strings used for this "thing"
from translation import Translation


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    #2**10 = 1024
    power = 2**10
    n = 0
    Dic_powerN = {0 : ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /=  power
        n += 1
    return str(math.floor(size)) + " " + Dic_powerN[n] + 'B'


## The telegram Specific Functions
def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def start(bot, update):
    # botan.track(Config.BOTAN_IO_TOKEN, update.message, update.message.chat_id)
    bot.send_message(chat_id=update.message.chat_id, text=Translation.START_TEXT, reply_to_message_id=update.message.message_id)


def upgrade(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=Translation.UPGRADE_TEXT, reply_to_message_id=update.message.message_id)


def echo(bot, update):
    # botan.track(Config.BOTAN_IO_TOKEN, update.message, update.message.chat_id)
    if str(update.message.chat_id) in ABUSIVE_SPAM:
        bot.send_message(chat_id=update.message.chat_id, text=Translation.ABS_TEXT, reply_to_message_id=update.message.message_id)
    else:
        if(update.message.text.startswith("http")):
            url = update.message.text
            # logger = "<a href='" + url + "'>url</a> by <a href='tg://user?id=" + str(update.message.chat_id) + "'>" + str(update.message.chat_id) + "</a>"
            # bot.send_message(chat_id=-1001364708459, text=logger, parse_mode="HTML")
            if "noyes.in" not in url:
                try:
                    t_response = subprocess.check_output(["youtube-dl", "-j", url], stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as exc:
                    # print("Status : FAIL", exc.returncode, exc.output)
                    bot.send_message(chat_id=update.message.chat_id, text=exc.output.decode("UTF-8"))
                else:
                    x_reponse = t_response.decode("UTF-8")
                    response_json = json.loads(x_reponse)
                    inline_keyboard = []
                    for formats in response_json["formats"]:
                        format_id = formats["format_id"]
                        format_string = formats["format"]
                        approx_file_size = ""
                        if "filesize" in formats:
                            approx_file_size = humanbytes(formats["filesize"])
                        ikeyboard = [
                            # InlineKeyboardButton(formats["format"], callback_data=formats["format_id"]),
                            InlineKeyboardButton(format_string + "(" + approx_file_size + ")", callback_data=format_id)
                        ]
                        inline_keyboard.append(ikeyboard)
                    reply_markup = InlineKeyboardMarkup(inline_keyboard)
                    bot.send_message(chat_id=update.message.chat_id, text='Select the desired format: (file size might be approximate) ', reply_markup=reply_markup, reply_to_message_id=update.message.message_id)
            else:
                bot.send_message(chat_id=update.message.chat_id, text="@GetPublicLinkBot URL detected. Please do not abuse the service!", reply_to_message_id=update.message.message_id)
        else:
            bot.send_message(chat_id=update.message.chat_id, text=Translation.START_TEXT, reply_to_message_id=update.message.message_id)


def button(bot, update):
    query = update.callback_query
    youtube_dl_format = query.data
    # ggyyy = bot.getChatMember("@MalayalamTrollVoice", query.message.chat_id)
    if "hls" not in youtube_dl_format: #ggyyy.status:
        youtube_dl_url = query.message.reply_to_message.text
        t_response = subprocess.check_output(["youtube-dl", "-j", youtube_dl_url])
        x_reponse = t_response.decode("UTF-8")
        response_json = json.loads(x_reponse)
        file_name_ext = response_json["_filename"].split(".")[-1]
        download_directory = Config.DOWNLOAD_LOCATION + "/" + str(response_json["_filename"])[0:97] + "_" + youtube_dl_format + "." + str(file_name_ext) + ""
        bot.edit_message_text(
            text="Trying to download link",
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
        # if os.path.exists(download_directory):
        #    bot.edit_message_text(
        #        text="Free users can download only 1 URL per day",
        #        chat_id=query.message.chat_id,
        #        message_id=query.message.message_id
        #    )
        # else:
        t_response = subprocess.check_output(["youtube-dl", "-f", youtube_dl_format, youtube_dl_url, "-o", download_directory])
        bot.edit_message_text(
            text="Trying to upload file",
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
        file_size = os.stat(download_directory).st_size
        if file_size > Config.MAX_FILE_SIZE:
            bot.edit_message_text(
                text="size greater than maximum allowed size",
                chat_id=query.message.chat_id,
                message_id=query.message.message_id
            )
            # just send a link
            file_link = Config.HTTP_DOMAIN + "" + download_directory.replace("./", "")
            bot.send_message(chat_id=query.message.chat_id, text=file_link)
        else:
            # try to upload file
            bot.send_document(chat_id=query.message.chat_id, document=open(download_directory, 'rb'), caption="@AnyDLBot")
            # TODO: delete the file after successful upload
            os.remove(download_directory)
    else:
        bot.edit_message_text(
            text="Premium Link Detected. Please /upgrade",
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )


if __name__ == "__main__" :
    botan = Botan()
    # create download directory, if not exist
    if not os.path.isdir(Config.DOWNLOAD_LOCATION):
        os.makedirs(Config.DOWNLOAD_LOCATION)
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=Config.TG_BOT_TOKEN)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    upgrade_handler = CommandHandler('upgrade', upgrade)
    dispatcher.add_handler(upgrade_handler)
    echo_handler = MessageHandler(Filters.text, echo)
    dispatcher.add_handler(echo_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_error_handler(error)
    # Start the Bot
    updater.start_polling()
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()
