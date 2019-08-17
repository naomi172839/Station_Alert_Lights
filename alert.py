#  Copyright (c) 2019
#  Author: Naomi Bonnin
#  Last Modified: 8/17/19, 9:22 AM
#  Description:  A visual alerting system for Laurel Volunteer Rescue Squad

import subprocess
import time
import email
import logging
from imapclient.imapclient import IMAPClient
import flux_led
import webcolors

# Prevents script from failing on login
time.sleep(10)

# necessary information
colorBlue = webcolors.name_to_rgb("blue")
colorRed = webcolors.name_to_rgb("red")
colorPurple = webcolors.name_to_rgb("purple")
colorGreen = webcolors.name_to_rgb("green")
colorYellow = webcolors.name_to_rgb("yellow")
colorOff = "0,0,0"
host = 'imap.gmail.com'
user = 'station49alerts'
password = 'Wicked2013'

# Initializes logger and opens stream.  Change path for each system
logger = logging.getLogger('alerting')
hdlr = logging.FileHandler('alerting.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s (%(threadName)-10s) %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

logger.info('Started')
print("Started")


# noinspection PyGlobalUndefined
def bulb_scan():
    try:
        ip_addresses = []
        scanner = flux_led.BulbScanner()
        bulbs_found = scanner.scan(10)
        for bulb in bulbs_found:
            ip_addresses.append(bulb['ipaddr'])
            logger.info(ip_addresses)
        return ip_addresses
    except Exception as exc:
        logger.log(str(exc))


# Downloads the latest unread email from gmail and returns the entire body of the email
def pull_email():
    try:
        server = IMAPClient(host)
        server.login(user, password)
        server.select_folder('INBOX')
        messages = server.search('UNSEEN')
        for uid, message_data in server.fetch(messages, 'RFC822').items():
            email_message = email.message_from_bytes(message_data[b'RFC822'])
            email_text = email_message.get_payload(decode=True)
            server.add_flags(uid, ['\\SEEN'])
            server.logout()
            split_email = email_text.decode('UTF-8').split('\r\n')
            return split_email
    except Exception as e:
        logger.error(str(e))


# Searches through a string for each unit and returns an array of how many times each unit appeared
def find_units(body):
    try:
        amb1 = str(body).count('A849')
        pa1 = str(body).count('PA849')
        e1 = str(body).count('E849')
        re1 = str(body).count('RE849')
        sq1 = str(body).count('SQ849')
        wr1 = str(body).count('WR849')
        units_found = [amb1, pa1, e1, re1, sq1, wr1]
        return units_found
    except Exception as e:
        logger.error(str(e))


def amb(counts):
    return 0 < counts[0] != counts[1]


def pa(counts):
    return 0 < counts[1] != counts[0]


def eng(counts):
    return counts[2] > 0 or counts[3] > 0


def sq(counts):
    return counts[4] > 0


def wr(counts):
    return counts[5] > 0


def set_pattern(counts, bulb_address_list):
    colors = []
    if amb(counts):
        colors.append(colorBlue)
    if pa(counts):
        colors.append(colorPurple)
    if eng(counts):
        colors.append(colorRed)
    if sq(counts):
        colors.append(colorGreen)
    if wr(counts):
        colors.append(colorYellow)

    if len(colors) == 1:
        print("True")
        print(bulb_address_list)
        for address in bulb_address_list:
            print(address)
            print(colors)
            bulb = flux_led.WifiLedBulb(address)
            bulb.setRgb(colors)


bulb_addresses = bulb_scan()
time.sleep(10)
logger.info(bulb_addresses)

while True:
    try:
        text = pull_email()
        if text is not None:
            units = find_units(text[3])
            set_pattern(units, bulb_addresses)
            time.sleep(15)
        else:
            time.sleep(1)
    except Exception as e:
        logging.error(str(e))
