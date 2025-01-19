# stroomer

## Introduction 
A Python based daemon that will handle button presses on your Stream Deck. It is configured using an old school INI file.

## Example
The attached example has three buttons (currently the only supported button types):
- Two buttons that sends an SNMP "SET" command with a value on a numerical OID (MIBs and readable OIDs are a hassle) to an SNMP device
- A button that ends the daemon ("Exit")

## Example .ini file
See stroomer.ini.example

## Requirements
- Python 3

## Installation and running
- Clone the git repo
- Copy/rename stroomer.ini.example to stroomer.ini
- Edit stroomer.ini per your requirements
- Create the Python virtual environment using ``python3 -m venv env``
- Enter the virtualenv using ``source env/bin/activate``
- Install the requirements ``pip -r requirements.txt``
- Start stroomer ``python3 ./stroomer.py``

## Ideas/issues/fixes
See the github issues page at https://github.com/ramdyne/stroomer/issues

## Pronunciation
For English speaking people, stroomer is pronounced "stroamer"; it is originally a Dutch play on the English word "stream".
