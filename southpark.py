from telethon import TelegramClient, events
from telethon.tl.types import PeerChat, PeerUser, PeerChannel
import configparser
import re
import os
from pathlib import Path

config = configparser.ConfigParser()
config.read("config.ini")

api_id = int(config['Telegram']['api_id'])
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

client = TelegramClient('anon', api_id, api_hash)

channels_videos = config["Telegram"]["channels"].split(" ")
bot_name = config["Telegram"]["botname"]


# # Escuchar los nuevos mensajes
# @client.on(events.NewMessage())
# async def messages(event):
#     peer_id = event.peer_id
#     for channel_id in channels_videos:
#         chanel_id = PeerChannel(int(channel_id))
#         if chanel_id == peer_id:
#             message = event.message
#             if message.media:
#                 await client.send_file(bot_name, message.media)
#             else:
#                 await client.send_message(bot_name, message.text)


async def get_chats_data():
    async for dialog in client.iter_dialogs():
        print(dialog.name, ' HAS ID ', dialog.id)


async def main():
    counter = 0
    for channel in channels_videos:
        counter += 1
        peer_channel = PeerChannel(int("-{}".format(channel)))
        async for dialog in client.iter_messages(entity=peer_channel):
            entity = await client.get_entity(peer_channel)
            channel_name = " ".join(entity.title.split(" ")[:2])
            if dialog.media:
                if re.search("mp4", dialog.media.document.mime_type):
                    if hasattr(dialog.media.document.attributes[0], 'file_name'):
                        dialog_file_name = dialog.media.document.attributes[0].file_name
                        await download_media(channel_name, dialog, dialog_file_name)
                    else:
                        dialog_file_name = channel_name.replace(" ", "") + "-unknown-" + str(counter) + ".mp4"
                        await download_media(channel_name, dialog, dialog_file_name)
            counter += 1
    exit()


async def download_media(channel_name, dialog, dialog_file_name):
    abs_path = os.path.join(Path.cwd(), channel_name, dialog_file_name)
    path_to_file = Path(abs_path)
    if not os.path.exists(path_to_file.parent):
        os.mkdir(channel_name)
    await dialog.download_media(path_to_file)


with client:
    client.loop.run_until_complete(main())

client.start()
client.run_until_disconnected()
