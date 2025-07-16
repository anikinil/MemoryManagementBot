TOKEN = "7755827804:AAED1PPZCTpScgMPg-ebXxn_BLZn7Bd_Xk8"

import logging

from llm import ChatAssistant, RequestHandler

from functools import wraps

from telegram import Update, ChatAction, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, error
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import threading
import time

from memory import update_display
from tools import available_functions

from google import genai

logger = logging.getLogger(__name__)


# Pre-assign menu text
FIRST_MENU = "<b>Menu 1</b>\n\nA beautiful menu with a shiny inline button."
SECOND_MENU = "<b>Menu 2</b>\n\nA better menu with even more shiny inline buttons."

# Pre-assign button text
NEXT_BUTTON = "Next"
BACK_BUTTON = "Back"
TUTORIAL_BUTTON = "Tutorial"

# Build keyboards
FIRST_MENU_MARKUP = InlineKeyboardMarkup([[
    InlineKeyboardButton(NEXT_BUTTON, callback_data=NEXT_BUTTON)
]])
SECOND_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)],
    [InlineKeyboardButton(TUTORIAL_BUTTON, url="https://core.telegram.org/bots/api")]
])

def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        def send_typing():
            time.sleep(1)
            while not stop_event.is_set():
                context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
                time.sleep(4)  # Telegram recommends sending every 4-5 seconds

        stop_event = threading.Event()
        typing_thread = threading.Thread(target=send_typing)
        typing_thread.start()

        try:
            return func(update, context, *args, **kwargs)
        finally:
            stop_event.set()
            typing_thread.join()

    return command_func

def process(update: Update, context: CallbackContext) -> None:

    # TODO make bot wait for a few seconds, before answering, so user can send multiple messages in a row
        # TODO concatenate multiple messages into one before passing to LLM

    user_input = update.message.text
    response = generate_llm_response(update, context, 'user', user_input)

    tool_calls = [part.function_call for part in response.parts if part.function_call is not None]
    if tool_calls:
        print('\nTool calls:\n')
        print(tool_calls)
        function_output = ''
        for tool in tool_calls:
            if function_to_call := available_functions.get(tool.name):
                print('Calling function: ' + tool.name)
                print('Arguments: ' + str(tool.args))
                function_output = function_to_call(**tool.args)
                send_telegram_message(update, message='Function ' + tool.name + ': ' + str(tool.args))
            else:
                function_output = 'function does not exist'
                print('Function does not exist: ' + tool.name)
                send_telegram_message(update, message='Function does not exist: ' + tool.name)

        if len(tool_calls) == 1:
            if tool_calls[0].name == 'print_subnodes':
                send_telegram_message(update, message=function_output)
            else:
                response_to_tool = generate_llm_response(update, context, 'tool', str(function_output))
                if response_to_tool.parts[0].text:
                    send_telegram_message(update, message=response_to_tool.parts[0].text)
        update_display()
    else:
        print("No tool calls\n")
        send_telegram_message(update, message=response.parts[0].text)

@send_typing_action
def generate_llm_response(update: Update, context: CallbackContext, role, input) -> None:
    
    try:
        return generate_response(role, input)
    except genai.errors.ServerError:
        print('Server error occurred, retrying...\n')
        return generate_response(role, input)


def send_telegram_message(update: Update, message) -> None:

    if message != '':
        # Escape markdown characters in the message
        if "*" in message or "_" in message:
            formatted_message = message.replace(",", "\\,").replace(".", "\\.").replace("?", "\\?").replace("!", "\\!")
            try:
                update.message.reply_text(formatted_message, parse_mode=ParseMode.MARKDOWN_V2)
            except error.BadRequest as e:
                update.message.reply_text(message)

        else:
            update.message.reply_text(message)
    else:
        update.message.reply_text('assistant responded with an empty message')


def menu(update: Update, context: CallbackContext) -> None:
    """
    This handler sends a menu with the inline buttons we pre-assigned above
    """

    context.bot.send_message(
        update.message.from_user.id,
        FIRST_MENU,
        parse_mode=ParseMode.HTML,
        reply_markup=FIRST_MENU_MARKUP
    )

def button_tap(update: Update, context: CallbackContext) -> None:
    """
    This handler processes the inline buttons on the menu
    """

    data = update.callback_query.data
    text = ''
    markup = None

    if data == NEXT_BUTTON:
        text = SECOND_MENU
        markup = SECOND_MENU_MARKUP
    elif data == BACK_BUTTON:
        text = FIRST_MENU
        markup = FIRST_MENU_MARKUP

    # Close the query to end the client-side loading animation
    update.callback_query.answer()

    # Update message content with corresponding menu section
    update.callback_query.message.edit_text(
        text,
        ParseMode.HTML,
        reply_markup=markup
    )


def main() -> None:
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler("menu", menu))

    # Register handler for inline buttons
    dispatcher.add_handler(CallbackQueryHandler(button_tap))

    # Echo any message that is not a command
    dispatcher.add_handler(MessageHandler(~Filters.command, process))

    # Start the Bot
    updater.start_polling()

    print('\nBot started\n')
    
    # Run the bot until you press Ctrl-C
    updater.idle()



if __name__ == '__main__':
    main()