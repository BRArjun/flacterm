```
███████╗██╗      █████╗  ██████╗████████╗███████╗██████╗ ███╗   ███╗
██╔════╝██║     ██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗████╗ ████║
█████╗  ██║     ███████║██║        ██║   █████╗  ██████╔╝██╔████╔██║
██╔══╝  ██║     ██╔══██║██║        ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║
██║     ███████╗██║  ██║╚██████╗   ██║   ███████╗██║  ██║██║ ╚═╝ ██║
╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
```

[![GitHub license](https://img.shields.io/github/license/ravachol/kew?color=333333&style=for-the-badge)](https://github.com/ravachol/kew/blob/master/LICENSE)

Stream [FLAC](https://en.wikipedia.org/wiki/FLAC) music, from the comfort of your Linux terminal.

## Features

- Search and play high quality sound tracks
- Built-in synchronized lyrics display
- Navigate quickly with easy to remember keybindings
- Easily find track metadata
- Bundled with every functionality you'll ever need - Playing queue, Playlists, Downloads and more!
- Your data stays with you and will always be private

## Installation

1. Start by cloning this repository locally
```
git clone https://github.com/BRArjun/flacterm.git
```
2. Install the required modules
```
cd your/path/to/flacterm
pip install -r requirements.txt
```

> [!IMPORTANT]
> Tested on **_Ubuntu 22.04_** with **_Python 3.10.12_**.

> [!WARNING]
> This application has not been tested on any Windows machine, and may not work as intended. 

## Usage

```
python3 main.py
```

## Keybindings

- <kbd>Space</kbd> to start or pause playback
- <kbd>></kbd> and <kbd><</kbd> to navigate results
- <kbd>q</kbd> to come out of the application
- <kbd>l</kbd> to toggle synced lyrics
- <kbd>s</kbd> to toggle track info panel
- <kbd>/</kbd> to start a new search within
- <kbd>Esc</kbd> to stop playback
- <kbd>b</kbd> and <kbd>v</kbd> for skip forward and rewind
- <kbd>r</kbd> to toggle repeat mode
- <kbd>a</kbd> to add currently hovered track to queue
- <kbd>y</kbd> to remove the least recently added track from queue
- <kbd>t</kbd> to toggle displaying the queue
- <kbd>c</kbd> to completely clear the queue
- <kbd>k</kbd> to switch to playing from queue
- <kbd>e</kbd> to return to normal results
- <kbd>m</kbd> to display playlist view
- <kbd>Ctrl+a</kbd> to add hovered song into playlist
- <kbd>Ctrl+r</kbd> to remove hovered song from playlist
- <kbd>d</kbd> to download the hovered track

## Screenshots

### Main Menu
![Screenshot from 2025-06-03 13-09-28](https://github.com/user-attachments/assets/ad3fa308-cd0c-4c41-a616-38dab8140acb)

### Track Search Results
![Screenshot from 2025-06-03 13-11-52](https://github.com/user-attachments/assets/60b1090b-c614-47f6-bd21-8ffef8837ce5)

### Synced Lyrics
![Screenshot from 2025-06-03 13-12-36](https://github.com/user-attachments/assets/43e1636b-4b01-4cc9-94b4-dc0686f7b28a)

### Queued Tracks
![Screenshot from 2025-06-03 13-14-08](https://github.com/user-attachments/assets/57164a12-a2ab-41e3-94ef-b6a4c6dc384c)

### Playlist Manager
![Screenshot from 2025-06-03 13-14-33](https://github.com/user-attachments/assets/3880c4eb-dbf6-41d1-ad63-83fca3449864)


## Inspirations
I was on the search for a terminal FLAC streaming tool, but could not find any that could support streaming FLACs natively [either that, or I just suck at searching, :( ]\
I knew downloading FLAC files and then playing them was an option as well, but I wanted to focus on streaming these files just like Spotify and Youtube Music. \
Other existing tools support high res formats too but FLAC files provide the best audio experience out of all existing formats.\
I felt that such an application may be useful to me at the very least, even if it is not for others, and so I built flacterm :) .

Major thanks to these other open source projects for being my inspiration: 
- [kew](https://github.com/ravachol/kew/)
- [spotify-tui](https://github.com/Rigellute/spotify-tui)
 
## Stuff TODO

- [ ] Major UI overhaul
- [ ] Make API calls faster
- [ ] Add playlist imports from other music services



