async def check_single_card(update: Update, context: CallbackContext):
    """Check a single card"""
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ **Please provide card details:**\n\n"
                "**Format:** `/cc 363112060601683|08|2028|7953`\n\n"
                "**Example:** `/cc 4111111111111111|12|2025|123`",
                parse_mode='Markdown'
            )
            return
        
        card_data = context.args[0]
        
        if "|" not in card_data or len(card_data.split("|")) != 4:
            await update.message.reply_text(
                "❌ **Invalid format!**\n\n"
                "Please use: `CCNUMBER|MM|YYYY|CVV`\n"
                "**Example:** `4111111111111111|12|2025|123`",
                parse_mode='Markdown'
            )
            return
        
        loading_msg = await update.message.reply_text(
            "🔍 **Checking Card...**\n\n"
            f"📤 **Card:** `{card_data}`\n"
            "⏳ *Please wait while we process your request...*",
            parse_mode='Markdown'
        )
        
        try:
            response = requests.get(f"{API_URL}{card_data}", timeout=30)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    formatted_response = format_response(result)
                    await loading_msg.delete()
                    
                    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(formatted_response, parse_mode='Markdown', reply_markup=reply_markup)
                except json.JSONDecodeError:
                    await loading_msg.delete()
                    await update.message.reply_text(
                        f"❌ **Invalid API Response**\n\n"
                        f"API returned non-JSON response.\n"
                        f"**Status Code:** {response.status_code}\n"
                        f"**Response:** `{response.text[:100]}...`",
                        parse_mode='Markdown'
                    )
            else:
                await loading_msg.delete()
                await update.message.reply_text(
                    f"❌ **API Error {response.status_code}**\n\n"
                    f"**Response:** `{response.text[:100] if response.text else 'No response'}`\n\n"
                    "Unable to process your request. Please try again.",
                    parse_mode='Markdown'
                )
        
        except requests.exceptions.Timeout:
            await loading_msg.delete()
            await update.message.reply_text(
                "⏰ **Request Timeout!**\n\n"
                "The server took too long to respond. Please try again.",
                parse_mode='Markdown'
            )
        except requests.exceptions.ConnectionError:
            await loading_msg.delete()
            await update.message.reply_text(
                "🔌 **Connection Error!**\n\n"
                "Could not connect to the API server. Please check your internet connection.",
                parse_mode='Markdown'
            )
        except Exception as e:
            await loading_msg.delete()
            logger.error(f"Error checking card: {e}")
            await update.message.reply_text(
                f"❌ **Error Occurred!**\n\n"
                f"**Details:** `{str(e)[:100]}...`\n\n"
                "Please try again later.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error in check_single_card: {e}")
        await update.message.reply_text(
            "❌ **An error occurred. Please try again.**",
            parse_mode='Markdown'
        )
