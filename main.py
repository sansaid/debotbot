#!/usr/bin/env python

# Example: https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/conversationbot.py

import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

#TODO: Create a DebateHandler, which will store the debate state and moderates responses
#TODO: Add handler to know if the bot has joined a group

#REF: Telegram API does not support modifying user permissions 

def start_debate(update: Update, context: CallbackContext) -> int:
    debate_start_msg = update.message
    debate_subj = ' '.join(context.args)

    debate_start_msg.reply_text(
        f'Debate started: {debate_subj}'
        'We need a moderator. First one to send a /moderate command will become the moderator.'
        'Anyone can cancel at any time by sending a /cancel command.\n\n'
        'Who would like to moderate?'
    )


def assign_moderator(update: Update, context: CallbackContext) -> int:
    moderator = update.message.from_user
    logger.info("Assigned moderator: %s", moderator.username)
    update.message.reply_text(
        f"Assigned moderator: {moderator.full_name}. Reconnaissance phase has begun. Please ask your questions to clarify the debate subject.",
        reply_markup=ReplyKeyboardRemove(),
    )


def main() -> None:
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("1592113728:AAFx6mIiCIzstpOsWcEmtAp3fKCZw2tuveo", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Create the command handlers
    start_debate_handler = CommandHandler('debate', start_debate)
    update_moderator_handler = CommandHandler('moderate', assign_moderator)

    dispatcher.add_handler(start_debate_handler)
    dispatcher.add_handler(update_moderator_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()