#!/usr/bin/env python3.8
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
import configparser
import re
import os
from pathlib import Path
import logging

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


def bytes_to(bytes, to, bsize=1024):
    a = {'k': 1, 'm': 2, 'g': 3, 't': 4, 'p': 5, 'e': 6}
    return format(bytes / (bsize ** a[to]), ".2f")


def progress(current, total):
    global file
    current_m = bytes_to(current, "m")
    total_b = bytes_to(total, "m")
    path = "/".join(str(file).split("/")[-3:])
    logging.info("Download total: {}% {} mb/{} mb {}"
                 .format(int((current / total) * 100), current_m, total_b, path))


async def main():
    counter_season = 30
    for channel in channels_videos:
        counter = 1
        peer_channel = PeerChannel(int("-{}".format(channel)))
        entity = await client.get_entity(peer_channel)
        channel_name = " ".join(entity.title.split(" ")[:2])
        async for dialog in client.iter_messages(entity=peer_channel):
            if dialog.media \
                    and not hasattr(dialog.media, "photo") \
                    and not hasattr(dialog.media, "webpage"):
                if re.search("video", dialog.media.document.mime_type) or \
                        re.search(".rar", dialog.media.document.mime_type):
                    await download_media(channel_name, dialog, counter_season, counter)
            counter += 1
        counter_season += 1
    exit()


async def download_media(channel_name, dialog, season, chapter):
    dialog_message_id = dialog.media.document.id
    if not already_downloaded(dialog_message_id):

        mime_type = dialog.media.document.mime_type
        if dialog.message != "":
            file_name = dialog.message + "." + mime_type.split("/")[1]
        elif hasattr(dialog.media.document.attributes[0], "file_name"):
            file_name = dialog.media.document.attributes[0].file_name
        else:
            file_name = "Unknown-{}-{}.{}".format(season, chapter, mime_type.split("/")[1])
        if channel_name != "South Park" and channel_name != "One Piece":
            tv_show_media_mime = file_name[-4:]
            tv_show_with_chapter = file_name.split("@")[0]
            tv_show_chapter = re.match("[0-9]{1,2}(x)[0-9]{1,2}", tv_show_with_chapter).group()
            tv_show_name = tv_show_with_chapter.replace(tv_show_chapter, "").replace("-", "")
            if re.match("^[0-9]", tv_show_name):
                tv_show_name = " ".join(tv_show_name.split(" ")[1:])
            abs_path = os.path.join(config["Telegram"]["folder"], "TV Shows", tv_show_name.strip(),
                                    tv_show_chapter.strip() + tv_show_media_mime)
        elif channel_name == "One Piece":
            tv_show_media_mime = file_name[-4:]
            tv_show_chapter = file_name.split(" ")[0].replace("#", "")
            tv_show_name = channel_name
            abs_path = os.path.join(config["Telegram"]["folder"], "TV Shows", tv_show_name.strip(),
                                    tv_show_chapter.strip() + tv_show_media_mime)
        else:
            abs_path = os.path.join(config["Telegram"]["folder"], "TV Shows", channel_name, file_name)
        path_to_file = Path(abs_path)
        if not os.path.exists(path_to_file.parent.parent):
            os.mkdir(path_to_file.parent.parent)
        if not os.path.exists(path_to_file.parent):
            os.mkdir(path_to_file.parent)
        logging.info("DOWNLOADING {}".format(str(path_to_file)))
        global file
        file = path_to_file
        await dialog.download_media(path_to_file, progress_callback=progress)
        logging.info("FINISHED {}".format(str(path_to_file)))
        with open("downloads.txt", "a") as file:
            file.write(str(dialog_message_id) + " " + str(path_to_file))
            file.write("\n")


def already_downloaded(media_id):
    result = False
    try:
        with open("downloads.txt", "r") as temp_file:
            data_file = temp_file.readlines()
            for line in data_file:
                if str(media_id) in line:
                    result = True
    except:
        logging.info("Downloads.txt not found")
        pass
    return result


def bot():
    with client:
        client.loop.run_until_complete(main())

    client.start()
    client.run_until_disconnected()


logging.basicConfig(level=logging.DEBUG)
if __name__ == "__main__":
    bot()
