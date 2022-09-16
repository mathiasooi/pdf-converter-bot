import discord
import requests
from fpdf import FPDF
import sys

class MyClient(discord.Client):
    def __init__(self, *, intents, **options) -> None:
        super().__init__(intents=intents, **options)
        self.files = 0

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message):
        if message.author.id == self.user.id: return
        if message.attachments:
            for url in message.attachments:
                with open(str(self.files) + ".jpg", 'wb') as handle:
                    response = requests.get(str(url), stream=True)
                    if not response.ok: print(response)
                    for block in response.iter_content(1024):
                        if not block: break
                        handle.write(block)
                self.files += 1
        if message.content == "merge":
            pdf = FPDF()
            for img in [str(i) + ".jpg" for i in range(self.files)]:
                pdf.add_page()
                pdf.image(img, 1, 0, 210, 297)
            pdf.output("a.pdf", "F")
            self.files = 0
            await message.reply(file=discord.File(open("a.pdf", "rb")), mention_author=True)

        

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)

client.run("MTAxOTQzOTQyNDEwMDExMDM1Nw.GeSZPp.LgR6JbFaT5JYSCYq-MIgdYVq6MWAaJ6T-ovUrA")