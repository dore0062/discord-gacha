from interactions.models import listen
from interactions import slash_command, SlashContext, Client
from config import db_config, discord_config
from db import create_tables
from pull import pull
import os
import interactions
import asyncpg

bot = Client(**discord_config)


# Connects to the DB and initalizes it to bot.db
async def connect_db():
    bot.db = await asyncpg.create_pool(**db_config)
    await create_tables(bot.db)


##########################
#         Events         #
##########################
@listen()
async def on_ready():
    await connect_db()
    print("Bot is ready")


##########################
#         Commands       #
##########################
# TODO:
# ☐ Pulls
# ☐ Showcase
# ☐ Inventory (only visible to user)
# ☐ Shop


@slash_command(name="pull", description="Pull a character, test command")
async def pull_debug(ctx: SlashContext):
    await ctx.defer(ephemeral=True)
    await pull(ctx, bot)


# @slash_command(name="debug", description="A debug command to do development things")
# async def pull_debug(ctx: SlashContext):


##########################
#       Extensions       #
##########################
bot.start()
