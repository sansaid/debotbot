#!/usr/bin/env python

# Example: https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/conversationbot.py

#TODO: Add a /help handler
#TODO: Add a profile photo for Debotbot
#TODO: Add handler to know if the bot has joined a group
#TODO: Add README
#TODO: Reject starting debate without appropriate bot permissions
#TODO: Try to implement slow_delay: https://python-telegram-bot.readthedocs.io/en/stable/telegram.chat.html#telegram.Chat.slow_mode_delay

#BUG: getUpdate eventually happens after using /votetocancel command. Is this because you're creating a copy of the `Update` class when passing into another function?

#NOTE: Can check members and permissions here: https://python-telegram-bot.readthedocs.io/en/stable/telegram.chat.html
#NOTE: Can get new chat members here: https://python-telegram-bot.readthedocs.io/en/stable/telegram.message.html#telegram.Message.new_chat_members

import logging
import conf
from random_debate_topics import get_random_topic
from math import ceil

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



def start_debate(update: Update, context: CallbackContext):
    debate_start_msg = update.message

    debate_subj = ' '.join(context.args)

    logger.debug(f'Chat data: {context.chat_data}')

    if context.chat_data.get('ongoing_debate'):
        update.effective_chat.send_message(
            'Debate is currently ongoing. You can vote to end this debate '
            'by sending /votetocancel or the moderator must /cancel the debate.'
        )

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
    debate_ongoing = context.chat_data.get('ongoing_debate', False)
    moderator = context.chat_data.get('moderator')

    if not debate_ongoing:
        update.effective_chat.send_message(
            'You need to start a /debate first before you can /moderate.\n\n'
            f'Example: /debate {get_random_topic()}'
        )
    elif debate_ongoing and moderator:
        update.effective_chat.send_message(
            f'Moderator already assigned, Stalin: {moderator}'
        )

    phase_chain.append('reconnaisance')
    moderator = context.chat_data['moderator'] = update.message.from_user.username

    update.effective_chat.send_message(
        parse_mode='MarkdownV2',
        text=(
            f"**Your moderator is:** {moderator.full_name}\n\n"
            "**Phase:** Reconnaissance\\. Please ask your questions to clarify the debate subject\\.\n\n"
            "\\#\\# Rules\n"
            "\\- Debators are only allowed to ask questions in this phase to clarify the subject being debated\n"
            "\\- The moderator is not allowed to pick sides or contribute to the debate other than ensuring everyone follows the rules\n"
            "\\- The initiator is the only one who is allowed to answer these questions \\(the initiator may accept help from others on clarifying their meaning\\)\n"
            "\\- The moderator is required to encourage well\\-intentioned questioning and is encouraged to ask the debators to clarify their questions to facilitate in drawing more helpful information abou the subject of debate\n"
        )
    ).pin()


def vote_cancel_debate(update: Update, context: CallbackContext):
    debate_ongoing = context.chat_data.get('ongoing_debate', False)
    moderator = context.chat_data.get('moderator')
    vote_cancel_count = context.chat_data.get('vote_cancel_counts', 0)

    members_count = update.effective_chat.get_members_count()
    tie_breaker_count = ceil(members_count / 2) if members_count % 2 else (members_count / 2) + 1

    if not debate_ongoing:
        update.effective_chat.send_message(
            'No debates ongoing to /votetocancel.'
        )
    
    if moderator:
        if update.effective_user.username == moderator:
            update.effective_chat.send_message(
                'As moderator, you can just /cancel. Your vote won\'t be counted.'
            )
    
    vote_cancel_count+=1

    if tie_breaker_count == vote_cancel_count:
        _cancel_debate(update, context)
    else:
        update.effective_chat.send_messag(
            f'Vote cancel registered. {tie_breaker_count - vote_cancel_count} more votes needed to cancel debate.'
        )


def _cancel_debate(update: Update, context: CallbackContext):
    context.chat_data = {}
    update.effective_chat.unpin_all_messages()

    update.effective_chat.send_message(
        'Debate cancelled. You can start a new one by sending the /debate command with your debate subject.'
        f'Example: /debate {get_random_topic()}'
    )
    

def cancel_debate(update: Update, context: CallbackContext):
    moderator = context.chat_data.get('moderator')

    if moderator:
        if update.effective_user.username != moderator:
            update.effective_chat.send_message(
                'Only the moderator can /cancel this debate. You can /votetocancel. '
                'If a majority of the users /votetocancel, then the debate will be cancelled.'
            )
        else:
            _cancel_debate(update, context)
    else:
        _cancel_debate(update, context)


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
    cancel_debate_handler = CommandHandler('cancel', cancel_debate)
    vote_cancel_debate_handler = CommandHandler('votetocancel', vote_cancel_debate)


    dispatcher.add_handler(start_debate_handler)
    dispatcher.add_handler(update_moderator_handler)
    dispatcher.add_handler(cancel_debate_handler)
    dispatcher.add_handler(vote_cancel_debate_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()