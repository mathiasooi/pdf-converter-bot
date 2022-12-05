import discord
import requests
import sqlite3
import PIL.Image as Image
import io
import json

class MyClient(discord.Client):
    def __init__(self, *, intents, **options) -> None:
        super().__init__(intents=intents, **options)
        self.db = "data.db"
        self.con = sqlite3.connect(self.db)
        self.cur = self.con.cursor()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def on_message(self, message):
        userid = message.author.id
        if userid == self.user.id: return

        if message.attachments:
            self.insert_data(userid, message.attachments)
            
        if message.content == "merge":
            await self.create_send(userid, message)

        if message.content == "clear":
            self.reset_data(userid)
            await message.reply("Your images have been cleared", mention_author=True)

    async def create_send(self, userid, message):
        """Merges user images into a pdf and sends a pdf file"""
        with self.read_data(userid) as pdf:
            if pdf.getbuffer().nbytes:
                await message.reply(file=discord.File(pdf, filename="a.pdf"), mention_author=True)
            else:
                await message.reply("No images were found", mention_author=True)
        self.reset_data(userid)

    def insert_data(self, userid, attachments):
        """Inserts user images into an sqlite database"""
        self.cur.execute("CREATE TABLE IF NOT EXISTS images (image, id)")
        
        for url in attachments:
            handle = bytearray()
            response = requests.get(str(url), stream=True)
            if not response.ok: print(response)
            for block in response.iter_content(1024):
                if not block: break
                handle.extend(block)
            self.cur.execute("INSERT INTO images (image, id) VALUES (?, ?)", (handle, userid))
            self.con.commit()

    def read_data(self, userid):
        """Reads and merges all iamges where id = userid in sqlite table"""
        self.cur.execute("SELECT image FROM images WHERE id = ?", (userid, ))

        images = []
        for img, in self.cur.fetchall():
            img = Image.open(io.BytesIO(img))
            img.load()
            bkg = Image.new("RGB", img.size, (255, 255, 255))
            bkg.paste(img)
            images.append(bkg)
        
        if not images: return io.BytesIO()

        output = io.BytesIO()
        images[0].save(output, "PDF", resolution=100.0, save_all=True, append_images=images[1:])
        output.seek(0)
        return output

    def reset_data(self, userid):
        """Deletes all rows in sqlite table where id = userid"""
        self.cur.execute("DELETE FROM images WHERE id=?", (userid, ))
        self.con.commit()

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)

with open("config.json") as f:
    config = json.load(f)

client.run(config["APP"]["TOKEN"])