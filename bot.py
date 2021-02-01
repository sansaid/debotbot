#!/usr/bin/env python

import logging
import os
import re
from math import ceil
from telegram import (Update, Chat, ParseMode)
from telegram.ext import (Updater, CommandHandler, CallbackContext)

from utils.random_debate_topics import get_random_topic

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

_, ASSIGN_MOD, RECON, DEBATE, RESULTS = range(5)

def load_envs():
    required_envs = ['TG_API_TOKEN']

    try:
        return { env:os.environ[env] for env in required_envs }
    except KeyError as e:
        raise Exception(f'Missing environment variable: {e.args[0]}') from e
        

def start_debate(update: Update, context: CallbackContext):
    debate_start_msg = update.message

    debate_prop = ' '.join(context.args)

    logger.debug(f'Chat data: {context.chat_data}')

    if context.chat_data.get('phase', 0):
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
        parse_mode=ParseMode.HTML,
        text=(f"""
<b>Starting debate:</b> {debate_prop}

We need a moderator. First one to send a /moderate command will become the moderator. Anyone can cancel at any time by sending a /cancel command.

Who would like to moderate?
 """))
    
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
            f'Moderator already assigned: {moderator.full_name}'
        )
        return

    context.chat_data['phase'] = RECON
    moderator = context.chat_data['moderator'] = update.message.from_user

    update.effective_chat.unpin_all_messages()
    update.effective_chat.send_message(
        parse_mode=ParseMode.HTML,
        text=(f"""
<b>Debate:</b> {context.chat_data.get('debate_prop')}

<b>Moderator:</b> {moderator.full_name}

<b>Phase:</b> Reconnaissance. Please ask your questions to clarify the debate proposition.

<b><u>RULES</u></b>
- Debators are only allowed to ask questions in this phase to clarify the proposition being debated. Please use the /poi command for information gathering.
- The moderator is not allowed to pick sides or contribute to the debate other than ensuring everyone follows the rules
- The initiator is the only one who is allowed to answer these questions (the initiator may accept help from others on clarifying their meaning)
- The moderator is required to encourage well-intentioned questioning and is encouraged to ask the debators to clarify their questions to facilitate in drawing more helpful information about the proposition
- Once the moderator has ensured that everyone has gathered their information, they can start the debate by sending /begin
""")).pin()


def _vote_close_debate(update: Update, context: CallbackContext, close_type: str):
    vote_count = context.chat_data.get(f'vote_{close_type}_counts', 0)

    members_count = update.effective_chat.get_members_count() - 2 # subtracting moderator and bot
    tie_breaker_count = ceil(members_count / 2) if members_count % 2 else (members_count / 2) + 1
    
    vote_count+=1

    if tie_breaker_count == vote_count:
        _close_debate(update, context, 'group vote')
        
        return

    update.effective_chat.send_message(
        f'You\'ve voted to {close_type}. {tie_breaker_count - vote_conclude_count} more votes '
        f'needed from non-moderators to {close_type} debate.'
    )


def _cleanup_debate(update: Update, context: CallbackContext):
    context.chat_data.clear()
    update.effective_chat.unpin_all_messages()


def _close_debate(update: Update, context: CallbackContext, via: str, close_type: str):
    action = ''

    if close_type == 'conclude':
        action = 'concluded'
        _send_survey(update, context, 'POST-DEBATE')
        _send_stats(update, context)
    elif close_type == 'cancel':
        action = 'cancelled'

    update.effective_chat.send_message(
        f'Debate {action} by {via}. You can start a new one by sending the /debate command with your proposition.\n\n'
        f'Example: /debate {get_random_topic()}'
    )

    _cleanup_debate(update, context)

    return
    

def close_debate(update: Update, context: CallbackContext):
    moderator = context.chat_data.get('moderator')
    phase = context.chat_data.get('phase', 0)
    command = _get_command(update.effective_message.text)

    if not phase:
        update.effective_chat.send_message(f'No debate ongoing to {command}.')
        return

    if moderator:
        if update.effective_user.username != moderator.username:
            _vote_close_debate(update, context, command)
        
        _close_debate(update, context, 'moderator', command)
        return

    _close_debate(update, context, 'user before moderator was assigned', command)
    return


def _send_survey(update: Update, context: CallbackContext, stage: str):
    update.effective_chat.send_poll(
        question=f"{stage}: {context.chat_data['debate_prop']}",
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
            parse_mode=ParseMode.HTML,
            text=(f"""
<b>Debate:</b> {context.chat_data.get('debate_prop')}

<b>Moderator:</b> {moderator.full_name}

<b>Phase:</b> Debate

<b><u>RULES</u></b>
- Debators are only allowed to send messages with one of 6 commands: /meta, /conclude, /poi, /for, /against, /lf or /cancel
- The moderator is not allowed to pick sides or contribute to the debate other than ensuring everyone follows the rules
- The moderator is required to ensure that all debators follow the rules
- The moderator is required to encourage is required to notify debators if their argument uses a logical fallacy and encourage the debator to update their argument
- If debators have no more arguments to present, they may /conclude their debate. The debate will officially /conclude when a majority of debators /conclude.
- The debate will officially /conclude when the moderator sends the /conclude command
- Only use the /cancel command to ungracefully end the debate
""")).pin()

        _send_survey(update, context, 'PRE-DEBATE')


def _get_command(msg):
    match = re.match(r'\s*/(\w+)\s*.*$', msg)

    if match:
        return match.group(1)
    
    return ''


def decorator_count(update: Update, context: CallbackContext):
    command = _get_command(update.effective_message.text)

    if context.chat_data.get(f'{command}_count'):
        context.chat_data[f'{command}_count'] += 1
    else:
        context.chat_data[f'{command}_count'] = 1
    
    return


def _send_stats(update: Update, context: CallbackContext):
    msg = f"""
<b>Debate stats:</b>

- For arguments made: {context.chat_data.get('for_count', 0)}
- Against arguments made: {context.chat_data.get('against_count', 0)}
- POIs requested: {context.chat_data.get('poi_count', 0)}
- Logical fallacies raised: {context.chat_data.get('lf_count', 0)}
- Meta comments made: {context.chat_data.get('meta_count', 0)}
"""

    update.effective_chat.send_message(
        parse_mode=ParseMode.HTML,
        text=msg
    )

    return


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    envs = load_envs()
    updater = Updater(envs['TG_API_TOKEN'], use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Create the command handlers
    start_debate_handler = CommandHandler('debate', start_debate)
    update_moderator_handler = CommandHandler('moderate', assign_moderator)
    close_debate_handler = CommandHandler(['cancel', 'conclude'], close_debate)
    begin_debate_handler = CommandHandler('begin', begin_debate)
    decorator_handler = CommandHandler(['meta', 'lf', 'for', 'against', 'poi'], decorator_count)

    dispatcher.add_handler(start_debate_handler)
    dispatcher.add_handler(update_moderator_handler)
    dispatcher.add_handler(close_debate_handler)
    dispatcher.add_handler(begin_debate_handler)
    dispatcher.add_handler(decorator_handler)

    # Start the Bot
    updater.start_polling(clean=True)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()