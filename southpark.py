#!/usr/bin/env python3.8
import time

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


def one_piece_path(dialog) -> str:
    show_name = "One Piece"
    dialog_document = dialog.media.document
    mime_type = dialog_document.mime_type
    dialog_message = dialog.message
    file_type = "." + mime_type.split("/")[1]
    if "#" in dialog_message:
        chapter = dialog_message.split(" ")[0]
    else:
        chapter = dialog_message
        if "x-matroska" in mime_type or "x-msvideo" in mime_type:
            file_type = dialog_document.attributes[0].file_name[-4:]
    file_name = chapter + file_type
    if "#" in file_name:
        file_name = "One Piece S01E" + file_name.replace("#", "").replace("Cap", "")
    if "145" in file_name:
        file_name = "One Piece S01E" + file_name.replace("Cap", "")
    file_name = file_name.replace("x-msvideo", "avi")
    if "3D" not in chapter and "Película" not in chapter:
        return os.path.join(config["Telegram"]["folder"], "Anime", "TV", show_name, file_name)


def young_sheldon_path(dialog) -> str:
    show_name = "Young Sheldon {tvdb-328724}"
    dialog_document = dialog.media.document
    mime_type = dialog_document.mime_type
    file_type = mime_type.split("/")[1]
    dialog_message = dialog.message
    if re.findall('cap|episodio', dialog_message, flags=re.IGNORECASE):
        chapter = re.findall("\d{1,2}", dialog_message)[0]
        if re.search("^Temporada", dialog_message):
            season = re.findall("\d{1,2}", dialog_message)[0]
            chapter = re.findall("\d{1,2}", dialog_message)[1]
            file_name = "Young Sheldon S0{}E{}".format(season, chapter)
        else:
            file_name = "Young Sheldon S01E{}".format(chapter)
        file_name = file_name + "." + file_type
        return os.path.join(config["Telegram"]["folder"], "TV Shows", show_name, file_name)


def palomitas_path(dialog) -> str:
    dialog_document = dialog.media.document
    mime_type = dialog_document.mime_type
    file_type = mime_type.split("/")[1]
    if hasattr(dialog_document.attributes[0], "file_name"):
        dialog_message = dialog_document.attributes[0].file_name
        show_episode_search = re.search("(\d{1,2}x\d{1,2})", dialog_message)
        if show_episode_search and "prano" not in dialog_message \
                and "gitivo" not in dialog_message \
                and "Hija" not in dialog_message:
            show_name_remove_chapter = dialog_message.replace(show_episode_search.group(), "")
            show_name = re.sub("\@.*", "", show_name_remove_chapter).strip()
            show_name = re.sub("[^a-zA-Z0-9,\s]", "", show_name)
            if "Hawaii" in show_name:
                show_name = "Hawaii Five Zero"
            if "Star Trek" in show_name:
                show_name = "Stark Trek"
            if "stacion" in show_name:
                show_name = "Estacion 19"
            if "rar" not in mime_type:
                season = re.findall("\d{1,2}", dialog_message)[0]
                chapter = re.findall("\d{1,2}", dialog_message)[1]
                file_type = file_type.replace("x-matroska", "mkv")
                file_type = file_type.replace("x-msvideo", "avi")
                file_name = fr'{show_name} S{season}E{chapter}.{file_type}'
                return os.path.join(config["Telegram"]["folder"], "TV Shows", show_name, file_name)
            else:
                return os.path.join(config["Telegram"]["folder"], "tmp", show_name, dialog_message)


async def download_media(channel_name, dialog, season, chapter):
    dialog_message_id = dialog.media.document.id
    if not already_downloaded(dialog_message_id):
        abs_path = None
        # mime_type = dialog.media.document.mime_type
        # if dialog.message != "":
        #     file_name = dialog.message + "." + mime_type.split("/")[1]
        # elif hasattr(dialog.media.document.attributes[0], "file_name"):
        #     file_name = dialog.media.document.attributes[0].file_name
        # else:
        #     file_name = "Unknown-{}-{}.{}".format(season, chapter, mime_type.split("/")[1])
        # if channel_name != "South Park" and channel_name != "One Piece":
        #     tv_show_media_mime = file_name[-4:]
        #     tv_show_with_chapter = file_name.split("@")[0]
        #     tv_show_chapter = re.match("[0-9]{1,2}(x)[0-9]{1,2}", tv_show_with_chapter).group()
        #     tv_show_name = tv_show_with_chapter.replace(tv_show_chapter, "").replace("-", "")
        #     if re.match("^[0-9]", tv_show_name):
        #         tv_show_name = " ".join(tv_show_name.split(" ")[1:])
        #     abs_path = os.path.join(config["Telegram"]["folder"], "TV Shows", tv_show_name.strip(),
        #                             tv_show_chapter.strip() + tv_show_media_mime)
        # else:
        #     abs_path = os.path.join(config["Telegram"]["folder"], "TV Shows", channel_name, file_name)
        if "ZUBY" in channel_name:
            abs_path = palomitas_path(dialog)
        if channel_name == "One Piece":
            abs_path = one_piece_path(dialog)
        if "El joven" in channel_name:
            abs_path = young_sheldon_path(dialog)
        if abs_path:
            path_to_file = Path(abs_path)
            if not os.path.exists(path_to_file.parent.parent):
                os.mkdir(path_to_file.parent.parent)
            if not os.path.exists(path_to_file.parent):
                os.mkdir(path_to_file.parent)
            logging.info("[DEBUG] DOWNLOADING {}".format(str(path_to_file)))
            global file
            file = path_to_file
            if "prod" in config["Telegram"]["env"] or "local" not in config["Telegram"]["env"]:
                await dialog.download_media(path_to_file, progress_callback=progress)
            logging.info("[DEBUG] FINISHED {}".format(str(path_to_file)))
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
        logging.info("[DEBUG] downloads.txt not found")
        pass
    return result


def bot():
    with client:
        client.loop.run_until_complete(main())

    client.start()
    client.run_until_disconnected()


logging.basicConfig(level=logging.INFO, filename='info.log')

if __name__ == "__main__":
    bot()
