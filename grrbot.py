import discord
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import imageio
import io
import json
import logging
from dotenv import load_dotenv
import os


load_dotenv()                                      # .env laden

TOKEN   = os.getenv("DISCORD_TOKEN")               # Bot‑Token
APP_ID  = os.getenv("DISCORD_APP_ID")   

# 📃 Logging konfigurieren
logging.basicConfig(level=logging.INFO)

# 🎛 Intents & Client
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# 🔠 Beste passende Schriftgröße finden
def find_max_font_size(text, max_width, max_height, font_path="arial.ttf", max_font_size=200):
    min_size = 1
    best_font = ImageFont.truetype(font_path, min_size)

    while min_size <= max_font_size:
        mid_size = (min_size + max_font_size) // 2
        font = ImageFont.truetype(font_path, mid_size)
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

        if text_w <= max_width and text_h <= max_height:
            best_font = font
            min_size = mid_size + 1
        else:
            max_font_size = mid_size - 1

    return best_font

# 🖼️ Slash-Befehl /grr (funktioniert überall – Server UND DMs)
@tree.command(name="grr", description="Erstellt ein wütendes GIF mit deinem Text oben")
@app_commands.describe(text="Text, der über dem GIF angezeigt werden soll")
async def grr(interaction: discord.Interaction, text: str):
    await interaction.response.defer()

    # 🌐 Logging für DM oder Server
    if isinstance(interaction.channel, discord.DMChannel):
        logging.info(f"📬 Befehl aus DM von {interaction.user}")
    else:
        logging.info(f"🌐 Befehl aus Server '{interaction.guild.name}' von {interaction.user}")

    gif_path = "grr.gif"
    scale_factor = 3
    extra_height = 200
    padding = 30

    try:
        reader = imageio.get_reader(gif_path)
    except FileNotFoundError:
        await interaction.followup.send("🚫 Die GIF-Datei wurde nicht gefunden.")
        return

    frames = []

    for frame in reader:
        image = Image.fromarray(frame).convert("RGBA")
        w, h = image.size

        image = image.resize((w * scale_factor, h * scale_factor), resample=Image.LANCZOS)
        new_width = image.width
        new_height = image.height + extra_height

        new_image = Image.new("RGBA", (new_width, new_height), (255, 255, 255, 255))
        new_image.paste(image, (0, extra_height))

        font = find_max_font_size(text, new_width - 2 * padding, extra_height - 2 * padding)
        draw = ImageDraw.Draw(new_image)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

        text_x = (new_width - text_w) / 2 - bbox[0]
        text_y = (extra_height - text_h) / 2 - bbox[1]

        draw.text((text_x, text_y), text, font=font, fill="black")
        frames.append(new_image)

    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=reader.get_meta_data().get("duration", 100),
        loop=0
    )
    buf.seek(0)

    await interaction.followup.send(file=discord.File(fp=buf, filename="grr.gif"))

@client.event
async def on_ready():
    try:
        synced = await tree.sync()
        logging.info(f"✅ {len(synced)} Slash-Befehle global synchronisiert.")
        logging.info("🌍 Registrierte Slash-Befehle:")
        for cmd in synced:
            logging.info(f"  └─ /{cmd.name} – {cmd.description}")
    except Exception as e:
        logging.error(f"❌ Fehler bei der Befehlssynchronisation: {e}")

    logging.info(f"🤖 Bot eingeloggt als {client.user} (ID: {client.user.id})")

    # Optional: Test-DM senden
    try:
        user = await client.fetch_user(1399336288133320754)
        await user.send("✅ Testnachricht: Der Bot kann DMs senden!")
    except Exception as e:
        logging.warning(f"⚠️ Konnte keine DM senden: {e}")

# 🚀 Start
client.run(TOKEN)
