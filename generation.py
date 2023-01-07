import random

# # Define a list of enemy names to choose from
# enemy_names = ["goblin", "orc", "troll", "zombie"]

# Define a function to generate player character
def generate_char(char_name):
    # Generate character stats
    health = random.randint(50, 100)
    strength = random.randint(5, 10)
    
    # Create a dictionary to represent the enemy
    char = {"name": char_name, "max_health": health, "health": health, "strength": strength}
    
    return char


# Define a function to generate enemies
def generate_enemy(enemy_name):
    # Generate enemy stats
    health = random.randint(50, 75)
    strength = random.randint(3, 8)
    
    # Create a dictionary to represent the enemy
    enemy = {"name": enemy_name, "health": health, "strength": strength}
    
    return enemy
