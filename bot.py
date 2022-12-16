import asyncio
import datetime
import functools
import logging
import os

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from sqlalchemy import delete, select
from pydantic import BaseModel

import db
from models import User, Drink,UserSettings 
from async_test import loop, work

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


DEFAULT_USER_SETTINGS = UserSettings(
    start_time=datetime.time(hour=8),
    daynorm=1650,
    end_time=datetime.time(hour=21),
    notify=True,
)

class End(Exception):
    pass


# Commands
def command_wrapper(func):
    @functools.wraps(func)
    async def deco(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except End:
            return None

    return deco


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    assert user is not None
    async with db.SessionLocal() as session, session.begin():
        q = select(User).where(User.user_id == user.id)
        res = await session.execute(q)
        db_user = res.scalar_one_or_none()

        if db_user is None:
            db_user = User(user_id=user.id, enabled=False, settings=DEFAULT_USER_SETTINGS.json())
            session.add(db_user)
            await update.message.reply_html(
                rf"Hi {user.mention_html()}! Nice to know you. Do you want to set some settings up? /settings ",
            )
        else:
            await update.message.reply_html(
                f"Hello again. I already know you, continue to other commands or get /help"
            )

@command_wrapper
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    assert user is not None
    db_user = await get_user_and_reply_dont_know_you(update, user)

    text = update.message.text[len('/settings '):]
    args = text.split(' ')
    if args == ['']:
        await update.message.reply_text(db_user.settings)
        return

    if args[0] == ['notify']:
        # todo
        pass

    if args[0] == ['start_time']:
        # todo
        pass

    if args[0] == ['end_time']:
        # todo
        pass

    if args[0] == ['daynorm']:
        # todo
        pass


@command_wrapper
async def drink_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    assert user is not None
    db_user = await get_user_and_reply_dont_know_you(update, user)
    text = update.message.text[len('/drink '):]

    if not text.isdigit():
        await update.message.reply_text('Need mililitres')
        return

    async with db.SessionLocal() as session, session.begin():
        mililitres = int(text)
        drink = Drink(user_id=db_user.user_id, mililitres=mililitres)
        session.add(drink)
        await session.flush()

        q = select(Drink).where(Drink.user_id == db_user.user_id).where(Drink.created_at > datetime.date.today())
        res = await session.execute(q)
        drinks_today = res.scalars()
        drank_today = sum([d.mililitres for d in drinks_today])
        await update.message.reply_text(f"Today: {drank_today}. (out of {db_user.get_settings().daynorm})")


async def get_user_and_reply_dont_know_you(update: Update, user) -> User:
    db_user = await get_user(user)
    if db_user is None:
        await update.message.reply_text('Do not know you, wanna /start?')
        raise End
    return db_user


async def get_user(user) -> User | None:
    async with db.SessionLocal() as session, session.begin():
        q = select(User).where(User.user_id == user.id)
        res = await session.execute(q)
        return res.scalar_one_or_none()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Help!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(update)
    await update.message.reply_text(update.message.text)


# Tasks management
async def work():
    print('...')


async def loop(coro, wait_time):
    while True:
        await asyncio.create_task(coro())
        await asyncio.sleep(wait_time)


# sync setup
def init_db() -> None:
    db.BaseModel.metadata.create_all(bind=db.sync_engine)


def start_bot() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    print('here')
    print('here', asyncio.get_event_loop())

    application = Application.builder().token(os.environ['WATTERINO_TOKEN']).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("drink", drink_command))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # add looping tasks
    async def _():
        asyncio.create_task(loop(work, 1))
    asyncio.get_event_loop().run_until_complete(_())

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

def main() -> None:
    init_db()
    start_bot()

if __name__ == "__main__":
    main()