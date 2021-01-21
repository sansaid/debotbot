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
    CallbackContext
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

_, ASSIGN_MOD, RECON, DEBATE, RESULTS = range(5) 


def start_debate(update: Update, context: CallbackContext):
    debate_start_msg = update.message

    debate_prop = ' '.join(context.args)

    logger.debug(f'Chat data: {context.chat_data}')

    if context.chat_data.get('ongoing_debate'):
        update.effective_chat.send_message(
            'Debate is currently ongoing. You can vote to end this debate '
            'by sending /cancel or the moderator can /cancel the debate.'
        )
        return

    if not debate_prop:
        update.effective_chat.send_message(
            'We need something to debate about.\n\n'
            f'Example: /debate {get_random_topic()}'
        )
        return

    context.chat_data['debate_prop'] = debate_prop
    context.chat_data['phase'] = ASSIGN_MOD

    debate_start_msg.reply_text(
        parse_mode='MarkdownV2',
        text=(
            f'Starting debate: **{debate_prop}**\n\n'
            'We need a moderator\\. First one to send a /moderate command will become the moderator\\. '
            'Anyone can cancel at any time by sending a /cancel command\\.\n\n'
            'Who would like to moderate?'
        )
    )
    
    return


def assign_moderator(update: Update, context: CallbackContext):
    phase = context.chat_data.get('phase', 0)
    moderator = context.chat_data.get('moderator')

    if not phase:
        update.effective_chat.send_message(
            'You need to start a /debate first before you can /moderate.\n\n'
            f'Example: /debate {get_random_topic()}'
        )
        return
    elif phase and moderator:
        update.effective_chat.send_message(
            f'Moderator already assigned, Stalin: {moderator}'
        )
        return

    context.chat_data['phase'] = RECON
    moderator = context.chat_data['moderator'] = update.message.from_user

    update.effective_chat.send_message(
        parse_mode='MarkdownV2',
        text=(
            f"Debate: {context.chat_data.get('debate_prop')}"
            f"**Moderator:** {moderator.full_name}\n\n"
            "**Phase:** Reconnaissance\\. Please ask your questions to clarify the debate proposition\\.\n\n"
            "\\#\\# Rules\n"
            "\\- Debators are only allowed to ask questions in this phase to clarify the proposition being debated\n"
            "\\- The moderator is not allowed to pick sides or contribute to the debate other than ensuring everyone follows the rules\n"
            "\\- The initiator is the only one who is allowed to answer these questions \\(the initiator may accept help from others on clarifying their meaning\\)\n"
            "\\- The moderator is required to encourage well\\-intentioned questioning and is encouraged to ask the debators to clarify their questions to facilitate in drawing more helpful information about the proposition\n"
            "\\- Once the moderator has ensured that everyone has gathered their information, they can start the debate by sending /begin\n"
        )
    ).pin()


def _vote_cancel_debate(update: Update, context: CallbackContext):
    vote_cancel_count = context.chat_data.get('vote_cancel_counts', 0)

    members_count = update.effective_chat.get_members_count() - 2 # subtracting moderator and bot
    tie_breaker_count = ceil(members_count / 2) if members_count % 2 else (members_count / 2) + 1
    
    vote_cancel_count+=1

    if tie_breaker_count == vote_cancel_count:
        return _cancel_debate(update, context, 'group vote')

    update.effective_chat.send_messag(
        f'You\'ve voted to cancel. {tie_breaker_count - vote_cancel_count} more votes '
        'needed from non-moderators to cancel debate.'
    )


def _cancel_debate(update: Update, context: CallbackContext, via: str):
    context.chat_data.clear()
    update.effective_chat.unpin_all_messages()

    update.effective_chat.send_message(
        f'Debate cancelled by {via}. You can start a new one by sending the /debate command with your proposition.\n\n'
        f'Example: /debate {get_random_topic()}'
    )
    return
    

def cancel_debate(update: Update, context: CallbackContext):
    moderator = context.chat_data.get('moderator')
    phase = context.chat_data.get('phase', 0)

    if not phase:
        update.effective_chat.send_message('No debate ongoing to cancel.')
        return

    if moderator:
        if update.effective_user.username != moderator.username:
            _vote_cancel_debate(update, context)
            
        return _cancel_debate(update, context, 'moderator')

    return _cancel_debate(update, context, 'user before moderator was assigned')


def _send_survey(update: Update, context: CallbackContext):
    update.effective_chat.send_poll(
        question=context.chat_data['debate_prop'],
        options=['For', 'Against', 'On the fence']
    )
    return

def begin_debate(update: Update, context: CallbackContext):
    moderator = context.chat_data.get('moderator')
    phase = context.chat_data.get('phase', 0)

    if not phase:
        update.effective_chat.send_message('No debate ongoing to begin.')
        return

    if moderator:
        if update.effective_user.username != moderator.username:
            update.effective_chat.send_message('Only the moderator can send the /begin command.')
            return
        
        context.chat_data['phase'] = DEBATE

        update.effective_chat.unpin_all_messages()

        update.effective_chat.send_message(
            parse_mode='MarkdownV2',
            text=(
                f"Debate: {context.chat_data.get('debate_prop')}"
                f"**Moderator:** {moderator.full_name}\n\n"
                "**Phase:** Debate\n\n"
                "\\#\\# Rules\n"
                "\\- Debators are only allowed to send messages with one of 6 commands: /meta, /conclude, /poi, /for, /against, /lf or /cancel\n"
                "\\- The moderator is not allowed to pick sides or contribute to the debate other than ensuring everyone follows the rules\n"
                "\\- The moderator is required to ensure that all debators follow the rules\n"
                "\\- The moderator is required to encourage is required to notify debators if their argument uses a logical fallacy and encourage the debator to update their argument\n"
                "\\- If debators have no more arguments to present, they may /conclude their debate. The debate will officially /conclude when a majority of debators /conclude.\n"
                "\\- The debate will officially /conclude when the moderator sends the /conclude command\n"
                "\\- Only use the /cancel command to ungracefully end the debate\n"
            )
        ).pin()

        _send_survey(update, context)
    

def decorator_count(update: Update, context: CallbackContext):
    command = re.match(r'\s*/(\w+)\s+.*$', update.effective_message.text)

    if context.chat_data.get(f'{command}_count'):
        context.chat_data[f'{}_count'] += 1
    else:
        context.chat_data[f'{}_count'] = 1
    
    return


def conclude_debate(update: Update, context: CallbackContext):
    phase = context.chat_data.get('phase', 0)

    if phase != DEBATE:
        update.effective_chat.send_message('TODO')


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
    begin_debate_handler = CommandHandler('begin', begin_debate)
    conclude_debate_handler = CommandHandler('conclude', conclude_debate)
    decorator_handler = CommandHandler(['meta', 'lf', 'for', 'against', 'poi'], decorator_count)

    dispatcher.add_handler(start_debate_handler)
    dispatcher.add_handler(update_moderator_handler)
    dispatcher.add_handler(cancel_debate_handler)
    dispatcher.add_handler(conclude_debate_handler)
    dispatcher.add_handler(begin_debate_handler)
    dispatcher.add_handler(decorator_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()