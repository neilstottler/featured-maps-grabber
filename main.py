# Std Lib Imports
import asyncio
import re
import os
import tempfile
import bz2
from zipfile import ZipFile, Path
import shutil

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
            print(download_page)

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
                    downloaded_filename = ''

                    #this stops duplicates in the mapcycle for some reason???
                    href = ''

            #download the file to /maps/
            try:
                downloaded_filename = await get_download_filename("https://tf2maps.net" + href)
                print(downloaded_filename)
                print(href)
                filepath = str(os.getcwd()) + "/maps/" + str(downloaded_filename)

                maps = ['arena_', 'cp_', 'ctf_', 'koth_', 'pass_', 'pd_', 'pl_', 'plr_', 'sd_']

                #filter for mvm maps
                if downloaded_filename.startswith(tuple(maps)):
                    if downloaded_filename.endswith(".bsp"):
                        print("Downloading: " + downloaded_filename)
                        await download_file("https://tf2maps.net" + href, filepath)

                        await add_to_mapcycle(downloaded_filename)

                    #bz2 check
                    if downloaded_filename.endswith(".bz2"):
                        await download_file("https://tf2maps.net" + href, filepath)
                        print(f"Decompressing {downloaded_filename}.")

                        zipfile = bz2.BZ2File(filepath) # open the file
                        data = zipfile.read() # get the decompressed data
                        newfilepath = filepath[:-4] # assuming the filepath ends with .bz2
                        open(newfilepath, 'wb').write(data) # write a uncompressed file

                        #remove bz2

                        #this isnt working for some reason
                        os.remove(os.getcwd() + '/maps/' + downloaded_filename)

                        await add_to_mapcycle(downloaded_filename)

                    #zip check
                    if downloaded_filename.endswith(".zip"):
                        await download_file("https://tf2maps.net" + href, filepath)
                        print(f"Unzipping {downloaded_filename}.")
                        
                        #unzip the zip
                        with ZipFile(filepath) as originalzip:
                            zipcontents = ZipFile.infolist(originalzip)
                            for file in zipcontents:
                                #check for bsp in folders
                                if file.filename.endswith('.bsp'):

                                    desired_file = file.filename.split('/')

                                    #get it
                                    with open('maps/' + desired_file[1], 'wb') as fileoutput:
                                        fileoutput.write(originalzip.read(str(file.filename)))

                        #delete zip
                        os.remove(os.getcwd() + '/maps/' + downloaded_filename)

                        await add_to_mapcycle(downloaded_filename)

            except:
                with open("errors.txt", "a") as f:
                    title = download_soup.select(".p-title-value")[0].text.strip()
                    f.write("Error downloading: " + str(title.rstrip()) + "\n")

async def add_to_mapcycle(mapname):
    #print to mapcycle file
    with open("mapcycle.txt", "a") as f:
        splited = mapname.split(".")
        f.write(splited[0] + "\n")

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
