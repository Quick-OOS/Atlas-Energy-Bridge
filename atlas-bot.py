import os
import subprocess
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# CONFIG
BOT_TOKEN = "8608471507:AAGYn2ZWoYH2sl7-qSqr70gN9HfjMIj1NEA"
AUTHORISED_CHAT_ID = 6613552834
SITE_DIR = r"C:\Users\footb\Documents\GitHub\Atlas-Energy-Bridge"

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Track pending changes per user
pending_changes = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != AUTHORISED_CHAT_ID:
        await update.message.reply_text("Unauthorised access.")
        return

    user_request = update.message.text.strip()
    chat_id = update.effective_chat.id

    # Check if user is confirming a pending change
    if user_request.lower() in ["yes", "y", "confirm", "push", "deploy"]:
        if chat_id not in pending_changes:
            await update.message.reply_text(
                "No pending changes to confirm. Send a request first."
            )
            return

        await update.message.reply_text("Pushing to GitHub...")
        try:
            subprocess.run(["git", "add", "."], cwd=SITE_DIR, check=True, shell=True)
            commit_msg = pending_changes[chat_id][:50]
            subprocess.run(
                ["git", "commit", "-m", f"Bot: {commit_msg}"],
                cwd=SITE_DIR,
                check=True,
                shell=True
            )
            subprocess.run(["git", "push"], cwd=SITE_DIR, check=True, shell=True)
            del pending_changes[chat_id]
            await update.message.reply_text(
                "Done. Live at atlasenergybridge.com in about 30-60 seconds."
            )
        except Exception as e:
            await update.message.reply_text(f"Push failed: {str(e)}")
        return

    # Check if user wants to cancel
    if user_request.lower() in ["no", "cancel", "abort", "discard"]:
        if chat_id not in pending_changes:
            await update.message.reply_text("Nothing to cancel.")
            return
        try:
            subprocess.run(
                ["git", "checkout", "."],
                cwd=SITE_DIR,
                check=True,
                shell=True
            )
            del pending_changes[chat_id]
            await update.message.reply_text("Changes discarded. Ready for a new request.")
        except Exception as e:
            await update.message.reply_text(f"Could not discard changes: {str(e)}")
        return

    # New request - run Claude Code to make the change
    await update.message.reply_text(f"Working on: {user_request}\n\nThis may take 30-90 seconds...")

    try:
        result = subprocess.run(
            ["claude", "-p", user_request, "--dangerously-skip-permissions"],
            cwd=SITE_DIR,
            capture_output=True,
            text=True,
            timeout=600,
            shell=True
        )

        # Get the diff to show the user what changed
        diff_result = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=SITE_DIR,
            capture_output=True,
            text=True,
            shell=True
        )

        diff_summary = diff_result.stdout.strip()

        if not diff_summary:
            await update.message.reply_text(
                "No changes were made. Claude may not have understood the request, "
                "or the change wasn't applicable. Try being more specific."
            )
            return

        # Store the pending change
        pending_changes[chat_id] = user_request

        # Build the response message
        message = f"Here's what I changed:\n\n```\n{diff_summary}\n```\n\n"
        message += "Check the result in the files, then reply:\n"
        message += "• YES to push live\n"
        message += "• NO to discard changes\n"
        message += "• Or tell me what to refine"

        await update.message.reply_text(message, parse_mode='Markdown')

    except subprocess.TimeoutExpired:
        await update.message.reply_text("Request timed out. Try a simpler change.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Atlas bot is running with confirmation mode. Send a message in Telegram.")
    app.run_polling()

if __name__ == "__main__":
    main()