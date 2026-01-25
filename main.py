import os
import time
import requests
import telebot
from telebot import types
from gatet import Tele

# Bot config
BOT_TOKEN = "8426512661:AAGWiADKvrJHDp919MndSpBS6PDTAY5TZ6k"
ALLOWED_CHAT_ID = "8202990461"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


def is_authorized(message) -> bool:
    return str(message.chat.id) == ALLOWED_CHAT_ID


def send_usage(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Help", "Stop")
    text = (
        "Send a .txt file to start checking.\n"
        "Each line: card|MM|YY|CVC\n"
        "Use Stop button (or /stop) to halt current run."
    )
    bot.reply_to(message, text, reply_markup=markup)


@bot.message_handler(commands=["start"])
def start(message):
    if not is_authorized(message):
        bot.reply_to(message, "Access denied.")
        return
    send_usage(message)


@bot.message_handler(commands=["help"])
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() == "help")
def help_cmd(message):
    if not is_authorized(message):
        bot.reply_to(message, "Access denied.")
        return
    send_usage(message)


@bot.message_handler(commands=["stop"])
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() == "stop")
def stop_cmd(message):
    if not is_authorized(message):
        bot.reply_to(message, "Access denied.")
        return
    with open("stop.stop", "w") as file:
        file.write("stop")
    bot.reply_to(message, "Stop request saved. Current run will halt shortly.")


@bot.message_handler(content_types=["document"])
def main(message):
    if not is_authorized(message):
        bot.reply_to(message, "Access denied.")
        return

    dd = live = ch = ccn = cvv = lowfund = 0
    ko = bot.reply_to(message, "checking....⌛").message_id
    ee = bot.download_file(bot.get_file(message.document.file_id).file_path)

    with open("combo.txt", "wb") as w:
        w.write(ee)

    try:
        with open("combo.txt", "r") as file:
            lines = file.readlines()
            total = len(lines)

            for cc in lines:
                cc = cc.strip()
                if os.path.exists("stop.stop"):
                    bot.edit_message_text(chat_id=message.chat.id, message_id=ko,
                                          text='STOP ✅\nBOT BY ➜ @Mr_Vempire1')
                    os.remove("stop.stop")
                    return

                try:
                    data = requests.get(f'https://bins.antipublic.cc/bins/{cc[:6]}').json()
                except Exception:
                    data = {}

                brand = data.get('brand', 'Unknown')
                card_type = data.get('type', 'Unknown')
                country = data.get('country_name', 'Unknown')
                country_flag = data.get('country_flag', 'Unknown')
                bank = data.get('bank', 'Unknown')

                start_time = time.time()
                try:
                    last = str(Tele(cc))
                except Exception as e:
                    print(e)
                    last = 'missing payment form'
                end_time = time.time()
                execution_time = end_time - start_time

                mes = types.InlineKeyboardMarkup(row_width=1)
                mes.add(
                    types.InlineKeyboardButton(f"• {cc} •", callback_data='u8'),
                    types.InlineKeyboardButton(f"• STATUS ➜ {last} •", callback_data='u8'),
                    types.InlineKeyboardButton(f"• CHARGED ➜ [ {ch} ] •", callback_data='x'),
                    types.InlineKeyboardButton(f"• CCN ➜ [ {ccn} ] •", callback_data='x'),
                    types.InlineKeyboardButton(f"• CVV ➜ [ {cvv} ] •", callback_data='x'),
                    types.InlineKeyboardButton(f"• LOW FUNDS ➜ [ {lowfund} ] •", callback_data='x'),
                    types.InlineKeyboardButton(f"• DECLINED ➜ [ {dd} ] •", callback_data='x'),
                    types.InlineKeyboardButton(f"• TOTAL ➜ [ {total} ] •", callback_data='x'),
                    types.InlineKeyboardButton(f"[ STOP ]", callback_data='stop')
                )
                bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text='@Mr_Vempire1', reply_markup=mes)

                # update counters based on last response
                if 'Payment Successful!' in last:
                    ch += 1
                    bot.reply_to(message, f"✅ Payment success: {cc}")
                elif 'Your card does not support this type of purchase' in last:
                    cvv += 1
                elif 'security code is incorrect' in last or 'security code is invalid' in last:
                    ccn += 1
                elif 'insufficient funds' in last:
                    lowfund += 1
                    bot.reply_to(message, f"💸 Low funds: {cc}")
                else:
                    dd += 1
                    time.sleep(1)

    except Exception as e:
        print(e)

    bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text='CHECKED ✅\nBOT BY ➜ @Mr_Vempire')


@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def menu_callback(call):
    with open("stop.stop", "w") as file:
        pass


if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
