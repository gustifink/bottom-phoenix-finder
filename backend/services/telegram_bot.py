import logging
from typing import List, Optional
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TelegramAlertBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.bot = None
        self.app = None
        
        if self.token:
            self.bot = Bot(token=self.token)
            self.app = Application.builder().token(self.token).build()
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up command handlers"""
        if not self.app:
            return
            
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("top", self.top_command))
        self.app.add_handler(CommandHandler("alert", self.alert_command))
        self.app.add_handler(CommandHandler("track", self.track_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🔥 Welcome to Bottom - Phoenix Token Finder Bot!

I help you find crypto tokens that have bottomed out but show strong recovery potential.

Commands:
/top - Show top 5 phoenix tokens
/alert [score] - Set alert threshold (default 80)
/track [address] - Track specific token
/stats - Show bot statistics
/help - Show this help message

Let's find some phoenixes! 🚀
        """
        await update.message.reply_text(welcome_message)
    
    async def top_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /top command"""
        # This would connect to your token manager to get top tokens
        await update.message.reply_text("🔍 Fetching top phoenix tokens...")
        # Implementation would fetch from database
    
    async def alert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alert command"""
        try:
            threshold = float(context.args[0]) if context.args else 80.0
            await update.message.reply_text(f"✅ Alert threshold set to {threshold}")
        except ValueError:
            await update.message.reply_text("❌ Please provide a valid number for threshold")
    
    async def track_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /track command"""
        if not context.args:
            await update.message.reply_text("❌ Please provide a token address to track")
            return
        
        address = context.args[0]
        await update.message.reply_text(f"📊 Now tracking token: {address}")
        # Implementation would add to watchlist
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        stats_message = """
📊 Bot Statistics:

🔍 Tokens Tracked: 0
🔥 Phoenixes Found: 0
📢 Alerts Sent: 0
⏱️ Uptime: 0h

Last scan: Just now
        """
        await update.message.reply_text(stats_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)
    
    async def send_alert(self, message: str, parse_mode: str = "HTML"):
        """Send alert to configured chat"""
        if not self.bot or not self.chat_id:
            logger.warning("Telegram bot not configured")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return False
    
    async def send_phoenix_alert(self, token_data: dict):
        """Send formatted phoenix alert"""
        message = f"""
🔥 <b>Phoenix Rising Alert!</b> 🔥

<b>Token:</b> {token_data['symbol']}
<b>Chain:</b> {token_data['chain'].upper()}
<b>BRS Score:</b> {token_data['brs_score']:.1f}/100

<b>Current Price:</b> ${token_data['current_price']:.6f}
<b>24h Change:</b> {token_data['price_change_24h']:.2f}%
<b>Volume 24h:</b> ${token_data['volume_24h']:,.0f}
<b>Liquidity:</b> ${token_data['liquidity_usd']:,.0f}

<b>Status:</b> {token_data['category']}
<b>Description:</b> {token_data['description']}

<a href="https://dexscreener.com/{token_data['chain']}/{token_data['address']}">View on Dexscreener</a>
        """
        
        return await self.send_alert(message)
    
    async def start_bot(self):
        """Start the bot polling"""
        if self.app:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
    
    async def stop_bot(self):
        """Stop the bot"""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown() 