import os
import time
import requests
import telebot
from telebot import types
from gatet import Tele

# Bot config
BOT_TOKEN = "8397296517:AAHsHLCgo7_je6uATLELv2U-XZqZlqOcxjM"
ALLOWED_CHAT_ID = "445949718"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


def is_authorized(message) -> bool:
	"""Return True if the message comes from the allowed chat."""
	return str(message.chat.id) == ALLOWED_CHAT_ID


def send_usage(message):
	"""Send quick instructions and a small reply keyboard."""
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
	dd = 0
	live = 0
	ch = 0
	ccn = 0
	cvv = 0
	lowfund = 0
	ko = (bot.reply_to(message, "checking....⌛").message_id)
	ee = bot.download_file(bot.get_file(message.document.file_id).file_path)
	with open("combo.txt", "wb") as w:
		w.write(ee)
	try:
		with open("combo.txt", 'r') as file:
			lino = file.readlines()
			total = len(lino)
			for cc in lino:
				current_dir = os.getcwd()
				for filename in os.listdir(current_dir):
					if filename.endswith(".stop"):
						bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text='STOP ✅\nBOT BY ➜ @Mr_Vempire1')
						os.remove('stop.stop')
						return
				try: data = requests.get('https://bins.antipublic.cc/bins/'+cc[:6]).json()
				except: pass
				try:
					brand = data['brand']
				except:
					brand = 'Unknown'
				try:
					card_type = data['type']
				except:
					card_type = 'Unknown'
				try:
					country = data['country_name']
					country_flag = data['country_flag']
				except:
					country = 'Unknown'
					country_flag = 'Unknown'
				try:
					bank = data['bank']
				except:
					bank = 'Unknown'
				
				start_time = time.time()
				try:
					last = str(Tele(cc))
				except Exception as e:
					print(e)
					last = 'missing payment form'
				mes = types.InlineKeyboardMarkup(row_width=1)
				cm1 = types.InlineKeyboardButton(f"• {cc} •", callback_data='u8')
				status = types.InlineKeyboardButton(f"• STATUS ➜ {last} •", callback_data='u8')
				cm3 = types.InlineKeyboardButton(f"• CHARGED ➜ [ {ch} ] •", callback_data='x')
				cm4 = types.InlineKeyboardButton(f"• CCN ➜ [ {ccn} ] •", callback_data='x')
				cm5 = types.InlineKeyboardButton(f"• CVV ➜ [ {cvv} ] •", callback_data='x')
				cm6 = types.InlineKeyboardButton(f"• LOW FUNDS ➜ [ {lowfund} ] •", callback_data='x')
				cm7 = types.InlineKeyboardButton(f"• DECLINED ➜ [ {dd} ] •", callback_data='x')
				cm8 = types.InlineKeyboardButton(f"• TOTAL ➜ [ {total} ] •", callback_data='x')
				stop=types.InlineKeyboardButton(f"[ STOP ]", callback_data='stop')
				mes.add(cm1,status, cm3, cm4, cm5, cm6, cm7, cm8, stop)
				end_time = time.time()
				execution_time = end_time - start_time
				bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text='''@Mr_Vempire1 ''', reply_markup=mes)
				msg = f"""
✨✨ 𝐂𝐀𝐑𝐃 𝐂𝐇𝐄𝐂𝐊 𝐑𝐄𝐒𝐔𝐋𝐓 ✨✨
━━━━━━━━━━━━━━━━━━
💳 <b>𝐂𝐀𝐑𝐃</b>
<code>{cc}</code>

[ϟ] <b>𝐑𝐄𝐒𝐏𝐎𝐍𝐒𝐄</b>
<code>Payment Successful! $1.00 🔥</code>

━━━━━━━━━━━━━━━━━━
🏦 <b>𝐁𝐈𝐍 𝐈𝐍𝐅𝐎</b>
<code>{cc[:6]} • {card_type} • {brand}</code>

🏛 <b>𝐁𝐀𝐍𝐊</b>
<code>{bank}</code>

🌍 <b>𝐂𝐎𝐔𝐍𝐓𝐑𝐘</b>
<code>{country} {country_flag}</code>

⏱ <b>𝐓𝐈𝐌𝐄</b>
<code>{execution_time:.1f} sec</code>

━━━━━━━━━━━━━━━━━━
🤖 <b>𝐁𝐎𝐓</b>
<b>@Mr_Vempire1</b>
"""
				
				print(last)
				if 'Payment Successful!' in last:
					ch += 1
					bot.reply_to(message, msg)
					
				elif 'Your card does not support this type of purchase' in last:
				    cvv += 1
				    				    
				elif 'security code is incorrect' in last or 'security code is invalid' in last:
					ccn += 1
					
				elif 'insufficient funds' in last:
					msg = f"""
✨✨ 𝐂𝐀𝐑𝐃 𝐂𝐇𝐄𝐂𝐊 𝐑𝐄𝐒𝐔𝐋𝐓 ✨✨
━━━━━━━━━━━━━━━━━━
💳 <b>𝐂𝐀𝐑𝐃</b>
<code>{cc}</code>

[ϟ] <b>𝐑𝐄𝐒𝐏𝐎𝐍𝐒𝐄</b>
<code>Insufficient🔥</code>

━━━━━━━━━━━━━━━━━━
🏦 <b>𝐁𝐈𝐍 𝐈𝐍𝐅𝐎</b>
<code>{cc[:6]} • {card_type} • {brand}</code>

🏛 <b>𝐁𝐀𝐍𝐊</b>
<code>{bank}</code>

🌍 <b>𝐂𝐎𝐔𝐍𝐓𝐑𝐘</b>
<code>{country} {country_flag}</code>

⏱ <b>𝐓𝐈𝐌𝐄</b>
<code>{execution_time:.1f} sec</code>

━━━━━━━━━━━━━━━━━━
🤖 <b>𝐁𝐎𝐓</b>
<b>@Mr_Vempire1</b>
"""
					lowfund += 1
					bot.reply_to(message, msg)
					
				elif 'The payment needs additional action before completion!' in last:
					msg = f'''			
𝐂𝐀𝐑𝐃: <code>{cc}</code>
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>3ds ✅</code>

𝐁𝐢𝐧 𝐈𝐧𝐟𝐨: <code>{cc[:6]}-{card_type} - {brand}</code>
𝐁𝐚𝐧𝐤: <code>{bank}</code>
𝐂𝐨𝐮𝐧𝐭𝐫𝐲: <code>{country} - {country_flag}</code>

𝐓𝐢𝐦𝐞: <code>1{"{:.1f}".format(execution_time)} second</code> 
𝐁𝐨𝐭 𝐀𝐛𝐨𝐮𝐭: @Mr_Vempire1'''
					cvv += 1
					bot.reply_to(message, msg)
				    	
				else:
					dd += 1
					time.sleep(5)
	except Exception as e:
		print(e)
	bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text='CHECKED ✅\nBOT BY ➜ @Mr_Vempire')
@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def menu_callback(call):
	with open("stop.stop", "w") as file:
		pass
if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
