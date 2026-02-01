import json
import requests
import logging
import asyncio
import sys
import tempfile
import os

# For python-telegram-bot v13.x
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
TOKEN = "8307343077:AAGG7qRYwcN2fJ2Wig3kMpsT7605YEb-pgU"

# API URL
API_URL = "https://chkr-api.vercel.app/api/check?cc="

def start(update: Update, context: CallbackContext):
    """Start command handler"""
    try:
        user = update.effective_user
        welcome_text = f"""
👋 **Hello {user.first_name}!**

🤖 **Welcome to Card Checker Bot**

📋 **Available Commands:**
• /cc [card] - Check a single card
• /ml - Check multiple cards from .txt file
• /help - Show help information

📌 **Format:** `CCNUMBER|MM|YYYY|CVV`

✨ **Ready to check cards!**
        """
        
        keyboard = [
            [InlineKeyboardButton("🛠️ Check Single Card", callback_data="single")],
            [InlineKeyboardButton("📊 Upload TXT File", callback_data="upload_txt")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in start: {e}")

def check_single_card(update: Update, context: CallbackContext):
    """Check a single card"""
    try:
        if not context.args:
            update.message.reply_text(
                "❌ **Please provide card details:**\n\n"
                "**Format:** `/cc 363112060601683|08|2028|7953`\n\n"
                "**Example:** `/cc 4111111111111111|12|2025|123`",
                parse_mode='Markdown'
            )
            return
        
        card_data = context.args[0]
        
        if "|" not in card_data or len(card_data.split("|")) != 4:
            update.message.reply_text(
                "❌ **Invalid format!**\n\n"
                "Please use: `CCNUMBER|MM|YYYY|CVV`\n"
                "**Example:** `4111111111111111|12|2025|123`",
                parse_mode='Markdown'
            )
            return
        
        loading_msg = update.message.reply_text(
            "🔍 **Checking Card...**\n\n"
            f"📤 **Card:** `{card_data}`\n"
            "⏳ *Please wait while we process your request...*",
            parse_mode='Markdown'
        )
        
        try:
            response = requests.get(f"{API_URL}{card_data}", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                formatted_response = format_response(result)
                context.bot.delete_message(chat_id=loading_msg.chat_id, message_id=loading_msg.message_id)
                
                keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                update.message.reply_text(formatted_response, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                context.bot.delete_message(chat_id=loading_msg.chat_id, message_id=loading_msg.message_id)
                update.message.reply_text(
                    f"❌ **API Error {response.status_code}**\n\n"
                    "Unable to process your request. Please try again.",
                    parse_mode='Markdown'
                )
        
        except requests.exceptions.Timeout:
            context.bot.delete_message(chat_id=loading_msg.chat_id, message_id=loading_msg.message_id)
            update.message.reply_text(
                "⏰ **Request Timeout!**\n\n"
                "The server took too long to respond. Please try again.",
                parse_mode='Markdown'
            )
        except Exception as e:
            context.bot.delete_message(chat_id=loading_msg.chat_id, message_id=loading_msg.message_id)
            logger.error(f"Error checking card: {e}")
            update.message.reply_text(
                f"❌ **Error Occurred!**\n\n"
                f"**Details:** `{str(e)[:100]}...`\n\n"
                "Please try again later.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error in check_single_card: {e}")
        update.message.reply_text(
            "❌ **An error occurred. Please try again.**",
            parse_mode='Markdown'
        )

def check_multiple_cards(update: Update, context: CallbackContext):
    """Check multiple cards - Prompt for file upload"""
    try:
        # If user provided cards directly in command (backward compatibility)
        if context.args:
            process_card_list(update, context, context.args)
        else:
            update.message.reply_text(
                "📤 **Please upload a .txt file**\n\n"
                "**File Requirements:**\n"
                "• Format: `.txt` file\n"
                "• Each line: `CCNUMBER|MM|YYYY|CVV`\n"
                "• Unlimited cards allowed\n\n"
                "**Example file content:**\n"
                "`4111111111111111|12|2025|123`\n"
                "`4222222222222222|06|2026|456`\n\n"
                "📎 **Upload your .txt file now...**",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error in check_multiple_cards: {e}")
        update.message.reply_text(
            "❌ **An error occurred. Please try again.**",
            parse_mode='Markdown'
        )

def handle_document(update: Update, context: CallbackContext):
    """Handle uploaded document files"""
    temp_file_path = None
    try:
        document = update.message.document
        
        # Check if it's a text file
        if not document.file_name.lower().endswith('.txt'):
            update.message.reply_text(
                "❌ **Invalid file type!**\n\n"
                "Please upload a `.txt` file only.",
                parse_mode='Markdown'
            )
            return
        
        # Download the file
        loading_msg = update.message.reply_text(
            "📥 **Downloading file...**\n\n"
            f"📄 **File:** {document.file_name}\n"
            f"📦 **Size:** {document.file_size:,} bytes\n"
            "⏳ *Please wait...*",
            parse_mode='Markdown'
        )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.txt', delete=False) as tmp_file:
            temp_file_path = tmp_file.name
            
        # Download file to temp path
        file = document.get_file()
        file.download(temp_file_path)
        
        # Read and process the file
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        context.bot.delete_message(chat_id=loading_msg.chat_id, message_id=loading_msg.message_id)
        
        # Parse cards from file
        cards = []
        lines = content.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line:  # Skip empty lines
                # Remove any quotes or extra spaces
                line = line.replace('"', '').replace("'", "").strip()
                cards.append(line)
        
        if not cards:
            update.message.reply_text(
                "❌ **Empty file!**\n\n"
                "The uploaded file contains no valid card data.",
                parse_mode='Markdown'
            )
            return
        
        # Process the cards
        process_card_list(update, context, cards)
        
    except Exception as e:
        logger.error(f"Error handling document: {e}")
        update.message.reply_text(
            f"❌ **Error processing file:**\n\n"
            f"`{str(e)[:100]}...`\n\n"
            "Please ensure the file is properly formatted.",
            parse_mode='Markdown'
        )
    finally:
        # Always clean up the temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Error cleaning up temp file {temp_file_path}: {e}")

def process_card_list(update: Update, context: CallbackContext, cards):
    """Process a list of cards - NO LIMIT ON AMOUNT"""
    temp_file_path = None
    try:
        invalid_cards = []
        valid_cards = []
        
        for card in cards:
            if "|" not in card or len(card.split("|")) != 4:
                invalid_cards.append(card)
            else:
                valid_cards.append(card)
        
        if invalid_cards:
            invalid_text = "\n".join(invalid_cards[:5])
            if len(invalid_cards) > 5:
                invalid_text += f"\n... and {len(invalid_cards) - 5} more"
            
            update.message.reply_text(
                f"⚠️ **Found {len(invalid_cards)} invalid cards:**\n\n"
                f"**Correct Format:** `CCNUMBER|MM|YYYY|CVV`\n\n"
                f"**Invalid cards:**\n```\n{invalid_text}\n```\n\n"
                f"✅ **Valid cards:** {len(valid_cards)}\n"
                f"❌ **Invalid cards:** {len(invalid_cards)}\n\n"
                f"Continue with valid cards only?",
                parse_mode='Markdown'
            )
            return
        
        if not valid_cards:
            update.message.reply_text(
                "❌ **No valid cards found!**\n\n"
                "**Correct Format:** `CCNUMBER|MM|YYYY|CVV`",
                parse_mode='Markdown'
            )
            return
        
        loading_msg = update.message.reply_text(
            "🔍 **Checking Multiple Cards...**\n\n"
            f"📊 **Total Cards:** {len(valid_cards):,}\n"
            f"⏳ **Status:** Processing...\n"
            "━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )
        
        results = []
        live_cards = []
        die_cards = []
        error_cards = []
        
        for i, card in enumerate(valid_cards, 1):
            try:
                # Update progress every 10 cards or at boundaries
                if i % 10 == 0 or i == 1 or i == len(valid_cards):
                    progress = int((i / len(valid_cards)) * 100)
                    progress_bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
                    
                    try:
                        context.bot.edit_message_text(
                            chat_id=loading_msg.chat_id,
                            message_id=loading_msg.message_id,
                            text=f"🔍 **Checking Multiple Cards...**\n\n"
                                 f"📊 **Total Cards:** {len(valid_cards):,}\n"
                                 f"🔄 **Processed:** {i:,}/{len(valid_cards):,}\n"
                                 f"📈 **Progress:** {progress}%\n"
                                 f"[{progress_bar}]\n"
                                 f"⏳ **Status:** Checking card #{i:,}...",
                            parse_mode='Markdown'
                        )
                    except:
                        pass  # Ignore edit errors
                
                response = requests.get(f"{API_URL}{card}", timeout=20)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status', 'Unknown').lower()
                    
                    if status == 'live':
                        live_cards.append(card)
                        card_info = result.get('card', {})
                        if isinstance(card_info, dict):
                            bank = card_info.get('bank', 'Unknown')
                            card_type = card_info.get('type', 'Unknown')
                            card_result = f"✅ **LIVE #{i}**\n┣ **Bank:** {bank}\n┣ **Type:** {card_type}\n┗ `{card}`"
                        else:
                            card_result = f"✅ **LIVE #{i}**\n┗ `{card}`"
                    else:
                        die_cards.append(card)
                        card_result = f"❌ **DIE #{i}**\n┗ `{card}`"
                    
                    results.append(card_result)
                else:
                    error_cards.append(card)
                    card_result = f"⚠️ **ERROR #{i}**\n┗ `{card}`"
                    results.append(card_result)
            
            except Exception as e:
                error_cards.append(card)
                card_result = f"⚠️ **FAILED #{i}**\n┗ `{card}`"
                results.append(card_result)
                logger.error(f"Error checking card {i}: {e}")
        
        try:
            context.bot.delete_message(chat_id=loading_msg.chat_id, message_id=loading_msg.message_id)
        except:
            pass
        
        summary = f"""
📊 **BULK CHECK COMPLETE**

━━━━━━━━━━━━━━━━━━━━
📈 **SUMMARY:**
┣ ✅ **Live Cards:** {len(live_cards):,}
┣ ❌ **Dead Cards:** {len(die_cards):,}
┣ ⚠️ **Errors:** {len(error_cards):,}
┗ 🔢 **Total:** {len(valid_cards):,}

⏱️ **Processing Time:** {len(valid_cards) * 2}s
━━━━━━━━━━━━━━━━━━━━

**RESULTS:**
        """
        
        update.message.reply_text(summary, parse_mode='Markdown')
        
        # Send results in batches to avoid message length limits
        batch_size = 10
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            result_text = "\n\n━━━━━━━━━━━━━━━━\n\n".join(batch)
            update.message.reply_text(result_text, parse_mode='Markdown')
        
        if live_cards:
            # Save live cards to temporary file
            live_cards_text = "\n".join(live_cards)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(live_cards_text)
                temp_file_path = f.name
            
            # Send live cards file
            try:
                with open(temp_file_path, 'rb') as f:
                    update.message.reply_document(
                        document=f,
                        filename=f"live_cards_{len(live_cards)}.txt",
                        caption=f"📥 **Live Cards File**\n✅ **Count:** {len(live_cards):,} cards"
                    )
            except Exception as e:
                logger.error(f"Error sending live cards file: {e}")
                # Send live cards as text if file fails
                if len(live_cards) <= 50:
                    live_text = "✅ **LIVE CARDS:**\n\n" + "\n".join([f"`{card}`" for card in live_cards])
                    update.message.reply_text(live_text[:4000], parse_mode='Markdown')
            
            keyboard = [[InlineKeyboardButton("🔄 Check Another File", callback_data="multiple")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                f"💾 **Live cards file sent!**\n"
                f"✅ **Live:** {len(live_cards):,} cards\n"
                f"❌ **Dead:** {len(die_cards):,} cards\n"
                f"⚠️ **Errors:** {len(error_cards):,} cards",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data="multiple")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                f"😞 **No live cards found!**\n\n"
                f"❌ **All cards are dead or invalid.**\n"
                f"**Total checked:** {len(valid_cards):,} cards",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logger.error(f"Error in process_card_list: {e}")
        update.message.reply_text(
            f"❌ **An error occurred while processing cards:**\n`{str(e)[:100]}...`",
            parse_mode='Markdown'
        )
    finally:
        # Clean up temp file if it exists
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Error cleaning up live cards temp file {temp_file_path}: {e}")

def format_response(data):
    """Format API response beautifully"""
    try:
        card = data.get('card', {})
        country = card.get('country', {}) if isinstance(card, dict) and isinstance(card.get('country'), dict) else {}
        meta = data.get('meta', {})
        
        status = data.get('status', 'Unknown').upper()
        status_emoji = "✅" if status == "LIVE" else "❌" if status == "DIE" else "⚠️"
        
        card_number = card.get('card', 'N/A') if isinstance(card, dict) else str(card)
        
        country_name = country.get('name', 'N/A')
        country_emoji = country.get('emoji', '')
        country_code = country.get('code', 'N/A')
        country_currency = country.get('currency', 'N/A')
        
        formatted_text = f"""
{status_emoji} **CARD CHECKER RESULTS**

━━━━━━━━━━━━━━━━━━━━
🎯 **STATUS:** **{status}**
📝 **Message:** {data.get('message', 'N/A')}
━━━━━━━━━━━━━━━━━━━━

💳 **CARD INFORMATION:**
┣ **Number:** `{card_number}`
┣ **Bank:** {card.get('bank', 'N/A') if isinstance(card, dict) else 'N/A'}
┣ **Type:** {card.get('type', 'N/A') if isinstance(card, dict) else 'N/A'}
┣ **Brand:** {card.get('brand', 'N/A') if isinstance(card, dict) else 'N/A'}
┣ **Category:** {card.get('category', 'N/A') if isinstance(card, dict) else 'N/A'}
┗ **Code:** {data.get('code', 'N/A')}

🌍 **COUNTRY INFORMATION:**
┣ **Country:** {country_name} {country_emoji}
┣ **Code:** {country_code}
┣ **Currency:** {country_currency}
┗ **Location:** {country.get('location', 'N/A') if isinstance(country, dict) else 'N/A'}

📊 **PROCESSING DETAILS:**
┣ **Time:** {meta.get('processingTime', 0)}ms
┣ **From Cache:** {'Yes ✅' if meta.get('fromCache') else 'No ❌'}
┣ **Rapid API:** {'Yes ✅' if meta.get('isRapidAPI') else 'No ❌'}
┗ **API Version:** v1.0

━━━━━━━━━━━━━━━━━━━━
⏰ **Timestamp:** Current time
━━━━━━━━━━━━━━━━━━━━

💡 **Tip:** Always verify cards from trusted sources only.
        """
        
        return formatted_text
    except Exception as e:
        logger.error(f"Error in format_response: {e}")
        return f"❌ **Error formatting response:** {str(e)[:100]}"

def help_command(update: Update, context: CallbackContext):
    """Help command handler"""
    try:
        help_text = """
📚 **HELP GUIDE**

━━━━━━━━━━━━━━━━━━━━
🔹 **SINGLE CARD CHECK:**
`/cc 363112060601683|08|2028|7953`

🔹 **MULTIPLE CARDS CHECK:**
Send `/ml` then upload a .txt file

🔹 **CARD FORMAT:**
`CCNUMBER|MM|YYYY|CVV`

━━━━━━━━━━━━━━━━━━━━
📌 **EXAMPLES:**
• Single: `/cc 4111111111111111|12|2025|123`
• Multiple: Upload .txt file with cards

━━━━━━━━━━━━━━━━━━━━
⚠️ **IMPORTANT NOTES:**
• Use only for legal purposes
• Don't share sensitive information
• Results may vary
• API rate limits apply
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="menu")],
            [InlineKeyboardButton("📖 Examples", callback_data="examples")],
            [InlineKeyboardButton("⚠️ Disclaimer", callback_data="disclaimer")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in help_command: {e}")

def button_callback(update: Update, context: CallbackContext):
    """Handle button callbacks"""
    try:
        query = update.callback_query
        query.answer()
        
        data = query.data
        
        if data == "single":
            query.edit_message_text(
                "🔍 **Single Card Check**\n\n"
                "Please use: `/cc CARDNUMBER|MM|YYYY|CVV`\n\n"
                "**Example:** `/cc 4111111111111111|12|2025|123`",
                parse_mode='Markdown'
            )
        elif data == "multiple" or data == "upload_txt":
            query.edit_message_text(
                "📊 **Multiple Cards Check**\n\n"
                "Please upload a .txt file with cards\n\n"
                "**Format:** Each line: `CCNUMBER|MM|YYYY|CVV`\n\n"
                "**Example file content:**\n"
                "`4111111111111111|12|2025|123`\n"
                "`4222222222222222|06|2026|456`\n\n"
                "📎 **Upload your .txt file now...**",
                parse_mode='Markdown'
            )
        elif data == "help":
            query.message.reply_text(
                "📚 **Need Help?**\n\n"
                "Use `/help` command or click buttons below:",
                parse_mode='Markdown'
            )
        elif data == "menu":
            keyboard = [
                [InlineKeyboardButton("🛠️ Check Single Card", callback_data="single")],
                [InlineKeyboardButton("📊 Upload TXT File", callback_data="upload_txt")],
                [InlineKeyboardButton("❓ Help", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_text = """
👋 **Welcome to Card Checker Bot**

📋 **Available Commands:**
• /cc [card] - Check a single card
• /ml - Check multiple cards from .txt file
• /help - Show help information

✨ **Click buttons below to get started!**
            """
            
            query.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
        elif data == "examples":
            query.edit_message_text(
                "📖 **Examples:**\n\n"
                "✅ **Single Card:**\n"
                "`/cc 4111111111111111|12|2025|123`\n\n"
                "✅ **Multiple Cards:**\n"
                "Upload .txt file with format:\n"
                "`4111111111111111|12|2025|123`\n"
                "`4222222222222222|06|2026|456`\n\n"
                "✅ **Format:**\n"
                "`CCNUMBER|MM|YYYY|CVV`",
                parse_mode='Markdown'
            )
        elif data == "disclaimer":
            query.edit_message_text(
                "⚠️ **DISCLAIMER**\n\n"
                "1. Use this bot for LEGAL purposes only\n"
                "2. Don't check cards without permission\n"
                "3. Results are for educational purposes\n"
                "4. The bot owner is not responsible for misuse\n"
                "5. Respect all laws and regulations",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error in button_callback: {e}")

def error_handler(update: Update, context: CallbackContext):
    """Error handler"""
    try:
        logger.error(f"Update {update} caused error {context.error}")
        
        error_text = """
❌ **An error occurred!**

🔧 **Troubleshooting:**
1. Check your internet connection
2. Verify card format is correct
3. Try again in a few moments
4. Contact support if issue persists

🔄 **Quick Fix:** Restart the bot with /start
        """
        
        if update and update.message:
            update.message.reply_text(error_text, parse_mode='Markdown')
        elif update and update.callback_query:
            update.callback_query.message.reply_text(error_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

def main():
    """Main function"""
    try:
        print("🤖 Starting Card Checker Bot...")
        print(f"🔗 Using Token: {TOKEN[:10]}...")
        
        # Create updater for python-telegram-bot v13.x
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # Command handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("cc", check_single_card))
        dp.add_handler(CommandHandler("ml", check_multiple_cards))
        dp.add_handler(CommandHandler("help", help_command))
        
        # Document handler for file uploads
        dp.add_handler(MessageHandler(Filters.document, handle_document))
        
        # Callback query handler for buttons
        dp.add_handler(CallbackQueryHandler(button_callback))
        
        # Error handler
        dp.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("✅ Bot is starting...")
        print("✅ Bot started successfully!")
        print("⚡ Bot is now running...")
        print("🔧 Press Ctrl+C to stop")
        
        # Start polling
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
