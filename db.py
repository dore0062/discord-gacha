from asyncpg import Pool


async def create_tables(pool: Pool):
    async with pool.acquire() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                id BIGSERIAL PRIMARY KEY NOT NULL,
                user_id BIGINT NOT NULL,
                guild_id BIGINT NOT NULL,
                currency_zenny BIGINT NOT NULL DEFAULT 0,
                currency_crystals BIGINT NOT NULL DEFAULT 0,
                pulls BIGINT NOT NULL DEFAULT 0,
                pull_track INT NOT NULL DEFAULT 0,
                pity_track INT NOT NULL DEFAULT 0,
                characters text[],
                items text[]
            )
            """
        )


async def create_user(pool: Pool, user_id, guild_id):
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            "SELECT * FROM users WHERE user_id=$1 AND guild_id=$2", user_id, guild_id
        )
        if record:
            return

        await connection.execute(
            "INSERT INTO users(user_id, guild_id) VALUES($1, $2)", user_id, guild_id
        )


async def get_currency(pool: Pool, user_id, guild_id):
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            "SELECT currency_zenny, currency_crystals FROM users WHERE user_id=$1 AND guild_id=$2",
            user_id,
            guild_id,
        )
        if record:
            return record["currency_zenny"], record["currency_crystals"]
        else:
            return None


async def add_zenny(pool: Pool, user_id, guild_id, amount):
    async with pool.acquire() as connection:
        await connection.execute(
            "UPDATE users SET currency_zenny = currency_zenny + $1 WHERE user_id=$2 AND guild_id=$3",
            amount,
            user_id,
            guild_id,
        )


async def add_crystals(pool: Pool, user_id, guild_id, amount):
    async with pool.acquire() as connection:
        await connection.execute(
            "UPDATE users SET currency_crystals = currency_crystals + $1 WHERE user_id=$2 AND guild_id=$3",
            amount,
            user_id,
            guild_id,
        )


async def get_gatcha_duplicate(pool: Pool, user_id, guild_id, data):
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            f"SELECT {data[1]} FROM users WHERE user_id=$1 AND guild_id=$2",
            user_id,
            guild_id,
        )
        if record[data[1]]:
            if data[0][0] in record[data[1]]:
                return True
            else:
                return False
        else:
            return False


async def add_gacha_pull(pool: Pool, user_id, guild_id, data):
    async with pool.acquire() as connection:
        await connection.execute(
            f"UPDATE users SET {data[1]} = array_append({data[1]},'{data[0][0]}') WHERE user_id=$1 AND guild_id=$2",
            user_id,
            guild_id,
        )


async def add_to_pulls(pool: Pool, user_id, guild_id):
    async with pool.acquire() as connection:
        await connection.execute(
            "UPDATE users SET pulls = pulls + 1 WHERE user_id=$1 AND guild_id=$2",
            user_id,
            guild_id,
        )


async def pull_track_checker(pool: Pool, user_id, guild_id):
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            "SELECT pull_track FROM users WHERE user_id=$1 AND guild_id=$2",
            user_id,
            guild_id,
        )
        if record["pull_track"] < 10:
            await connection.execute(
                "UPDATE users SET pull_track = pull_track + 1 WHERE user_id=$1 AND guild_id=$2",
                user_id,
                guild_id,
            )
            return False
        else:
            await connection.execute(
                "UPDATE users SET pull_track = 0 WHERE user_id=$1 AND guild_id=$2",
                user_id,
                guild_id,
            )
            return True
