'''
Created on Nov 23, 2018

@author: Naomi Bonnin
'''

import subprocess
import time
import email
import logging
from imapclient.imapclient import IMAPClient
import flux_led

# Prevents script from failing on login
time.sleep(10)

# necessary information
colorBlue = "0,0,255"
colorRed = "255,0,0"
colorPurple = "255,0,255"
colorGreen = "0,255,0"
colorYellow = "255,255,0"
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


'''

def amb_pa_e_re_sq_wr(counts):
    return amb(counts) and pa(counts) and eng(counts) and sq(counts) and wr(counts)


def amb_e_re_sq_wr(counts):
    return amb(counts) and not pa(counts) and eng(counts) and sq(counts) and wr(counts)


def amb_pa_sq_wr(counts):
    return amb(counts) and pa(counts) and not e(counts) and sq(counts) and wr(counts)


def amb_pa_e_re_wr(counts):
    return amb(counts) and pa(counts) and e(counts) and not sq(counts) and wr(counts)


def amb_pa_e_re_sq(counts):
    return amb(counts) and pa(counts) and e(counts) and sq(counts) and not wr(counts)


def pa_e_re_sq_wr(counts):
    return not amb(counts) and pa(counts) and e(counts) and sq(counts) and wr(counts)


def amb_sq_wr(counts):
    return amb(counts) and not pa(counts) and not e(counts) and sq(counts) and wr(counts)


def amb_e_re_wr(counts):
    return amb(counts) and not pa(counts) and e(counts) and not sq(counts) and wr(counts)


def amb_e_re_sq(counts):
    return amb(counts) and not pa(counts) and e(counts) and sq(counts) and not wr(counts)

'''


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
    logger.info(colors)
    logger.info(bulb_address_list)

    if len(colors) == 1:
        for address in bulb_address_list:
            logger.info(address)
            bulb = flux_led.WifiLedBulb(address)
            bulb.setRgb(colors[0],colors[1], colors[2])


