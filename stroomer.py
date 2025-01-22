#
 # This file is part of stroomer (https://github.com/ramdyne/stroomer).
 #
 # Copyright (c) 2025 Andreas Sikkema.
 #
 # This program is free software: you can redistribute it and/or modify
 # it under the terms of the GNU General Public License as published by
 # the Free Software Foundation, version 3.
 #
 # This program is distributed in the hope that it will be useful, but
 # WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 # General Public License for more details.
 #
 # You should have received a copy of the GNU General Public License
 # along with this program. If not, see <http://www.gnu.org/licenses/>.
 #

import os
import threading
import configparser


from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")


devices = {}
buttons = {}

# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_image(deck, icon_filename, font_filename, label_text):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    icon = Image.open(icon_filename)
    image = PILHelper.create_scaled_key_image(deck, icon, margins=[0, 0, 20, 0])

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 14)
    draw.text((image.width / 2, image.height - 5), text=label_text, font=font, anchor="ms", fill="white")

    return PILHelper.to_native_key_format(deck, image)


# Returns styling information for a key based on its position and state.
def get_key_style(deck, key, state):
    # Last button in the example application is the exit button.
    exit_key_index = deck.key_count() - 1

    if key == exit_key_index:
        name = "exit"
        icon = "{}.png".format("Exit")
        font = "Roboto-Regular.ttf"
        label = "Bye" if state else "Exit"
    else:
        name = "emoji"
        icon = "{}.png".format("Pressed" if state else "Released")
        font = "Roboto-Regular.ttf"
        label = "Pressed!" if state else "Key {}".format(key)

    return {
        "name": name,
        "icon": os.path.join(ASSETS_PATH, icon),
        "font": os.path.join(ASSETS_PATH, font),
        "label": label
    }


def update_key_image(deck, key, state):
    key_style = get_key_style(deck, key, state)

    if str(key) in buttons:
        button = buttons[str(key)]
        if 'icon' in button:
            key_style['icon'] = button['icon']
        image = render_key_image(deck, key_style["icon"], key_style["font"], button['label'])

        with deck:
            # Update  requested key with the generated image.
            deck.set_key_image(key, image)


def key_change_callback(deck, key, key_down):
    if key >= deck.key_count():
        return

    update_key_image(deck, key, key_down)

    # Check if the key is changing to the pressed state.
    if key_down:
        if str(key) in buttons:
            handle_button_press(key)


def handle_button_press(key):
    button = buttons[str(key)]

    if button['type'] == 'snmp':
        handle_snmp_button_press(button)
    elif button['type'] == 'exit':
        handle_exit_button_press(button)
    else:
        print("No handler for button " + str(key))


def handle_snmp_button_press(button):
    from ezsnmp import Session
    snmp_device = devices[button['device']]
    session = Session(hostname=snmp_device['host'], community=snmp_device['community'], version=2)

    if button['command'] == 'get':
        print("Get command is currently unsupported")
    elif button['command'] == 'set':
        settype = "string"
        if button['value_type'] in ['integer', 'int', 'number']:
            settype = 'integer'

        session.set(button['oid'], button['value'], settype)
    else:
        print("Unsupported command " + button['command'] )

def handle_exit_button_press(button):
    """Clear the deck and close the thread(s) as started by the StreamDeck
       library. This will end the application"""
    with deck:
        deck.reset()
        deck.close()


def add_snmp_device_from_section(section_name, section):
    new_device = {'type': section['device_type'],
                  'host': section['host'],
                  'community': section['community'],
                  'version': section['version']
                  }
    devices[section_name] = new_device

def add_device_from_section(section_name, section):
    if section["device_type"] == "snmp":
        add_snmp_device_from_section(section_name, section)
    else:
        print("Unsupported device " + section_name + " of type " + section["device_type"])

def add_snmp_button_from_section(section_name, section):
    button_location = int(section['location'])
    new_button = {'type': section['button_type'],
                  'location': button_location,
                  'label': section['label'],
                  'device': section['device'],
                  'command': section['command'],
                  'oid': section['oid'],
                  'value_type': section['value_type'],
                  'value': section['value'],
                  'icon': os.path.join(ASSETS_PATH, section['icon'])
                  }

    buttons[str(button_location-1)] = new_button


def add_exit_button_from_section(section_name, section):
    button_location = int(section['location'])
    new_button = {'type': section['button_type'],
                  'location': button_location,
                  'label': section['label'],
                  'icon': os.path.join(ASSETS_PATH, 'Exit.png')
                  }

    buttons[str(button_location - 1)] = new_button


def add_button_from_section(section_name, section):
    if section["button_type"] == "snmp":
        add_snmp_button_from_section(section_name, section)
    elif section["button_type"] == "exit":
        add_exit_button_from_section(section_name, section)
    else:
        print("Unsupported button " + section_name + " of type " + section["button_type"])


def load_config_file(file_name="stroomer.ini"):
    config = configparser.ConfigParser()
    config.read(file_name)

    for section in config.sections():
        if 'type' in config[section]:
            if config[section]["type"] == "device":
                add_device_from_section(section, config[section])
            elif config[section]["type"] == "button":
                    add_button_from_section(section, config[section])
            else:
                print("Not a device")
                for option in config[section]:
                    print(" " + option + "= " + config[section][option])
        else:
            if section != "default":
                print("Missing type in section " + section)


if __name__ == "__main__":

    load_config_file()

    streamdecks = DeviceManager().enumerate()

    for index, deck in enumerate(streamdecks):
        if not deck.is_visual():
            continue

        deck.open()
        deck.reset()

        print("Opened '{}' device (serial number: '{}', fw: '{}')".format(
            deck.deck_type(), deck.get_serial_number(), deck.get_firmware_version()
        ))

        # Set initial key images.
        for key in range(deck.key_count()):
            update_key_image(deck, key, False)

        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass
