import asyncio
import datetime
import functools
import logging
import os
import random

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
from sqlalchemy import delete, select
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

import db
from models import Drink, User, UserSettings

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


DEFAULT_USER_SETTINGS = UserSettings(
    start_time=datetime.time(hour=8),
    daynorm=1650,
    end_time=datetime.time(hour=21),
    utc_offset=3,
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
            db_user = User(
                user_id=user.id, enabled=True, settings=DEFAULT_USER_SETTINGS.json()
            )
            session.add(db_user)
            await update.message.reply_html(
                rf"Hi {user.mention_html()}! Nice to know you. Check your /settings (this will also start notifications) ",
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

    async with db.SessionLocal() as session, session.begin():
        if not db_user.chat_id:
            db_user.chat_id = update.message.chat.id
            session.add(db_user)

    text = update.message.text[len("/settings ") :]
    args = text.split(" ")
    if args == [""]:
        await update.message.reply_text(db_user.settings)
        return

    if args[0] == ["notify"]:
        # todo
        pass

    if args[0] == ["start_time"]:
        # todo
        pass

    if args[0] == ["end_time"]:
        # todo
        pass

    if args[0] == ["daynorm"]:
        # todo
        pass

    if args[0] == ["utc_offset"]:
        # todo
        pass


@command_wrapper
async def drink_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    assert user is not None
    db_user = await get_user_and_reply_dont_know_you(update, user)

    text = update.message.text[len("/drink ") :]

    if not text.isdigit():
        await update.message.reply_text("Need mililitres")
        return

    async with db.SessionLocal() as session, session.begin():
        if not db_user.chat_id:
            db_user.chat_id = update.message.chat.id
            session.add(db_user)

        mililitres = int(text)
        drink = Drink(user_id=db_user.user_id, mililitres=mililitres)
        session.add(drink)
        await session.flush()

        res = await session.execute(drinks_today_q(db_user.user_id))
        drinks_today = res.scalars()
        drank_today = sum([d.mililitres for d in drinks_today])
        await update.message.reply_text(
            f"Today: {drank_today} ({db_user.get_settings().daynorm})"
        )


async def get_user_and_reply_dont_know_you(update: Update, user) -> User:
    db_user = await get_user(user)
    if db_user is None:
        await update.message.reply_text("Do not know you, wanna /start?")
        raise End
    return db_user


async def get_user(user) -> User | None:
    async with db.SessionLocal() as session, session.begin():
        q = select(User).where(User.user_id == user.id)
        res = await session.execute(q)
        return res.scalar_one_or_none()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Help!")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_user = await get_user_and_reply_dont_know_you(update, update.effective_user)
    async with db.SessionLocal() as session, session.begin():
        db_user.enabled = False
        session.add(db_user)
    await update.message.reply_text("Bye!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(update)
    await update.message.reply_text(update.message.text)


# Queries
def drinks_today_q(user_id: int):
    q = (
        select(Drink)
        .where(Drink.user_id == user_id)
        .where(Drink.created_at > datetime.date.today())
    )
    return q


# Tasks management
async def work(context: ContextTypes.DEFAULT_TYPE):
    print(context)


async def remind(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Reminding...")

    REMINDERS = [
        "Hey sweetie, it's time to drink!",
        "Hey darling, it's time to drink!",
        "Isn't it the water time?",
        "Water-time-o-clock!",
        "I would be soo-oo thirsty if I were you...",
        "I would be soo-oo thirsty if I were you...",
        "Waterrr-rrr-rino!",
        "Here we go, it's time to drink",
        "Let's drink a little",
        "Drinking is game with no loosers...(c) Waterrino",
        "Drinking water is important. Let's drink some",
        "W-a-a-a-a-t-e-e-r",
        "Drink some!",
        "It's me, w-a-a-a-t-e-r-r-ino!!",
        "Time-time-time",
        "Mililitres...Li-li-li... What a weird word. Let's drink in litres already.",
        "A water a day keeps the doctor away (c) Waterrino",
        "One more",
        "A cup in, a cup out (c) Waterrino",
    ]

    async with db.SessionLocal() as session, session.begin():
        q = select(User).where(User.enabled == True)
        res = await session.execute(q)
        db_users = res.scalars()
        for db_user in list(db_users):
            q = select(Drink).where(
                Drink.user_id == db_user.user_id,
                Drink.created_at
                > (datetime.datetime.utcnow() - datetime.timedelta(hours=1)),
            )
            res = await session.execute(q)
            last_hour_drinks = list(res.scalars())
            user_settings = db_user.get_settings()

            res = await session.execute(drinks_today_q(db_user.user_id))
            drinks_today = list(res.scalars())
            drank_today = sum([d.mililitres for d in drinks_today])
            if drank_today > user_settings.daynorm:
                continue
            if len(last_hour_drinks) > 0:
                continue

            now_in_user_time = (
                datetime.datetime.utcnow()
                + datetime.timedelta(hours=user_settings.utc_offset)
            ).time()
            if not (
                user_settings.start_time <= now_in_user_time <= user_settings.end_time
            ):
                continue

            if db_user.chat_id and user_settings.notify:
                logger.info(f"Time to drink {db_user.user_id=}, {db_user.chat_id=}")
                text = f"{random.choice(REMINDERS)} ({drank_today}/{user_settings.daynorm})"
                await context.bot.send_message(chat_id=db_user.chat_id, text=text)


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
    application = Application.builder().token(os.environ["WATTERINO_TOKEN"]).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("drink", drink_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.job_queue.run_repeating(
        remind, interval=60 * 90, first=3
    )  # each 1.5 hour

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


def main() -> None:
    init_db()
    start_bot()


if __name__ == "__main__":
    main()
