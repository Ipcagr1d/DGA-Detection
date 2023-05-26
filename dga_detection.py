#!/usr/bin/env python3

# Software License Agreement (BSD License)
# Copyright (c) 2017 Phil Arkwright
# Modified to comply with modern framework
# All rights reserved.

from pprint import pprint
from scapy.all import *
import scipy.stats

import configparser
import os.path
import json
import tldextract  # Separating subdomain from input_domain in capture
import majestic

from pushbullet import PushBullet

import argparse

pushbullet_key = ''
if pushbullet_key != '':
    # Configure Pushbullet
    p = PushBullet(pushbullet_key)

    def send_note(note):
        push = p.push_note('%s' % (note), '')

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def load_settings():
    if os.path.isfile('data/settings.conf'):
        Config = configparser.ConfigParser()
        Config.read("data/settings.conf")
        percentage_list_dga_settings = float(Config["Percentages"]["percentage_list_dga_settings"])
        percentage_list_majestic_settings = float(Config["Percentages"]["percentage_list_majestic_settings"])
        baseline = float(Config["Percentages"]["baseline"])
        total_bigrams_settings = float(Config["Values"]["total_bigrams_settings"])
        return baseline, total_bigrams_settings
    else:
        print("No settings file. Please run the training function.")

def load_data():
    if os.path.isfile('data/database.json') and os.path.isfile('data/settings.conf'):
        baseline, total_bigrams_settings = load_settings()

        with open('data/database.json', 'r') as f:
            try:
                bigram_dict = json.load(f)
                process_data(bigram_dict, total_bigrams_settings)  # Call process_data
            except ValueError:
                bigram_dict = {}
    else:
        try:
            Config = configparser.ConfigParser()
            Config.add_section('Percentages')
            Config.add_section('Values')
            Config.set('Percentages', 'baseline', '0')
            with open("data/settings.conf", 'w') as cfgfile:
                Config.write(cfgfile)
        except:
            print("Settings file error. Please delete.")
            exit()

        if os.path.isfile('data/majestic_top_1m_domain.json'):
            with open('data/majestic_top_1m_domain.json', 'r') as f:
                training_data = json.load(f)
        else:
            print("Downloading majestic Top 1m Domains...")
            training_data = majestic.top_list(1000000)
            with open('data/majestic_top_1m_domain.json', 'w') as f:
                json.dump(training_data, f)

        bigram_dict = {}
        total_bigrams = 0
        for input_domain in training_data:
            input_domain = tldextract.extract(input_domain[1])
            if len(input_domain.domain) > 5 and "-" not in input_domain.domain:
                print("Processing domain:", input_domain.domain)
                for bigram_position in range(len(input_domain.domain) - 1):
                    total_bigrams += 1
                    if input_domain.domain[bigram_position:bigram_position + 2] in bigram_dict:
                        bigram_dict[input_domain.domain[bigram_position:bigram_position + 2]] += 1
                    else:
                        bigram_dict[input_domain.domain[bigram_position:bigram_position + 2]] = 1

        pprint(bigram_dict)
        with open('data/database.json', 'w') as f:
            json.dump(bigram_dict, f)

        process_data(bigram_dict, total_bigrams)

def process_data(bigram_dict, total_bigrams):
    # Sort bigrams by occurrence
    bigram_sorted = sorted(bigram_dict.items(), key=lambda x: x[1], reverse=True)

    print("\nBigram Sorted List")
    pprint(bigram_sorted)

    total_bigrams_settings = 0.75
    percentage_list_majestic_settings = 0.75
    percentage_list_dga_settings = 0.75

    # Write list to json file
    with open('data/bigram_sorted.json', 'w') as f:
        json.dump(bigram_sorted, f)

    # Process data to extract average percentages
    for bigram in bigram_sorted:
        if bigram[0] in majestic.top_list(100000):
            percentage_list_majestic_settings += bigram[1]
        else:
            percentage_list_dga_settings += bigram[1]

        total_bigrams_settings += bigram[1]

    percentage_list_dga_settings = percentage_list_dga_settings / total_bigrams_settings
    percentage_list_majestic_settings = percentage_list_majestic_settings / total_bigrams_settings

    # Write settings to configuration file
    Config = configparser.ConfigParser()
    Config.read("data/settings.conf")
    Config.set('Percentages', 'percentage_list_dga_settings', str(percentage_list_dga_settings))
    Config.set('Percentages', 'percentage_list_majestic_settings', str(percentage_list_majestic_settings))
    Config.set('Values', 'total_bigrams_settings', str(total_bigrams_settings))

    with open("data/settings.conf", 'w') as cfgfile:
        Config.write(cfgfile)

def testing():
    if os.path.isfile('data/test_domains.txt'):
        with open('data/test_domains.txt', 'r') as f:
            domains = f.readlines()
    else:
        print("Test file not found.")
        exit()

    detection_count = 0
    total_count = 0
    for domain in domains:
        if check_domain(domain.rstrip("\n")) == "dga":
            detection_count += 1
        total_count += 1

    print("Detection Rate: ", (detection_count / total_count) * 100, "%")

def check_domain(input_domain):
    try:
        input_domain = tldextract.extract(input_domain)
    except:
        print("Invalid domain:", input_domain)
        return

    if len(input_domain.domain) < 6 or "-" in input_domain.domain:
        return "white"

    baseline, total_bigrams_settings = load_settings()

    with open('data/bigram_sorted.json', 'r') as f:
        bigram_sorted = json.load(f)

    percentage_list_dga = 0
    percentage_list_majestic = 0
    total_bigrams = 0

    for bigram in bigram_sorted:
        if input_domain.domain[bigram_position:bigram_position + 2] in bigram_dict:
            total_bigrams += bigram_dict[input_domain.domain[bigram_position:bigram_position + 2]]

            if bigram[0] in majestic.top_list(100000):
                percentage_list_majestic += bigram_dict[input_domain.domain[bigram_position:bigram_position + 2]]
            else:
                percentage_list_dga += bigram_dict[input_domain.domain[bigram_position:bigram_position + 2]]

    if total_bigrams != 0:
        percentage_list_dga = percentage_list_dga / total_bigrams
        percentage_list_majestic = percentage_list_majestic / total_bigrams
    else:
        percentage_list_dga = 0
        percentage_list_majestic = 0

    if percentage_list_dga > percentage_list_dga_settings + baseline:
        send_note("Possible DGA Domain Detected: %s" % (input_domain.domain))
        return "dga"
    elif percentage_list_majestic > percentage_list_majestic_settings + baseline:
        return "majestic"
    else:
        return "white"

def main():
    parser = argparse.ArgumentParser(description="Domain Generation Algorithm Detection")
    parser.add_argument("-t", "--train", help="Train the algorithm", action="store_true")
    parser.add_argument("-c", "--check", help="Check a domain", type=str)
    parser.add_argument("-r", "--rate", help="Check detection rate", action="store_true")
    args = parser.parse_args()

    if args.train:
        load_data()
    elif args.check:
        result = check_domain(args.check)
        print("Result:", result)
    elif args.rate:
        testing()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
