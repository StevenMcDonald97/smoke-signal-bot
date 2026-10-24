# load Discord
import discord
from discord import app_commands
import asyncio

# get the bot token
TOKEN = open("token.txt").read().strip()

# define the morse code library
SHORT = "💨"
LONG = "☁️"

MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "!": "-.-.--",
}

REVERSE={}
for letter, code in MORSE.items():
    REVERSE[code] = letter

def to_smoke(text):
    lines = []
    for word in text.upper().split():
        puffs = []
        for letter in word:
            if letter in MORSE:
                code = MORSE[letter]
                puffs.append(code.replace(".", SHORT).replace("-", LONG))
        if puffs:
            lines.append(" ".join(puffs))
    return "\n".join(lines)

def from_smoke(smoke):
    long_base = LONG.replace("\ufe0f", "")  # just "☁"
    words = []
    for line in smoke.split("\n"):
        letters = []
        for puff in line.split():
            code = puff.replace("\ufe0f", "").replace(long_base, "-").replace(SHORT, ".")
            letters.append(REVERSE.get(code, "?"))
        words.append("".join(letters))
    return " ".join(words)

def smoke_card(sender, lines, finished):
    if lines:
        smoke = "\n".join(lines)
    else:
        smoke = "🔥 *Lighting the fire...*"
    
    card = discord.Embed(description=smoke, color=0x8A8F98)
    card.set_author(
        name=f"{sender.display_name} is sending smoke signals ",
        icon_url=sender.display_avatar.url,
    )

    if finished:
        card.set_footer(text="Press 🔍 Read the smoke to decode it")
    else:
        card.set_footer(text="The smoke is rising...")
    
    return card

class SmokeButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Read the smoke", emoji="🔍",
                       style=discord.ButtonStyle.secondary, custom_id="smoke:read")
    async def read(self, interaction: discord.Interaction, button: discord.ui.Button):
        card = interaction.message.embeds[0]
        decoded = from_smoke(card.description)
        await interaction.response.send_message(
            f"You squint at the sky and read: **{decoded}**",
            ephemeral=True,
        )

    @discord.ui.button(label="Reply in smoke", emoji="↩️",
                       style=discord.ButtonStyle.primary, custom_id="smoke:reply")
    async def reply(self, interaction: discord.Interaction, button: discord.ui.Button):
        original_sender = interaction.message.interaction_metadata.user
        await interaction.response.send_modal(ReplyBox(original_sender))

class ReplyBox(discord.ui.Modal, title="Reply in smoke signals"):
    reply_text = discord.ui.TextInput(
        label="Your message",
        placeholder="Meet at the big rock at dawn",
        max_length=80,
    )

    def __init__(self, friend):
        super().__init__()
        self.friend = friend

    async def on_submit(self, interaction: discord.Interaction):
        await send_smoke(interaction, self.reply_text.value, self.friend)

async def send_smoke(interaction, message, friend=None):
    smoke_text = to_smoke(message)

    if smoke_text == "":
        await interaction.response.send_message(
            "Smoke signals only work with letters, numbers and basic punctuation!",
            ephemeral=True,
        )
        return

    lines = smoke_text.split("\n")
    sender = interaction.user

    shout = None
    if friend is not None and friend.id != sender.id:
        shout = f"{friend.mention}, look to the sky! 🔥"

    await interaction.response.send_message(content=shout, embed=smoke_card(sender, [], False))

    for count in range(1, len(lines)):
        await asyncio.sleep(1)
        await interaction.edit_original_response(embed=smoke_card(sender, lines[:count], False))

    await asyncio.sleep(1)
    await interaction.edit_original_response(
        embed=smoke_card(sender, lines, True),
        view=SmokeButtons(),
    )


class SmokeBot(discord.Client):
    # initialize the events the bot listens to
    # create a command tree (i.e. the commands the bot listens to)
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    # runs once at startup: register slash commands globally
    async def setup_hook(self):
        await self.tree.sync()
        self.add_view(SmokeButtons())

    async def on_ready(self):
        print(f"{self.user} is online!")


client = SmokeBot()


# create a slash command (because message is str, Discord shows a text box)
@client.tree.command(name="smoke", description="Send a message as smoke signals")
@app_commands.describe(message="What to say", friend="A friend to signal (optional)")
async def smoke(
    interaction: discord.Interaction,
    message: app_commands.Range[str, 1, 80],
    friend: discord.Member = None,
):
    await send_smoke(interaction, message, friend)


# log in and keep the bot running
client.run(TOKEN)