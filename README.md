# GrandArchiveProxier

## How to use:

Get any deck in one of the deck builders that can export to TTS

In Tabletop Simulator, use this mod:
https://steamcommunity.com/sharedfiles/filedetails/?id=3430736587&searchtext=grand+archive

Upload your deck into the mod, and it will create 3 decks: Main, Material, and Sidboard. Stack them all in one deck and save that as an Object on TTS

Go to this folder: C:\Users\USERNAME\Documents\My Games\Tabletop Simulator\Saves\Saved Objects -> replacing USERNAME with your username

Inside, you will find a .json file with the name you saved for your deck. 

Open the file: generate_from_tts.py, and change the variable tts_file to the path of your own deck .json file.

Run on the terminal using "python generate_from_tts.py"; this will download the images and wait for it to finish. After it is done, it will create a file in the Output folder named tts_cards_printable.pdf

Rename the pdf file to avoid overwriting, and it's done. Just print this pdf file, and you're good to go.

P.S. It is hacky and full of extra steps, but it works

## Requirements
Python version 3.11 or newer
Tabletop Simulator (available on Steam)

## Plans
I'll eventually try to make a simple UI and find a more reasonable way that doesn't involve using TTS, but for now this serves its purpose
