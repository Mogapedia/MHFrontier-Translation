# Monster Hunter Frontier Translation

A community-driven project to translate Monster Hunter Frontier game files.
This is a *translation setup guide*, if you only want to translate game files, check the online Weblate website.

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Setup](#setup)
4. [Translation Process](#translation-process)
5. [Other tools](#other-tools-not-integrated-yet)

## Introduction

The Frontier Translation Project aims to facilitate the translation of Monster Hunter Frontier game files through a community effort.
This project relies on the collaboration of users who contribute translations via Weblate, an open-source web platform.

If you only want to translate game files, you only need to register on Weblate.
If you wan to dig deeper, read the next sections.

## Requirements

To participate in this project, you will need:

* [ReFrontier](https://github.com/Houmgaor/ReFrontier): A C# application used for decrypting and decompressing Frontier game files.
* [FrontierTextHandler](https://github.com/Houmgaor/FrontierTextHandler): A Python tool that extracts strings from original source files and creates a CSV file for translation purposes.
* The original game files.

## Setup

To start, follow these steps:

1. Get the original game files.
2. Download and install [ReFrontier](https://github.com/Houmgaor/ReFrontier). You can use the release for pre-built executables.
3. Obtain FrontierTextHandler and use it to create a CSV file from the original game file.
4. Push the resulting CSV file to Weblate for translation.

Assuming you use Windows and ReFrontier 1.2.0, the commands to get the CSV should look something like this:

```bash
# Create mhfdat.bin.decd.bin, a readable version of mhfdat.bin
./ReFrontier.exe mhfdat.bin --log --noFileRewrite --close  
cp mhfdat.bin.decd.bin ../FrontierTextHandler/data
cd ../FrontierTextHandler
python main.py mhfdat.bin.decd.bin --xpath=dat/items/name
```

The CSV file should be ``FrontierTextHandler/output/dat-items-name.csv``.

## Translation Process

Once your translation is complete, follow these steps:

1. Download the translated CSV file from Weblate.
2. Use FrontierTextHandler to insert the translated CSV file into your original game file.
3. Utilize ReFrontier to reformat the file into a format compatible with the Frontier client.

Starting from the CSV and ReFrontier 1.2, with a translated file called "dat-items-name.csv":

```bash
# Edit the binary file with the new translations
python main.py mhfdat.bin.decd.bin dat-items-name.csv --insert
cp mhfdat.bin.decd.bin ../ReFrontier
cd ../ReFrontier
# Create a new mhfdat.bin
./ReFrontier.exe mhfdat.bin.decd.bin --compress=3,80 --encrypt --close
```

Replace your original "mhfdat.bin" by the new one.
You can now enjoy new translations.

## Other tools (not integrated yet)

For NPC dialogues, you can use: [stratick-dev/readDialogue.py](https://gist.github.com/stratic-dev/162f4e5ad1766aeb59eb5edf1c1fb288) and [stratick-dev/writeDialogue.py](https://gist.github.com/stratic-dev/51e7927afc67612782e54ae87b4612b2).

For quest data (on the server side): [Pax's MHFZ Quest Editor](https://github.com/Paxlord/PaxMHFZQuestEditor). The main issue of this tool is that it is built to be used in closed loop.

## Notes

The downloaded translation will be in the form of a CSV file. When using ReFrontier, ensure that you are working with the correct file formats and settings to avoid any issues.
