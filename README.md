# XDCC-Downloader

A simple XDCC file downloader written in python. (Personal Project.)

## Usage

Uses XDCC commands to download single or multiple packages.

**Example:**

    # This is the xdcc message: '/msg the_bot xdcc send #1' or '/ctcp the_bot xdcc send #1'
    
    # For single pack download.
    $ '/msg the_bot xdcc send #1'

    # For range of packs.
    $ '/msg the_bot xdcc send #1-10'

    # For multiple specific packs.
    $ '/msg the_bot xdcc send #1,2,45,50'


Json files can be used to download multiple files.

**Example:**

    [
        {
            "server": server address,
            "channel": list of channels to be joined,
            "message": XDCC download command,
            "file_path" : path where the file will be stored,
            "pass": if true will be skiped.
        },
        ...
    ]

Press `CTRL-C` to stop the current download and `CTRL-\` to exit script.

## Setup

This project is not on PyPi. After cloning `pip install .` to install.
After installed `xdcc-bot` command directly initiates the script.