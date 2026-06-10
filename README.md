Nuty Image Converter — Super Simple Install

What this does
A tiny Nautilus (GNOME) extension that adds a right-click "Convert" action to convert images.

Prerequisites
- GNOME + Nautilus
- Python 3

Install (copy-paste each line)

cd ~/Projects/nutyimgconvertor-main
chmod +x install.sh
./install.sh

If the installer asks for root, run:
sudo ./install.sh

Permissions note
- Make the installer executable before running: chmod +x install.sh

Optional tools
To install optional encoders (improve format support):
chmod +x install-tools.sh
./install-tools.sh

Uninstall (copy-paste)

chmod +x uninstall.sh
./uninstall.sh

Restart Nautilus to apply changes
nautilus -q

Quick usage
Open Nautilus, right-click an image, choose "Convert" and pick a format.

Showcase 
___________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
-- Showcase preview --

![](images/showcase-1.png)

![](images/showcase-2.png)