"""
# Logic to determine which set of lights to activate.  The return is for debugging
def which_units(counts):
    try:
        if amb_pa_e_re_sq_wr(counts):
            turn_on_amb_pa_e_re_sq_wr()
            return 1

        if amb_e_re_sq_wr(counts):
            turn_on_amb_e_re_sq_wr()
            return 2

        if amb_pa_sq_wr(counts):
            turn_on_amb_pa_sq_wr()
            return 3

        if amb_pa_e_re_wr(counts):
            turn_on_amb_pa_e_re_wr()
            return 4

        if amb_pa_e_re_sq(counts):
            turn_on_amb_pa_e_re_sq()
            return 5

        if pa_e_re_sq_wr(counts):
            turn_on_pa_e_re_sq_wr()
            return 6

        if amb_sq_wr(counts):
            turn_on_amb_sq_wr()
            return 7

        if amb_e_re_wr(counts):
            turn_on_amb_e_re_wr()
            return 8

        if amb_e_re_sq(counts):
            turn_on_amb_e_re_sq()
            return 9

        if (
                (counts[0] > 0 and counts[0] != counts[1]) and
                (counts[1] > 0 and counts[0] != counts[1]) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] == 0) and
                (counts[5] > 0)
        ):
            turn_on_amb_pa_wr()
            return 10

        if (
                (counts[0] > 0 and counts[0] != counts[1]) and
                (counts[1] > 0 and counts[0] != counts[1]) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] > 0) and
                (counts[5] == 0)
        ):
            turn_on_amb_pa_sq()
            return 11

        if (
                (counts[0] > 0 and counts[0] != counts[1]) and
                (counts[1] > 0 and counts[0] != counts[1]) and
                (counts[2] > 0 or counts[3] > 0) and
                (counts[4] == 0) and
                (counts[5] == 0)
        ):
            turn_on_amb_pa_e_re()
            return 12

        if (
                (counts[0] > 0 and counts[0] == counts[1]) and
                (counts[1] > 0 and counts[0] == counts[1]) and
                (counts[2] > 0 or counts[3] > 0) and
                (counts[4] > 0) and
                (counts[5] == 0)
        ):
            turn_on_pa_e_re_sq()
            return 13

        if (
                (counts[0] > 0 and counts[0] == counts[1]) and
                (counts[1] > 0 and counts[0] == counts[1]) and
                (counts[2] > 0 or counts[3] > 0) and
                (counts[4] == 0) and
                (counts[5] > 0)
        ):
            turn_on_pa_e_re_wr()
            return 14

        if (
                (counts[0] > 0 and counts[0] == counts[1]) and
                (counts[1] > 0 and counts[0] == counts[1]) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] > 0) and
                (counts[5] > 0)
        ):
            turn_on_pa_sq_wr()
            return 15

        if (
                (counts[0] == 0) and
                (counts[1] == 0) and
                (counts[2] > 0 or counts[3] > 0) and
                (counts[4] > 0) and
                (counts[5] > 0)
        ):
            turn_on_e_re_sq_wr()
            return 16

        if (
                (counts[0] > 0 and counts[0] != counts[1]) and
                (counts[1] > 0 and counts[0] != counts[1]) and
                (counts[2] == 0 or counts[3] == 0) and
                (counts[4] == 0) and
                (counts[5] == 0)
        ):
            turn_on_amb_pa()
            return 17

        if (
                (counts[0] > 0) and
                (counts[1] == 0) and
                (counts[2] > 0 or counts[3] > 0) and
                (counts[4] == 0) and
                (counts[5] == 0)
        ):
            turn_on_amb_e_re()
            return 18

        if (
                (counts[0] > 0) and
                (counts[1] == 0) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] > 0) and
                (counts[5] == 0)
        ):
            turn_on_amb_sq()
            return 19

        if (
                (counts[0] > 0) and
                (counts[1] == 0) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] == 0) and
                (counts[5] > 0)
        ):
            turn_on_amb_wr()
            return 20

        if (
                (counts[0] > 0 and counts[0] == counts[1]) and
                (counts[1] > 0 and counts[0] == counts[1]) and
                (counts[2] > 0 or counts[3] > 0) and
                (counts[4] == 0) and
                (counts[5] == 0)
        ):
            turn_on_pa_e_re()
            return 21

        if (
                (counts[0] > 0 and counts[0] == counts[1]) and
                (counts[1] > 0 and counts[0] == counts[1]) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] > 0) and
                (counts[5] == 0)
        ):
            turn_on_pa_sq()
            return 22

        if (
                (counts[0] > 0 and counts[0] == counts[1]) and
                (counts[1] > 0 and counts[0] == counts[1]) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] == 0) and
                (counts[5] > 0)
        ):
            turn_on_pa_wr()
            return 23

        if (
                (counts[0] == 0) and
                (counts[1] == 0) and
                (counts[2] > 0 or counts[3] > 0) and
                (counts[4] > 0) and
                (counts[5] == 0)
        ):
            turn_on_e_re_sq()
            return 24

        if (
                (counts[0] == 0) and
                (counts[1] == 0) and
                (counts[2] > 0 or counts[3] > 0) and
                (counts[4] == 0) and
                (counts[5] > 0)
        ):
            turn_on_e_re_wr()
            return 25

        if (
                (counts[0] == 0) and
                (counts[1] == 0) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] > 0) and
                (counts[5] > 0)
        ):
            turn_on_sq_wr()
            return 26

        if (
                (counts[0] > 0) and
                (counts[1] == 0) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] == 0) and
                (counts[5] == 0)
        ):
            turn_on_amb()
            return 27

        if (
                (counts[0] > 0 and counts[0] == counts[1]) and
                (counts[1] > 0 and counts[0] == counts[1]) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] == 0) and
                (counts[5] == 0)
        ):
            turn_on_pa()
            return 28

        if (
                (counts[0] == 0) and
                (counts[1] == 0) and
                (counts[2] > 0 or counts[3] > 0) and
                (counts[4] == 0) and
                (counts[5] == 0)
        ):
            turn_on_e_re()
            return 29

        if (
                (counts[0] == 0) and
                (counts[1] == 0) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] > 0) and
                (counts[5] == 0)
        ):
            turn_on_sq()
            return 30

        if (
                (counts[0] == 0) and
                (counts[1] == 0) and
                (counts[2] == 0 and counts[3] == 0) and
                (counts[4] == 0) and
                (counts[5] > 0)
        ):
            turn_on_wr()
            return 31
        else:
            return 0

    except Exception as e:
        logger.error(str(e))


def turn_on_amb_pa_e_re_sq_wr():
    logger.info('Ambulance, PA, E/RE, SQ, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 5
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])

    logger.info('Off')


def turn_on_amb_e_re_sq_wr():
    logger.info('Ambulance, E/RE, SQ, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 4
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_pa_sq_wr():
    logger.info('Ambulance, PA, SQ, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 4
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_pa_e_re_wr():
    logger.info('Ambulance, PA, E/RE, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 4
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_pa_e_re_sq():
    logger.info('Ambulance, PA, E/RE, SQ')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        count = count + 4
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_pa_e_re_sq_wr():
    logger.info('PA, E/RE, SQ, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 5
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_sq_wr():
    logger.info('Ambulance, SQ, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 3
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_e_re_wr():
    logger.info('Ambulance, E/RE, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 3
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_e_re_sq():
    logger.info('Ambulance, E/RE, SQ')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        count = count + 3
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_pa_wr():
    logger.info('Ambulance, PA, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 3
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_pa_sq():
    logger.info('Ambulance, PA, SQ')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        count = count + 3
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_pa_e_re():
    logger.info('Ambulance, PA, E/RE')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        count = count + 3
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_pa_e_re_sq():
    logger.info('PA, E/RE, SQ')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        count = count + 3
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_pa_e_re_wr():
    logger.info('PA, E/RE, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 3
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_pa_sq_wr():
    logger.info('PA, SQ, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 3
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_e_re_sq_wr():
    logger.info('E/RE, SQ, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 3
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_pa():
    logger.info('Ambulance, PA')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        count = count + 2
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_e_re():
    logger.info('Ambulance, E/RE')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        count = count + 2
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_sq():
    logger.info('Ambulance, SQ')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        count = count + 2
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb_wr():
    logger.info('Ambulance, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 2
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_pa_e_re():
    logger.info('PA, E/RE')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        count = count + 2
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_pa_sq():
    logger.info('PA, SQ')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        count = count + 2
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_pa_wr():
    logger.info('PA, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 2
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_e_re_sq():
    logger.info('E/RE, SQ')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        count = count + 2
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_e_re_wr():
    logger.info('E/RE, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 2
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_sq_wr():
    logger.info('SQ, WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 2
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_amb():
    logger.info('Ambulance')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorBlue])
        time.sleep(1)
        count = count + 1
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_pa():
    logger.info('PA')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorPurple])
        time.sleep(1)
        count = count + 1
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_e_re():
    logger.info('E/RE')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorRed])
        time.sleep(1)
        count = count + 1
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_sq():
    logger.info('SQ')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorGreen])
        time.sleep(1)
        count = count + 1
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')


def turn_on_wr():
    logger.info('WR')
    count = 0
    while count < 60:
        subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', colorYellow])
        time.sleep(1)
        count = count + 1
    subprocess.call(['python', '-m', 'flux_led', '-sS', '-c', '0,0,0'])
    logger.info('Off')

"""
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
