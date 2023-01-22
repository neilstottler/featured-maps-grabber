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

#store the bsp name for later use
bsp_file_name = 'bsp name'

async def main():
    global bsp_file_name

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
                    downloaded_filename = ''

                    #this stops duplicates in the mapcycle for some reason???
                    href = ''

            #download the file to /maps/
            try:
                downloaded_filename = await get_download_filename("https://tf2maps.net" + href)
                filepath = str(os.getcwd()) + "/maps/" + str(downloaded_filename)

                maps = ['arena_', 'cp_', 'ctf_', 'koth_', 'pass_', 'pd_', 'pl_', 'plr_', 'sd_']


                #filter for mvm maps
                if downloaded_filename.startswith(tuple(maps)):
                    if downloaded_filename.endswith(".bsp"):
                        #setr the name for consistency
                        bsp_file_name = downloaded_filename

                        print("Downloading: " + downloaded_filename)
                        await download_file("https://tf2maps.net" + href, filepath)
                        await add_to_mapcycle(downloaded_filename)


                        #compress for redirect
                        await compress_file(downloaded_filename)

                    #bz2 check
                    if downloaded_filename.endswith(".bz2"):
                        await download_file("https://tf2maps.net" + href, filepath)
                        print(f"Decompressing {downloaded_filename}.")
                        await bz2_decompress(filepath, downloaded_filename)
                        await add_to_mapcycle(downloaded_filename)

                        #compress for redirect
                        await compress_file(bsp_file_name)

                    #zip check
                    if downloaded_filename.endswith(".zip"):
                        print(f"Downloading {downloaded_filename}.")
                        await download_file("https://tf2maps.net" + href, filepath)
                        print(f"Unzipping {downloaded_filename}.")
                        
                        await unzip_file(filepath, downloaded_filename)
                        await add_to_mapcycle(downloaded_filename)

                        #compress for redirect
                        print(bsp_file_name)
                        await compress_file(bsp_file_name)


            except Exception as e:
                print("-----------------------------------------------------")
                print(download_page)
                print(e)
                print("-----------------------------------------------------")

                with open("errors.txt", "a") as f:
                    title = download_soup.select(".p-title-value")[0].text.strip()
                    f.write("Error downloading: " + str(title.rstrip()) + "\n")

async def add_to_mapcycle(mapname):
    #print to mapcycle file
    with open("mapcycle.txt", "a") as f:
        splited = mapname.split(".")
        f.write(splited[0] + "\n")

async def bz2_decompress(filepath, downloaded_filename):
    global bsp_file_name

    with bz2.BZ2File(filepath) as f:
        data = f.read()
        newfilepath = filepath[:-4]
        open(newfilepath, 'wb').write(data)

        bsp_file_name = str(newfilepath).split('/')[-1]

    #remove bz2 after extracting
    os.remove(os.getcwd() + '/maps/' + downloaded_filename)

async def compress_file(filepath):
    print(f'Compressing {filepath} for redirect.')
    output_filepath = os.getcwd() + '/compressed_maps/' + f"{filepath}.bz2"

    with open('maps/' + filepath, 'rb') as input:
        with bz2.BZ2File(output_filepath, 'wb') as output:
            shutil.copyfileobj(input, output)

    return output_filepath

async def unzip_file(filepath, downloaded_filename):
    global bsp_file_name
    
    with ZipFile(filepath) as originalzip:
        zipcontents = ZipFile.infolist(originalzip)
        for file in zipcontents:
            #check for bsp in folders
            if file.filename.endswith('.bsp'):

                #this is only for mappers who put their map in a folder in a zip
                if '/' in file.filename:
                    desired_file = file.filename.split('/')

                    #get it
                    with open('maps/' + desired_file[1], 'wb') as fileoutput:
                        fileoutput.write(originalzip.read(str(file.filename)))
                        
                        #set this value for bz2 compression later
                        bsp_file_name = str(desired_file[1])
                else:
                    with open('maps/' + file.filename, 'wb') as fileoutput:
                        fileoutput.write(originalzip.read(str(file.filename)))

                        #set this value for bz2 compression later
                        bsp_file_name = str(file.filename)
    
    #remove zip file
    os.remove(os.getcwd() + '/maps/' + downloaded_filename)

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
