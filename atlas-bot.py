import os
import subprocess
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# CONFIG - REPLACE THESE THREE VALUES
BOT_TOKEN = "8608471507:AAGYn2ZWoYH2sl7-qSqr70gN9HfjMIj1NEA"
AUTHORISED_CHAT_ID = 6613552834
SITE_DIR = r"C:\Users\footb\Documents\GitHub\Atlas-Energy-Bridge"

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != AUTHORISED_CHAT_ID:
        await update.message.reply_text("Unauthorised access.")
        return

    user_request = update.message.text
    await update.message.reply_text(f"Got it. Working on: {user_request}")

    try:
        result = subprocess.run(
            ["claude", "-p", user_request, "--dangerously-skip-permissions"],
            cwd=SITE_DIR,
            capture_output=True,
            text=True,
            timeout=600,
            shell=True
        )

        subprocess.run(["git", "add", "."], cwd=SITE_DIR, check=True, shell=True)
        commit_result = subprocess.run(
            ["git", "commit", "-m", f"Bot: {user_request[:50]}"],
            cwd=SITE_DIR,
            capture_output=True,
            text=True,
            shell=True
        )

        if commit_result.returncode == 0:
            subprocess.run(["git", "push"], cwd=SITE_DIR, check=True, shell=True)
            await update.message.reply_text(
                "Done. Pushed to GitHub. Netlify is deploying now.\n\n"
                "Live at atlasenergybridge.com in about 30-60 seconds."
            )
        else:
            await update.message.reply_text(
                "No changes were made. Claude may not have understood the request, "
                "or no actual file edits were needed. Try being more specific."
            )

    except subprocess.TimeoutExpired:
        await update.message.reply_text("Request timed out. Try a simpler change.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Atlas bot is running. Send a message in Telegram.")
    app.run_polling()

if __name__ == "__main__":
    main()