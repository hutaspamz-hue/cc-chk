async def process_card_list(update: Update, cards):
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
            
            await update.message.reply_text(
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
            await update.message.reply_text(
                "❌ **No valid cards found!**\n\n"
                "**Correct Format:** `CCNUMBER|MM|YYYY|CVV`",
                parse_mode='Markdown'
            )
            return
        
        loading_msg = await update.message.reply_text(
            "🔍 **Checking Multiple Cards...**\n\n"
            f"📊 **Total Cards:** {len(valid_cards):,}\n"
            f"⏳ **Status:** Processing...\n"
            f"🔗 **API:** {API_URL}\n"
            "━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )
        
        results = []
        live_cards = []
        die_cards = []
        error_cards = []
        
        # Test the API first with one card
        test_card = valid_cards[0] if valid_cards else ""
        test_url = f"{API_URL}{test_card}"
        
        await loading_msg.edit_text(
            f"🔍 **Testing API Connection...**\n\n"
            f"📊 **Total Cards:** {len(valid_cards):,}\n"
            f"🔗 **Test URL:** `{test_url[:50]}...`\n"
            f"⏳ **Status:** Testing API...",
            parse_mode='Markdown'
        )
        
        # Test API first
        try:
            test_response = requests.get(test_url, timeout=10)
            test_status = test_response.status_code
            
            if test_status == 200:
                try:
                    test_data = test_response.json()
                    logger.info(f"API Test successful: {test_status}, Response: {test_data}")
                except:
                    logger.info(f"API Test successful: {test_status}, but non-JSON response")
            else:
                logger.error(f"API Test failed: Status {test_status}, Response: {test_response.text[:100]}")
                
            await loading_msg.edit_text(
                f"🔍 **Checking Multiple Cards...**\n\n"
                f"📊 **Total Cards:** {len(valid_cards):,}\n"
                f"✅ **API Test:** Status {test_status}\n"
                f"⏳ **Status:** Processing cards...",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"API Test Exception: {e}")
            await loading_msg.edit_text(
                f"🔍 **API Connection Failed!**\n\n"
                f"❌ **Error:** `{str(e)[:100]}`\n"
                f"🔗 **API URL:** {API_URL}\n\n"
                f"Please try again later.",
                parse_mode='Markdown'
            )
            return
        
        for i, card in enumerate(valid_cards, 1):
            try:
                # Update progress every 10 cards or at boundaries
                if i % 10 == 0 or i == 1 or i == len(valid_cards):
                    progress = int((i / len(valid_cards)) * 100)
                    progress_bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
                    
                    try:
                        await loading_msg.edit_text(
                            f"🔍 **Checking Multiple Cards...**\n\n"
                            f"📊 **Total Cards:** {len(valid_cards):,}\n"
                            f"🔄 **Processed:** {i:,}/{len(valid_cards):,}\n"
                            f"📈 **Progress:** {progress}%\n"
                            f"[{progress_bar}]\n"
                            f"⏳ **Status:** Checking card #{i:,}...",
                            parse_mode='Markdown'
                        )
                    except:
                        pass  # Ignore edit errors
                
                try:
                    # Add headers to mimic browser request
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json',
                    }
                    
                    response = requests.get(f"{API_URL}{card}", timeout=15, headers=headers)
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            logger.debug(f"Card {i}: Status 200, Response: {result}")
                            
                            status = result.get('status', '').lower()
                            message = result.get('message', '')
                            
                            if status == 'live':
                                live_cards.append(card)
                                card_info = result.get('card', {})
                                if isinstance(card_info, dict):
                                    bank = card_info.get('bank', 'Unknown')
                                    card_type = card_info.get('type', 'Unknown')
                                    card_result = f"✅ **LIVE #{i}**\n┣ **Bank:** {bank}\n┣ **Type:** {card_type}\n┗ `{card}`"
                                else:
                                    card_result = f"✅ **LIVE #{i}**\n┗ `{card}`"
                            elif status == 'die':
                                die_cards.append(card)
                                card_result = f"❌ **DIE #{i}**\n┗ `{card}`"
                            else:
                                # Unknown status
                                error_cards.append(card)
                                card_result = f"⚠️ **UNKNOWN #{i}**\n┣ **Status:** {status}\n┣ **Message:** {message[:30]}\n┗ `{card}`"
                            
                            results.append(card_result)
                            
                        except json.JSONDecodeError:
                            error_cards.append(card)
                            card_result = f"⚠️ **JSON ERROR #{i}**\n┗ `{card}`\n┗ **Response:** `{response.text[:50]}`"
                            results.append(card_result)
                            logger.error(f"JSON decode error for card {i}: {response.text[:100]}")
                            
                    else:
                        # API returned an error status
                        error_cards.append(card)
                        card_result = f"⚠️ **API {response.status_code} #{i}**\n┗ `{card}`\n┗ **Response:** `{response.text[:50] if response.text else 'No response'}`"
                        results.append(card_result)
                        logger.error(f"API error {response.status_code} for card {i}: {response.text[:100]}")
                
                except requests.exceptions.Timeout:
                    error_cards.append(card)
                    card_result = f"⚠️ **TIMEOUT #{i}**\n┗ `{card}`"
                    results.append(card_result)
                    logger.warning(f"Timeout for card {i}")
                except requests.exceptions.ConnectionError:
                    error_cards.append(card)
                    card_result = f"⚠️ **CONN ERROR #{i}**\n┗ `{card}`"
                    results.append(card_result)
                    logger.error(f"Connection error for card {i}")
                except Exception as e:
                    error_cards.append(card)
                    card_result = f"⚠️ **ERROR #{i}**\n┗ `{card}`\n┗ **Reason:** `{str(e)[:50]}`"
                    results.append(card_result)
                    logger.error(f"Error checking card {i}: {e}")
            
            except Exception as e:
                error_cards.append(card)
                card_result = f"⚠️ **PROCESS ERROR #{i}**\n┗ `{card}`"
                results.append(card_result)
                logger.error(f"Processing error for card {i}: {e}")
        
        try:
            await loading_msg.delete()
        except:
            pass
        
        # Log summary for debugging
        logger.info(f"Bulk check complete: Live={len(live_cards)}, Die={len(die_cards)}, Errors={len(error_cards)}")
        
        summary = f"""
📊 **BULK CHECK COMPLETE**

━━━━━━━━━━━━━━━━━━━━
📈 **SUMMARY:**
┣ ✅ **Live Cards:** {len(live_cards):,}
┣ ❌ **Dead Cards:** {len(die_cards):,}
┣ ⚠️ **Errors:** {len(error_cards):,}
┗ 🔢 **Total:** {len(valid_cards):,}

⏱️ **Processing Time:** {len(valid_cards) * 2}s
🔗 **API URL:** {API_URL}
━━━━━━━━━━━━━━━━━━━━

**RESULTS:**
        """
        
        await update.message.reply_text(summary, parse_mode='Markdown')
        
        # Send results in batches to avoid message length limits
        if results:
            # Group results by type for better organization
            live_results = [r for r in results if "LIVE" in r]
            die_results = [r for r in results if "DIE" in r]
            error_results = [r for r in results if "ERROR" in r or "TIMEOUT" in r or "UNKNOWN" in r]
            
            # Send live results first (if any)
            if live_results:
                await update.message.reply_text(
                    f"✅ **LIVE CARDS ({len(live_results)}):**\n" + 
                    "━━━━━━━━━━━━━━━━",
                    parse_mode='Markdown'
                )
                batch_size = 10
                for i in range(0, len(live_results), batch_size):
                    batch = live_results[i:i + batch_size]
                    result_text = "\n\n━━━━━━━━━━━━━━━━\n\n".join(batch)
                    await update.message.reply_text(result_text, parse_mode='Markdown')
            
            # Send die results
            if die_results:
                await update.message.reply_text(
                    f"❌ **DEAD CARDS ({len(die_results)}):**\n" + 
                    "━━━━━━━━━━━━━━━━",
                    parse_mode='Markdown'
                )
                batch_size = 15
                for i in range(0, len(die_results), batch_size):
                    batch = die_results[i:i + batch_size]
                    result_text = "\n\n".join(batch)
                    await update.message.reply_text(result_text, parse_mode='Markdown')
            
            # Send error results (summarized if too many)
            if error_results:
                if len(error_results) > 20:
                    error_types = {}
                    for err in error_results:
                        if "API " in err:
                            err_type = "API Error"
                        elif "TIMEOUT" in err:
                            err_type = "Timeout"
                        elif "CONN ERROR" in err:
                            err_type = "Connection Error"
                        elif "JSON ERROR" in err:
                            err_type = "JSON Error"
                        else:
                            err_type = "Other Error"
                        error_types[err_type] = error_types.get(err_type, 0) + 1
                    
                    error_summary = "⚠️ **ERROR SUMMARY:**\n"
                    for err_type, count in error_types.items():
                        error_summary += f"┣ **{err_type}:** {count}\n"
                    
                    await update.message.reply_text(
                        f"{error_summary}\n"
                        f"**Total Errors:** {len(error_results)}\n\n"
                        f"First 5 errors:",
                        parse_mode='Markdown'
                    )
                    
                    # Show first 5 errors
                    for i in range(min(5, len(error_results))):
                        await update.message.reply_text(error_results[i], parse_mode='Markdown')
                else:
                    await update.message.reply_text(
                        f"⚠️ **ERRORS ({len(error_results)}):**\n" + 
                        "━━━━━━━━━━━━━━━━",
                        parse_mode='Markdown'
                    )
                    batch_size = 10
                    for i in range(0, len(error_results), batch_size):
                        batch = error_results[i:i + batch_size]
                        result_text = "\n\n━━━━━━━━━━━━━━━━\n\n".join(batch)
                        await update.message.reply_text(result_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "❌ **No results to display. All cards had errors.**\n\n"
                f"**API Test Status:** Check logs for details.\n"
                f"**Possible Issues:**\n"
                f"• API server down\n"
                f"• Network blocked\n"
                f"• Rate limiting\n"
                f"• Invalid API endpoint",
                parse_mode='Markdown'
            )
        
        if live_cards:
            # Save live cards to temporary file
            live_cards_text = "\n".join(live_cards)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(live_cards_text)
                temp_file_path = f.name
            
            # Send live cards file
            try:
                with open(temp_file_path, 'rb') as f:
                    await update.message.reply_document(
                        document=f,
                        filename=f"live_cards_{len(live_cards)}.txt",
                        caption=f"📥 **Live Cards File**\n✅ **Count:** {len(live_cards):,} cards"
                    )
            except Exception as e:
                logger.error(f"Error sending live cards file: {e}")
                # Send live cards as text if file fails
                if len(live_cards) <= 50:
                    live_text = "✅ **LIVE CARDS:**\n\n" + "\n".join([f"`{card}`" for card in live_cards])
                    await update.message.reply_text(live_text[:4000], parse_mode='Markdown')
            
            keyboard = [[InlineKeyboardButton("🔄 Check Another File", callback_data="multiple")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
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
            
            # Provide troubleshooting tips
            troubleshooting = f"""
🔧 **TROUBLESHOOTING:**

**If all cards show errors:**
1. **API might be down** - Try again later
2. **Rate limiting** - Wait a few minutes
3. **Network issues** - Check Railway logs
4. **Invalid cards** - Test with known valid cards

**Quick test:**
Try `/cc 4111111111111111|12|2025|123` (test card)
            
**Next steps:**
• Check Railway logs for API response details
• Try smaller batch (10-20 cards)
• Wait 5 minutes and try again
            """
            
            await update.message.reply_text(
                f"😞 **No live cards found!**\n\n"
                f"❌ **All {len(valid_cards):,} cards had issues.**\n"
                f"{troubleshooting}",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logger.error(f"Error in process_card_list: {e}")
        await update.message.reply_text(
            f"❌ **Critical error processing cards:**\n`{str(e)[:200]}...`\n\n"
            f"**Debug info:**\n"
            f"• Cards in file: {len(cards) if 'cards' in locals() else 'Unknown'}\n"
            f"• Valid cards: {len(valid_cards) if 'valid_cards' in locals() else 'Unknown'}\n"
            f"• API URL: `{API_URL}`\n"
            f"• Error type: `{type(e).__name__}`\n\n"
            f"Please check Railway logs for more details.",
            parse_mode='Markdown'
        )
    finally:
        # Clean up temp file if it exists
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Error cleaning up live cards temp file {temp_file_path}: {e}")
