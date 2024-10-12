# Batronix Magnova - Python SCPI Helper

Helper script to read/write values via SCPI (USBTMC).

```bash

bytronix/main.py -h
usage: main.py [-h] {device,rest,commands} ...

options:
  -h, --help            show this help message and exit

command (required):
  Run command with the loaded configuration.

  {device,rest,commands}
    device              device commands
    rest                REST API
    commands            known device commands
```

## Installation

```bash
# add udev-rules
cd /etc/udev/rules.d && echo '
# Batronix: idVendor==0x19b2 | Magnova: idProduct=0x0030
ACTION=="add", SUBSYSTEMS=="usb", ATTRS{idVendor}=="19b2", ATTRS{idProduct}=="0030", MODE="660", GROUP="users"
' | sudo tee ./95-batronix-magnova.rules

sudo udevadm control --reload  
sudo udevadm trigger
```

```bash
cd ~/bytronix
poetry shell
poetry install
bytronix/main.py -h
```
