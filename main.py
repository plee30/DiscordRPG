import discord
import os
import requests
import sqlite3
import random
from dotenv import load_dotenv
import generation
import helpers

load_dotenv()
TOKEN = os.getenv('botDISCORD_TOKEN')

conn = sqlite3.connect("game.db")
cursor = conn.cursor()

# Creates tables to store data
# Avatar table
cursor.execute(
    """CREATE TABLE IF NOT EXISTS avatars (
        user TEXT NOT NULL, 
        photo BLOB NOT NULL
    )""")
# Character table
# 0 = id
# 1 = user_id
# 2 = character_name
# 3 = max_health
# 4 = health
# 5 = strength
cursor.execute(
    """CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY,
        user_id TEXT,
        character_name TEXT,
        max_health INTEGER,
        health INTEGER,
        strength INTEGER
    )""")
# Enemy table
cursor.execute(
    """CREATE TABLE IF NOT EXISTS enemies (
        id INTEGER PRIMARY KEY, 
        user_id TEXT, 
        enemy_name TEXT, 
        health INTEGER, 
        strength INTEGER
    )""")
# Currency Table
cursor.execute(
    """CREATE TABLE IF NOT EXISTS balance (
        id INTEGER PRIMARY KEY, 
        user_id TEXT, 
        bal INTEGER
    )""")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot()

currency_name = "gold"

##### Bot functions ######


# Confirms bot is running
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

##### Admin Commands #####
admin_commands = bot.create_group("admin", "Edit user & game config")

# /setbal command
# Define a command to set the balance of a user
@admin_commands.command(description="Sets balance of a user", pass_context=True)
async def setbal(ctx, member: discord.User, amount: int):
    # If the user has permission
    if ctx.author.guild_permissions.administrator:
        # Initalizes the user's balance if they have not yet been initalized
        cursor.execute("SELECT * FROM balance WHERE user_id = ?",
                       (member.id,))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO balance (user_id, bal) VALUES (?, ?)", (
                    member.id,
                    amount
                )
            )
            conn.commit()
        # Updates the user's balance
        cursor.execute(
            "UPDATE balance SET bal = ? WHERE user_id = ?", (
                amount, 
                member.id
            )
        )
        conn.commit()
        embed = discord.Embed(
            title="Balance Set",
            description=f"{member.name}'s balance has been set to {amount}!",
            color=discord.Color.green()
        )
        helpers.add_sender_as_author(ctx, embed)
        await ctx.respond(embed=embed)
    # Sends an error if the user does not have permission
    else:
        embed = discord.Embed(
            title="Balance Set Error",
            description="You do not have permission to do this!",
            color=discord.Color.red()
        )
        helpers.add_sender_as_author(ctx, embed)
        await ctx.respond(embed=embed)


##### User Commands #####
### Test Commands ###
# /hello command
# Test Hello command
@bot.command()
async def hello(ctx):
    await ctx.respond("Hello!")

### Character Stuffs ###
# /create command
# Define a command to create a new character


@bot.command(description="Create a new character!")
async def create(ctx, *, character_name: str):
    # Check if the user already has a character, if they do, displays an error
    existCheck = helpers.character_existence_check(
        ctx,
        "Character Creation Error",
        "You already have a character. Use /delete to delete your current character, or /stats to check the stats of your current character!"
    )
    if (existCheck[0] is True):
        await ctx.respond(embed=existCheck[1])
        return
    # Create a new character for the user
    char = generation.generate_char(character_name)
    cursor.execute(
        "INSERT INTO characters (user_id, character_name, max_health, health, strength) VALUES (?, ?, ?, ?, ?)", (
            ctx.author.id,
            char['name'],
            char['max_health'],
            char['health'],
            char['strength']
        )
    )
    conn.commit()
    # Initalize balance of a user if it has not been initalized already
    cursor.execute("SELECT * FROM balance WHERE user_id = ?",
                   (ctx.author.id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO balance (user_id, bal) VALUES (?, ?)", (
                ctx.author.id,
                0
            )
        )
        conn.commit()
    # Send a message to the user to confirm that the character has been created
    embed = discord.Embed(
        title="Character Created",
        description=f"Your character {char['name']} has been created!",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Health",
        value=f"{char['health']}",
        inline=True
    )
    embed.add_field(
        name="Strength",
        value=f"{char['strength']}",
        inline=True
    )
    helpers.add_sender_as_author(ctx, embed)
    await ctx.respond(embed=embed)

# /delete command
# Define a command to delete a character


@bot.command(description="Delete your character!")
async def delete(ctx):
    # Check if the user has a character, if they do not, displays an error
    existCheck = helpers.character_existence_check(
        ctx,
        "Character Deletion Error",
        "You don't have a character. Use /create to create a new character."
    )
    if (existCheck[0] is False):
        await ctx.respond(embed=existCheck[1])
        return
    # Delete the character for the user
    cursor.execute("DELETE FROM characters WHERE user_id = ?",
                   (ctx.author.id,))
    conn.commit()
    # Send a message to the user to confirm that the character has been deleted
    embed = discord.Embed(
        title="Character Deleted",
        description="Your character has been deleted.",
        color=discord.Color.green()
    )
    helpers.add_sender_as_author(ctx, embed)
    await ctx.respond(embed=embed)

