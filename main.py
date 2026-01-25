import os
import time
import requests
import telebot
import logging
from telebot import types
from gatet import Tele

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot config
BOT_TOKEN = "8426512661:AAGWiADKvrJHDp919MndSpBS6PDTAY5TZ6k"
ALLOWED_CHAT_ID = "8202990461"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Ensure cleanup directory exists
if not os.path.exists("stop"):
    os.makedirs("stop")

def cleanup_files():
    """Clean up temporary files"""
    files_to_remove = ["combo.txt", "stop.stop"]
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
            except:
                pass

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
    cleanup_files()
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
    try:
        with open("stop.stop", "w") as file:
            file.write("stop")
        bot.reply_to(message, "Stop request saved. Current run will halt shortly.")
    except Exception as e:
        logger.error(f"Error creating stop file: {e}")
        bot.reply_to(message, "Error saving stop request.")

@bot.message_handler(content_types=["document"])
def main(message):
    if not is_authorized(message):
        bot.reply_to(message, "Access denied.")
        return

    # Clean up any previous files
    cleanup_files()
    
    dd = live = ch = ccn = cvv = lowfund = 0
    
    try:
        ko = bot.reply_to(message, "Checking....⌛").message_id
        
        # Download file
        file_info = bot.get_file(message.document.file_id)
        ee = bot.download_file(file_info.file_path)

        with open("combo.txt", "wb") as w:
            w.write(ee)

        with open("combo.txt", "r") as file:
            lines = file.readlines()
            total = len(lines)
            
            for index, cc in enumerate(lines, 1):
                cc = cc.strip()
                if not cc:
                    continue
                    
                # Check for stop signal
                if os.path.exists("stop.stop"):
                    bot.edit_message_text(
                        chat_id=message.chat.id, 
                        message_id=ko,
                        text='STOP ✅\nBOT BY ➜ @Mr_Vempire1'
                    )
                    cleanup_files()
                    return

                try:
                    # Get BIN info
                    bin_data = {}
                    if len(cc.split("|")[0]) >= 6:
                        bin_response = requests.get(f'https://bins.antipublic.cc/bins/{cc.split("|")[0][:6]}', timeout=10)
                        if bin_response.status_code == 200:
                            bin_data = bin_response.json()
                except Exception as e:
                    logger.error(f"BIN lookup error: {e}")
                    bin_data = {}

                brand = bin_data.get('brand', 'Unknown')
                card_type = bin_data.get('type', 'Unknown')
                country = bin_data.get('country_name', 'Unknown')
                country_flag = bin_data.get('country_flag', 'Unknown')
                bank = bin_data.get('bank', 'Unknown')

                # Process card
                start_time = time.time()
                try:
                    last = str(Tele(cc))
                except Exception as e:
                    logger.error(f"Card processing error: {e}")
                    last = 'Error processing card'
                
                end_time = time.time()
                execution_time = end_time - start_time

                # Update counters based on response
                if 'Payment Successful!' in last:
                    ch += 1
                    bot.send_message(message.chat.id, f"✅ Payment success: {cc}")
                elif 'Your card does not support this type of purchase' in last:
                    cvv += 1
                elif 'security code is incorrect' in last or 'security code is invalid' in last:
                    ccn += 1
                elif 'insufficient funds' in last:
                    lowfund += 1
                    bot.send_message(message.chat.id, f"💸 Low funds: {cc}")
                else:
                    dd += 1
                    time.sleep(1)

                # Update progress every 5 cards or on last card
                if index % 5 == 0 or index == total:
                    mes = types.InlineKeyboardMarkup(row_width=1)
                    mes.add(
                        types.InlineKeyboardButton(f"• Processing: {index}/{total} •", callback_data='u8'),
                        types.InlineKeyboardButton(f"• CHARGED ➜ [ {ch} ] •", callback_data='x'),
                        types.InlineKeyboardButton(f"• CCN ➜ [ {ccn} ] •", callback_data='x'),
                        types.InlineKeyboardButton(f"• CVV ➜ [ {cvv} ] •", callback_data='x'),
                        types.InlineKeyboardButton(f"• LOW FUNDS ➜ [ {lowfund} ] •", callback_data='x'),
                        types.InlineKeyboardButton(f"• DECLINED ➜ [ {dd} ] •", callback_data='x'),
                        types.InlineKeyboardButton(f"[ STOP ]", callback_data='stop')
                    )
                    try:
                        bot.edit_message_text(
                            chat_id=message.chat.id, 
                            message_id=ko, 
                            text=f'Progress: {index}/{total}\n@Mr_Vempire1', 
                            reply_markup=mes
                        )
                    except Exception as e:
                        logger.error(f"Edit message error: {e}")

    except Exception as e:
        logger.error(f"Main error: {e}")
        bot.reply_to(message, f"Error: {str(e)}")
    finally:
        cleanup_files()
        try:
            bot.edit_message_text(
                chat_id=message.chat.id, 
                message_id=ko, 
                text='CHECKED ✅\nBOT BY ➜ @Mr_Vempire'
            )
        except:
            pass

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def menu_callback(call):
    try:
        with open("stop.stop", "w") as file:
            file.write("stop")
        bot.answer_callback_query(call.id, "Stop requested!")
    except Exception as e:
        logger.error(f"Stop callback error: {e}")

if __name__ == "__main__":
    logger.info("Bot starting...")
    cleanup_files()  # Clean up on start
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        cleanup_files()
