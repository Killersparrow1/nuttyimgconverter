
Nuty Image Converter — Super Simple Install

What this does

A tiny Nautilus (GNOME) extension that adds a right-click "Convert" action to convert images.

Prerequisites

- GNOME + Nautilus
- Python 3

Install (copy-paste each line)

git clone https://github.com/witherdotexe/nuttyimgconverter.git

cd ~/nuttyimgconverter/

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
<img width="501" height="386" alt="Screenshot From 2026-06-10 23-42-19" src="https://github.com/user-attachments/assets/57dcb233-1281-4559-baf3-0ba3632d86e1" />
<img width="480" height="607" alt="Screenshot From 2026-06-10 23-42-09" src="https://github.com/user-attachments/assets/d3a0b96b-584b-49dd-ad85-81c0d2554afd" />
<img width="421" height="106" alt="Screenshot From 2026-06-10 23-44-00" src="https://github.com/user-attachments/assets/4f3dd6a1-56e4-4625-9da0-e86e04b6d67c" />
<img width="511" height="105" alt="Screenshot From 2026-06-10 23-43-35" src="https://github.com/user-attachments/assets/2bd4cb72-32d9-4b98-8c45-27c2b50256ae" />