# /stats command
# Define a command to check a player character's stats


@bot.command(description="Check your stats!")
async def stats(ctx):
    # Check if the user has a character, if they do not, displays an error
    existCheck = helpers.character_existence_check(
        ctx,
        "Character Stat Error",
        "You don't have a character. Use /create to create a new character."
    )
    if (existCheck[0] is False):
        await ctx.respond(embed=existCheck[1])
        return
    # If user has a character, show it's stats
    character = existCheck[2]
    embed = discord.Embed(
        # TODO Change index so it can work as a dictionary
        title=f"{character[2]}'s Stats",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Health",
        value=f"{character[4]}",
        inline=True
    )
    embed.add_field(
        name="Strength",
        value=f"{character[5]}",
        inline=True
    )
    await ctx.respond(embed=embed)


### Currency Stuffs ###
# /balance command
# Define a command to check a user's balance
@bot.command(description="Check a user's balance!", pass_context=True)
async def balance(ctx, member: discord.User = None):
    # If optional user argument is not passed, use the author as the user
    if member is None:
        member = ctx.author
    cursor.execute("SELECT * FROM balance WHERE user_id = ?",
                   (member.id,))
    user = cursor.fetchone()
    if user is None:
        embed = discord.Embed(
            title="Balance Error",
            description=f"{member.display_name} has never created a character and does not have a balance!",
            color=discord.Color.red()
        )
        helpers.add_sender_as_author(ctx, embed)
        await ctx.respond(embed=embed)
    else:
        embed = discord.Embed(
            title="Balance",
            description=f"{member.name}'s balance is {user[2]}!",
            color=discord.Color.green()
        )
        helpers.add_sender_as_author(ctx, embed)
        await ctx.respond(embed=embed)

# /give command
# Define a command to let the user give currency to another user


@bot.command(description=f"Give a player some {currency_name}!")
async def give(ctx, member: discord.User, amount: int):
    amount = abs(amount)
    # Checks if the giver & receiver have balances
    cursor.execute("SELECT * FROM balance where user_id = ?",
                   (ctx.author.id,))
    giver = cursor.fetchone()
    cursor.execute("SELECT * FROM balance where user_id = ?",
                   (member.id,))
    receiver = cursor.fetchone()
    if giver is None:
        embed = discord.Embed(
            title="Give Error",
            description=f"You do not have a balance! Create a character first with /create!",
            color=discord.Color.red()
        )
        helpers.add_sender_as_author(ctx, embed)
        await ctx.respond(embed=embed)
        return
    if receiver is None:
        embed = discord.Embed(
            title="Give Error",
            description=f"{member.display_name} does not have a balance! Create a character first with /create!",
            color=discord.Color.red()
        )
        helpers.add_sender_as_author(ctx, embed)
        await ctx.respond(embed=embed)
        return
    # Checks if the giver has enough currency
    if giver[2] < amount:
        embed = discord.Embed(
            title="Give Error",
            description=f"You have insufficient balance!",
            color=discord.Color.red()
        )
        helpers.add_sender_as_author(ctx, embed)
        await ctx.respond(embed=embed)
        return
    # Gives currency from the giver to the receiver
    cursor.execute(
        "UPDATE balance SET bal = bal - ? WHERE user_id = ?", (
            amount,
            ctx.author.id
        )
    )
    conn.commit()
    cursor.execute(
        "UPDATE balance SET bal = bal + ? where user_id = ?", (
            amount,
            member.id
        )
    )
    conn.commit()
    embed = discord.Embed(
        title="Giving Succeeded",
        description=f"You gave {amount} {currency_name} to {member.display_name}!",
        color=discord.Color.green()
    )
    helpers.add_sender_as_author(ctx, embed)
    await ctx.respond(embed=embed)


