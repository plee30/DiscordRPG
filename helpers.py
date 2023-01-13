import sqlite3, discord
# <!--- Repeated functions here ---!> #

conn = sqlite3.connect("game.db")
cursor = conn.cursor()

# Checks if a user's character does not exist
# Returns True if the character exists
# Returns False if the character does not exist
def character_existence_check(ctx, title: str, description: str):
    # Check if the user has a character
    cursor.execute("SELECT * FROM characters WHERE user_id = ?",
                   (ctx.author.id,))
    curCursor = cursor.fetchone()
    embed = discord.Embed(
        title = title,
        description= description,
        color=discord.Color.red()
    )
    embed.set_author(
        name=ctx.author.display_name,
        icon_url=ctx.author.display_avatar.url
    )
    if curCursor is None:
        return (False, embed, curCursor)
    else:
        return (True, embed, curCursor)

def get_avatar_url(user_id):
    cursor.execute("SELECT * FROM avatars WHERE user_id = ?", 
                   (user_id,))
    user = cursor.fetchone()
    return user[1]
    
def add_sender_as_author(ctx, embed):
    embed.set_author(
        name=ctx.author.display_name,
        icon_url=ctx.author.display_avatar.url
    )