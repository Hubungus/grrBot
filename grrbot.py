import os
import io
import logging

from dotenv import load_dotenv
import discord
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import imageio

# ─── Umgebungsvariablen laden (.env) ─────────────────────────────────────
load_dotenv()
TOKEN    = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1399423266392772719  # Deine echte Server‑ID hier

# ─── Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)

# ─── Discord Client Setup ────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True  # Damit on_message() den Inhalt sieht
client = discord.Client(intents=intents)
tree   = app_commands.CommandTree(client)

# ─── Hilfsfunktion: Maximal passende Schriftgröße ermitteln ─────────────
def find_max_font_size(text, max_width, max_height, font_path="arial.ttf", max_font_size=200):
    min_size = 1
    best_font = ImageFont.truetype(font_path, min_size)
    while min_size <= max_font_size:
        mid_size = (min_size + max_font_size) // 2
        font = ImageFont.truetype(font_path, mid_size)
        dummy = Image.new("RGB", (1,1))
        draw  = ImageDraw.Draw(dummy)
        bbox  = draw.textbbox((0,0), text, font=font)
        w, h  = bbox[2]-bbox[0], bbox[3]-bbox[1]
        if w <= max_width and h <= max_height:
            best_font = font
            min_size  = mid_size + 1
        else:
            max_font_size = mid_size - 1
    return best_font

# ─── Slash-Command /grr ──────────────────────────────────────────────────
@tree.command(name="grr", description="Erstellt ein wütendes GIF mit deinem Text oben")
@app_commands.describe(text="Text, der über dem GIF angezeigt werden soll")
async def grr(interaction: discord.Interaction, text: str):
    logging.info(f"🔔 /grr Slash-Command von {interaction.user} in {interaction.channel}")
    try:
        await interaction.response.defer()
    except discord.NotFound:
        logging.warning("❌ Interaktion abgelaufen beim defer.")
        return

    gif_path     = "grr.gif"
    scale_factor = 3
    extra_height = 200
    padding      = 30

    if not os.path.isfile(gif_path):
        await interaction.followup.send("🚫 Die GIF-Datei wurde nicht gefunden.")
        return

    try:
        reader = imageio.get_reader(gif_path)
    except Exception as e:
        logging.error(f"Fehler beim Laden der GIF-Datei: {e}")
        await interaction.followup.send("🚫 Fehler beim Lesen der GIF-Datei.")
        return

    frames = []
    for frame in reader:
        img = Image.fromarray(frame).convert("RGBA")
        w, h = img.size
        img = img.resize((w*scale_factor, h*scale_factor), resample=Image.LANCZOS)

        new_w = img.width
        new_h = img.height + extra_height
        canvas = Image.new("RGBA", (new_w, new_h), (255,255,255,255))
        canvas.paste(img, (0, extra_height))

        font = find_max_font_size(text, new_w-2*padding, extra_height-2*padding)
        draw = ImageDraw.Draw(canvas)
        bbox = draw.textbbox((0,0), text, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x = (new_w - tw)/2 - bbox[0]
        y = (extra_height - th)/2 - bbox[1]
        draw.text((x,y), text, font=font, fill="black")

        frames.append(canvas)

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

    # GIF senden
    await interaction.followup.send(file=discord.File(fp=buf, filename="grr.gif"))

# ─── Nachrichten-Events inkl. Prefix-Befehle ─────────────────────────────
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    logging.info(f"📩 Nachricht von {message.author} in #{message.channel}: {message.content}")

    # !ping
    if message.content.lower().startswith("!ping"):
        await message.channel.send("🏓 Ich bin da!")
        return

    # !debug
    if message.content.lower().startswith("!debug"):
        await message.channel.send(f"🛠 Ich sehe deine Nachricht: `{message.content}`")
        return

    # !grr Prefix-Befehl
    if message.content.lower().startswith("!grr "):
        text = message.content[5:].strip()
        if not text:
            return await message.channel.send("❓ Bitte gib mir einen Text: `!grr Dein Text`")

        logging.info(f"🔔 !grr Prefix-Command von {message.author} in {message.channel}")

        # Typing-Indicator
        async with message.channel.typing():
            gif_path     = "grr.gif"
            scale_factor = 3
            extra_height = 200
            padding      = 30

            if not os.path.isfile(gif_path):
                await message.channel.send("🚫 Die GIF-Datei wurde nicht gefunden.")
                return

            try:
                reader = imageio.get_reader(gif_path)
            except Exception as e:
                logging.error(f"Fehler beim Laden der GIF-Datei: {e}")
                await message.channel.send("🚫 Fehler beim Lesen der GIF-Datei.")
                return

            frames = []
            for frame in reader:
                img = Image.fromarray(frame).convert("RGBA")
                w, h = img.size
                img = img.resize((w*scale_factor, h*scale_factor), resample=Image.LANCZOS)

                new_w = img.width
                new_h = img.height + extra_height
                canvas = Image.new("RGBA", (new_w, new_h), (255,255,255,255))
                canvas.paste(img, (0, extra_height))

                font = find_max_font_size(text, new_w-2*padding, extra_height-2*padding)
                draw = ImageDraw.Draw(canvas)
                bbox = draw.textbbox((0,0), text, font=font)
                tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
                x = (new_w - tw)/2 - bbox[0]
                y = (extra_height - th)/2 - bbox[1]
                draw.text((x,y), text, font=font, fill="black")
                frames.append(canvas)

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

            # GIF senden
            await message.channel.send(file=discord.File(fp=buf, filename="grr.gif"))

        # **Nachricht des Users löschen**
        try:
            await message.delete()
        except discord.Forbidden:
            logging.warning("Bot hat keine Rechte, Nachrichten zu löschen!")
        return

# ─── Bot-Startup ─────────────────────────────────────────────────────────
@client.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)

        # Lokale Guild-Synchronisierung für Slash-Commands
        synced_guild  = await tree.sync(guild=guild)
        logging.info(f"✅ {len(synced_guild)} Slash-Commands für Guild {GUILD_ID} synchronisiert.")

        # Globale Synchronisierung (optional)
        synced_global = await tree.sync()
        logging.info(f"🌍 {len(synced_global)} globale Slash-Commands synchronisiert.")

    except Exception as e:
        logging.error(f"❌ Fehler beim Synchronisieren: {e}")

    logging.info(f"🤖 Bot eingeloggt als {client.user} (ID: {client.user.id})")

# ─── Bot starten ─────────────────────────────────────────────────────────
client.run(TOKEN)
