#!/usr/bin/env python

# Example: https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/conversationbot.py

import logging
import conf
from random_debate_topics import get_random_topic

from telegram import (
    Update,
    Chat
)

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
#TODO: Add README

#NOTE: Can check members and permissions here: https://python-telegram-bot.readthedocs.io/en/stable/telegram.chat.html
#NOTE: Can get new chat members here: https://python-telegram-bot.readthedocs.io/en/stable/telegram.chat.html

def start_debate(update: Update, context: CallbackContext):
    debate_start_msg = update.message

    debate_subj = ' '.join(context.args)

    logger.debug(f'Chat data: {context.chat_data}')

    if not debate_subj:
        update.effective_chat.send_message(
            'We need something to debate about.\n\n'
            f'Example: /debate {get_random_topic()}'
        )
    else:
        context.chat_data['ongoing_debate'] = True
        context.chat_data['debate_subject'] = debate_subj
        context.chat_data['phase_chain'] = ['requesting_moderator']

        debate_start_msg.reply_text(
            parse_mode='MarkdownV2',
            text=(
                f'Starting debate: **{debate_subj}**\n\n'
                'We need a moderator\\. First one to send a /moderate command will become the moderator\\. '
                'Anyone can cancel at any time by sending a /cancel command\\.\n\n'
                'Who would like to moderate?'
            )
        )


def assign_moderator(update: Update, context: CallbackContext):
    moderator = update.message.from_user
    logger.info("Assigned moderator: %s", moderator.username)

    try:
        context.chat_data['phase_chain'].append('reconnaisance')
    except KeyError:
        update.effective_chat.send_message(
            'You need to start a /debate first before you can /moderate.\n\n'
            f'Example: /debate {get_random_topic()}'
        )

    update.effective_chat.send_message(
        parse_mode='MarkdownV2',
        text=(
            f"**Your moderator is:** {moderator.full_name} "
            "**Phase:** Reconnaissance\\. Please ask your questions to clarify the debate subject\\."
            "\\#\\# Rules"
            "* Debators are only allowed to ask questions in this phase to clarify the subject being debated"
            "* The initiator is the only one who is allowed to answer these questions \\(the initiator may accept help from others on clarifying their meaning\\)"
            "* The moderator is required to encourage well-intentioned questioning and is encouraged to ask the debators to clarify their questions to facilitate in drawing more helpful information"
        )
    ).pin()


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(conf.API_TOKEN, use_context=True)

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