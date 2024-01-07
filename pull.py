import interactions
from interactions import ActionRow, Button, spread_to_rows, ButtonStyle
import asyncio
import random
import csv
import math
from asyncio import TimeoutError
from db import (
    create_user,
    get_currency,
    add_gacha_pull,
    get_gatcha_duplicate,
    add_zenny,
    add_crystals,
    add_to_pulls,
    pull_track_checker,
)
from util import csv_reader


async def pull(ctx, bot):
    db = bot.db
    uid = ctx.author.id  # Discord user ID
    guid = ctx.guild.id  # Discord guild ID

    await create_user(db, uid, guid)
    packs = {}

    with open("data/packs.csv", newline="") as csvfile:
        reader = list(csv_reader(csvfile))
        for each in reader:
            packs[each[0]] = each[1]

    components: list[ActionRow] = spread_to_rows(
        Button(
            style=ButtonStyle.BLURPLE,
            label=f"{packs['character']} (5 C)",
            custom_id="character",
        ),
        Button(
            style=ButtonStyle.GRAY,
            label=f"{packs['item']} (5 C)",
            custom_id="item",
        ),
        Button(
            style=ButtonStyle.GREEN,
            label=f"{packs['standard']} (50 Z)",
            custom_id="standard",
        ),
    )

    # Get the users current currency and display options
    # Need to make pack_message dynamic
    currency = await get_currency(db, uid, guid)

    pack_message = await ctx.send(
        f"\n You currently have:\n<:mone:1138737098485157938> {currency[0]}\n<:Prism:1138732378639048765> {currency[1]} ",
        components=components,
        ephemeral=True,
    )
    try:
        pull_bought = await bot.wait_for_component(components=components, timeout=10)
    except TimeoutError:
        components[0].components[0].disabled = True
        components[0].components[1].disabled = True
        components[0].components[2].disabled = True
        await ctx.edit(pack_message, components=components)
        return

    # Deal with old message
    components[0].components[0].disabled = True
    components[0].components[1].disabled = True
    components[0].components[2].disabled = True
    await ctx.edit(pack_message, components=components)

    # Pulling TODO
    # ☑ Change pool based on pack
    # ☑ Pull pool of characters
    # ☑ Calculate odds
    # ☑ Pull character
    # ☑ Add each previous pull attempt:
    # ☐ Every ten pulls = 1 guaranteed 4 star, 50/50 if it is the featured 5 star character or not.
    # ☑ Every five pulls thereafter = 1 guaranteed 4 star, more likely to be 5 star
    # use pull_tracker for this
    # ☑ Duplicate pulls are converted into special currency regardless of rarity

    pull_bought_name = pull_bought.ctx.custom_id

    if pull_bought_name == "standard":
        if currency[0] < 50:
            await pull_bought.ctx.send(
                "You don't have enough <:mone:1138737098485157938> to buy this pack!",
                ephemeral=True,
            )
            return
        else:
            await add_zenny(db, uid, guid, -10)
    else:
        if currency[1] < 5:
            await pull_bought.ctx.send(
                "You don't have enough <:Prism:1138732378639048765> to buy this pack!",
                ephemeral=True,
            )
            return
        else:
            await add_crystals(db, uid, guid, -5)

    await pull_bought.ctx.send("Gacha in progress...", ephemeral=True)

    print(f"{uid} selected: {pull_bought_name}")

    ####

    ### FIXME SHOULD BE BASED ON BANNER
    ten_pulls = await pull_track_checker(
        db, uid, guid
    )  # Add to tracker and check if they need a guarenteed 4 star
    gatcha = get_banner(pull_bought_name, ten_pulls)

    print(f"{uid} got: {gatcha[0]}")

    if await get_gatcha_duplicate(db, uid, guid, gatcha[0]):
        if pull_bought_name == "standard":
            await add_zenny(db, uid, guid, 10)
        else:
            await add_crystals(db, uid, guid, 1)
    else:
        await add_gacha_pull(db, uid, guid, gatcha[0])

    await add_to_pulls(db, uid, guid)  # Add to total
    await play_rating_anim(ctx, gatcha[1], gatcha[0][0])


def get_banner(pack, ten_pulls):
    gatcha = None
    type = 0
    rating = 0

    with open(f"data/odds/odds_{pack}.csv", newline="") as csvfile:
        reader = list(csv_reader(csvfile))
        if ten_pulls == False:
            print("Less then 10 pulls")
            # First check: What rating did they get
            weighted_odds_rating = []
            for row in reader:
                weighted_odds_rating.append(int(math.ceil(float(row[1]))))
            rating = int(
                random.choices((0, 1, 2, 3, 4), tuple(weighted_odds_rating))[0]
            )
            print("rating:" + str(rating))
        else:
            print("Guaranteed 3/4 star")
            rating = random.choices((3, 4), (90, 10))[0]

        # Second check: did they get a character, featured character or item?
        weighted_odds_type = []

        for x in range(3):
            weighted_odds_type.append(int(math.ceil(float(reader[rating][x + 2]))))
        type = int(random.choices((0, 1, 2), tuple(weighted_odds_type))[0])
        # Third check: what thing did they get?

    match type:
        case 0:  # Featured Character
            with open(
                f"data/characters/characters{rating}.csv", newline=""
            ) as csvfile2:
                print("Got a featured character")
                reader2 = list(csv_reader(csvfile2))
                featured = []
                for each in reader2:
                    if each[2] == "true":
                        featured.append(each)
                gatcha = [random.choice(featured), "characters"]

        case 1:  # Any Character (Full pool)
            with open(
                f"data/characters/characters{rating}.csv", newline=""
            ) as csvfile2:
                reader2 = list(csv_reader(csvfile2))
                gatcha = [random.choice(reader2), "characters"]

        case 2:  # Any item (Full pool)
            with open(f"data/items/items{rating}.csv", newline="") as csvfile2:
                reader2 = list(csv_reader(csvfile2))
                gatcha = [random.choice(reader2), "items"]

    return gatcha, rating


async def play_rating_anim(ctx, rating, character):
    time_adjust = rating + 1.2
    with open(f"assets/public/stars/{rating+1}.gif", "rb") as f:
        file = interactions.File(file=f, file_name=f"{rating+1}.gif")
        await ctx.send(files=file, delete_after=time_adjust)  # Send the animation
        await asyncio.sleep(time_adjust)

    stars = ":star:" * (
        rating + 1
    )  # This is the first time I've ever actually had to use this

    print(character)
    character_card_embed = interactions.Embed(
        title=character[0] + "\n" + stars,
        description="000000000000000000000000",
        color=0x312D2C,
    )
    character_card_embed.set_image(url=character[1])
    character_card_info_embed = interactions.Embed(
        description="This is for stats and stuff",
        color=0xF500D4,
    )

    await ctx.send(embeds=character_card_embed)
    await ctx.send(embeds=character_card_info_embed)
