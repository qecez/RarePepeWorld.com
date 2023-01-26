#!/usr/bin/env python3

import sys, os
from pathlib import Path

os.environ['RPW_SCRIPT_BASE'] = str(Path(os.getcwd()).parent)
os.environ['RPW_LOG_PATH'] = str(Path(os.getcwd()).parent / 'logs/')
os.environ['RPW_LOG_LEVEL'] = 'DEBUG'
sys.path.insert(0, os.environ['HOME'] + '/RarePepeWorld/')  # rpw path

import requests
from bs4 import BeautifulSoup

from rpw.DataConnectors import DBConnector
from rpw.QueryTools import PepeData
from rpw.Utils import JSONTool

"""
Methods for getting the urls for each pepe in rarepepedirectory.com
"""

db_connection = DBConnector()
pepe_data = PepeData(db_connection)
pepe_names_list = pepe_data.get_pepe_names()
table = 'assets'
column = 'rarepepedirectory_url'
rarepepedirectory_list_file = "../rpw/static/pepes/rarepepedirectory_links.json"
misses_file = "../rpw/static/pepes/rarepepedirectory_links_misses.txt"


def parse_cache_file(cache: str):
    links = {}
    with open(cache, 'r') as f:
        lines = f.readlines()
    for line in lines:
        parts = line.split(':')
        if len(parts) == 2:
            links[parts[0].strip()] = parts[1].strip()
            print(f"Read: {parts[0]} : {links[parts[0].strip()]}")
    return links


def parse_rarepepedirectory(pepe_names):
    found = JSONTool.read_json_file(rarepepedirectory_list_file)
    search_base = "http://rarepepedirectory.com/?s="
    skipped = []
    i = 0
    while i < len(pepe_names):
        pepe_name = pepe_names[i]
        if pepe_name not in found.keys():
            print(f"Searching for {pepe_name} url")
            url = f"{search_base}{pepe_name}"
            page_content = requests.get(url).text
            soup = BeautifulSoup(page_content, 'html.parser')
            try:
                pepe_url = soup.findAll('a', {'title': pepe_name})[0]['href']
                print(f"Found at {pepe_url}")
                # f.writelines(f"{pepe_name} : {pepe_url}\n")
                JSONTool.store_json_file(rarepepedirectory_list_file, found, sort_keys=True, indent=2)
                found[pepe_name] = pepe_url
            except IndexError:
                print(f"Could not find link for {pepe_name}. Skipping")
                skipped.append(pepe_name)
        else:
            print(f"Already in list: {pepe_name}, value {found[pepe_name]}")
            found[pepe_name] = found[pepe_name]
        i += 1
    return {'urls': found, 'misses': skipped}


def db_insert(db_connector: DBConnector, rarepepedirectory_urls: dict):
    for pepe_name, rarepepedirectory_url in rarepepedirectory_urls.items():
        query = f"UPDATE {table} SET {column}=\'{rarepepedirectory_url}\' WHERE asset=\'{pepe_name}\'"
        print(query)
        db_connector.execute(query)
        db_connector.commit()
    db_connector.close()


results = parse_rarepepedirectory(pepe_names_list)
JSONTool.store_json_file(rarepepedirectory_list_file, results['urls'])
with open(misses_file, 'w') as f:
    for missed_pepe in results['misses']:
        f.write(missed_pepe)
