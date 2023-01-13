# Std Lib Imports
import asyncio
import re
import os
import tempfile
import bz2
from zipfile import ZipFile

# 3rd Party Imports
from bs4 import BeautifulSoup
import requests
import httpx

feature_page = requests.get("https://tf2maps.net/downloads/featured")

print("hello")
with open("mapcycle.txt", "w") as f:
    f.write("Starting Mapcycle File.\n")

with open("errors.txt", "w") as f:
    f.write("Starting Error Log.\n")

async def main():
    featured_soup = BeautifulSoup(feature_page.content, 'html.parser')
    
    for a in featured_soup.find_all('a', "avatar--s", href=True):
        link = a['href']
        if re.match("^\/(downloads)\/[a-z]", link):
            #download page
            download_page = "https://tf2maps.net" + link

            #download page soup
            download_soup = BeautifulSoup(requests.get(download_page).content, 'html.parser')
            #external download check
            try:
                href = download_soup.select(".button--icon--download")[0].get("href")
            except:
                with open("errors.txt", "a") as f:
                    title = download_soup.select(".p-title-value")[0].text.strip()
                    download_link = download_soup.select(".button--icon--redirect")[0].get("href")
                    f.write("External download for: " + str(title.rstrip()) + "\n")

            #download the file to /maps/

            try:
                filename = await get_download_filename("https://tf2maps.net" + href)
                filepath = str(os.getcwd()) + "/maps/" + str(filename)

                maps = ['arena_', 'cp_', 'ctf_', 'koth_', 'pass_', 'pd_', 'pl_', 'plr_', 'sd_']

                #filter for mvm maps
                if filename.startswith(tuple(maps)):
                    print("Downloading: " + filename)
                    await download_file("https://tf2maps.net" + href, filepath)

                    #print to mapcycle file
                    with open("mapcycle.txt", "a") as f:
                            splited = filename.split(".")
                            f.write(splited[0] + "\n")

                    #bz2 check
                    if filename.endswith(".bz2"):
                        print("Decompressing.")
                        map_decompressed = bz2.BZ2File(filename).read()
                        print(map_decompressed)

                    if filename.endswith(".zip"):
                        print("Unzipping.")
                        with ZipFile(filepath) as zipObject:
                            splited = filename.split(".")
                            zipObject.extractall(path=os.getcwd() + "/maps/" + str(splited[0]))
                            pass


            except:
                with open("errors.txt", "a") as f:
                    title = download_soup.select(".p-title-value")[0].text.strip()
                    f.write("Error downloading: " + str(title.rstrip()) + "\n")

async def unzip_file(file):
    pass

async def download_file(link, destination):
    async with httpx.AsyncClient() as client:
        response = await client.get(link)

        with open(destination, "wb") as file:
            file.write(response.content)

async def get_download_filename(link):
    async with httpx.AsyncClient() as client:
        response = await client.head(link)
        content_header = response.headers.get("content-disposition")
        matches = re.search("filename=\"([\w.]+)\"", content_header)
        filename = matches.group(1)

        return filename

#loooooop
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
except KeyboardInterrupt:
    pass
finally:
    loop.stop()