### Actions ###
# /attack command
# Define a command to attack (and for now generate) an enemy
@bot.command(description="Fight an enemy!")
async def attack(ctx, *, enemy_name: str):
    # Check if the user has a character, if they do not, displays an error
    existCheck = helpers.character_existence_check(
        ctx,
        "Attack Error",
        "You don't have a character. Use /create to create a new character."
    )
    if (existCheck[0] is False):
        await ctx.respond(embed=existCheck[1])
        return
    # Check if user already has an enemy
    cursor.execute("SELECT * FROM enemies WHERE user_id = ?",
                   (ctx.author.id,))
    enemyTuple = cursor.fetchone()
    # If the enemy should be defeated, but still exists in the table, remove them
    if enemyTuple is not None:
        if enemyTuple[3] <= 0:
            cursor.execute(
                "DELETE FROM enemies WHERE user_id = ?", (ctx.author.id,))
            conn.commit()
            enemyTuple = None
    # If not, generate one
    else:
        # Generates an enemy
        enemyGeneration = generation.generate_enemy(enemy_name)
        cursor.execute("INSERT INTO enemies (user_id, enemy_name, health, strength) VALUES (?, ?, ?, ?)",
                       (ctx.author.id, enemyGeneration['name'], enemyGeneration['health'], enemyGeneration['strength']))
        conn.commit()
        cursor.execute(
            "SELECT * FROM enemies WHERE user_id = ?", (ctx.author.id,))
        enemyTuple = cursor.fetchone()
    # Converts character and enemy from tuples to lists
    character = list(existCheck[2])
    enemy = list(enemyTuple)
    # Fight loop
    # Fight continues until one of the fighters falls to 0 HP
    # Start the fight
    embed = discord.Embed(
        title=f"Battle: {character[2]} versus {enemy[2]}",
        color=discord.Color.blue()
    )
    helpers.add_sender_as_author(ctx, embed)
    fightMessage = await ctx.send(embed=embed)
    # Fight Loop
    while character[4] > 0 and enemy[3] > 0:
        # Player attacks enemy
        charDamage = random.randint(3, 6) * character[5]
        enemy[3] -= charDamage
        cursor.execute(
            "UPDATE enemies SET health = ? WHERE user_id = ?", (enemy[3], ctx.author.id,))
        conn.commit()
        embed.add_field(
            name=f"{character[2]}",
            value=f"{character[2]} deals {charDamage} damage to {enemy[2]}!",
            inline=False
        )
        await fightMessage.edit(embed=embed)

        # Check if the enemy is defeated
        if enemy[3] <= 0:
            cursor.execute(
                "DELETE FROM enemies WHERE user_id = ?", (ctx.author.id,))
            conn.commit()
            embed.add_field(
                name="Result",
                value=f"🥳 {character[2]} defeats {enemy[2]}!",
                inline=False
            )
            await fightMessage.edit(embed=embed)
            break
        # Enemy attacks player
        enemyDamage = random.randint(1, 3) * enemy[4]
        character[4] -= enemyDamage
        cursor.execute("UPDATE characters SET health = ? WHERE user_id = ?",
                       (character[4], ctx.author.id,))
        conn.commit()
        embed.add_field(
            name=f"{enemy[2]}",
            value=f"{enemy[2]} deals {enemyDamage} damage to {character[2]}!",
            inline=False
        )
        await fightMessage.edit(embed=embed)
        # Check if the player is defeated
        if character[4] <= 0:
            cursor.execute(
                "DELETE FROM enemies WHERE user_id = ?", (ctx.author.id,))
            conn.commit()
            cursor.execute(
                "DELETE FROM characters WHERE user_id = ?", (ctx.author.id,))
            conn.commit()
            embed.add_field(
                name="Result",
                value=f"{character[2]} defeats {enemy[2]}!",
                inline=False
            )
            embed.add_field(
                name="DEATH",
                value=f"{character[2]} has died! Create a new character with /create!",
                inline=False
            )
            await fightMessage.edit(embed=embed)
            break

# /rest command
# Define a command to restore a character's stats
@bot.command(description="Restores your character's stats!")
async def rest(ctx):
    # Checks if the user has a character, if they do not, displays an error
    existCheck = helpers.character_existence_check(
        ctx,
        "Rest Error!",
        "You don't have a character. Use /create to create a new character!"
    )
    if (existCheck[0] is False):
        await ctx.respond(embed=existCheck[1])
        return

    # Restores character health to its max_health
    character = existCheck[2]
    cursor.execute(
        "UPDATE characters SET health = max_health WHERE user_id = ?", (
            ctx.author.id
        )
    )
    conn.commit()

    embed = discord.Embed(
        title=f"{character[2]} Rested Succesfully!",
        color=discord.Color.green()
        # TODO insert rest of the information
    )


# TODO /avatar:
# Create /avatar command that allows users to upload an image or insert a URL to an image,
# stores the image in a SQLite3 table, and confirms the image has been uploaded
# & sends the image in the text channel.
# Define a command that allows users to upload an avatar
# @bot.command(description="Sets your character's avatar.")
# async def avatar(ctx, url: str):
#     userId = ctx.author.id
#     avatarFileName = "avatar_" + str(userId) + ".jpg"
#     # Download the avatar image
#     response = requests.get(url)
#     # Check the size of the image
#     if len(response.content) > 1024 * 1024:  # 1MB
#         # The image is too large
#         await ctx.send("The image is too large. Please upload an image less than 1MB.")
#     else:
#         # # Save the avatar image to a file
#         # open(avatarFileName, "wb").write(response.content)
#         # Open the image file in binary mode
#         with open(avatarFileName, "rb") as f:
#             # Read the file content
#             photoData = f.read()
#         # Insert the image into the table
#         cursor.execute("INSERT INTO avatars VALUES (?, ?)", (userId, photoData))
#         conn.commit()

#     # Send a message to the user to confirm that their avatar has been changed
#     await ctx.send("Your avatar has been changed.")

bot.run(TOKEN)
