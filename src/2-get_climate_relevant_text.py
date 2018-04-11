# This script take parsed utterances from com_hearings_parse.py and keeps only climate relevant texts
# Also completes meta-data acquisition.

import re
from collections import defaultdict
from langdetect import detect
import codecs
import urllib
import dateparser
import pandas as pd
import glob
import os
import yaml
from libxml2mod import doc
from shutil import copyfile

## Get paths of climate-relevant parsed csvs.  
list_texts = glob.glob('/home/constantine/Dropbox/congress_committees/data/texts/text_*.htm')
list_mods = glob.glob('/home/constantine/Dropbox/congress_committees/data/mods/mods_*.xml')
list_parsed_utters = glob.glob('/home/constantine/Dropbox/congress_committees/data/parsed_utterances/parsed_*.csv')
doc_names = [re.search('parsed_utters_(.+?)_.+?.csv', text).groups()[0] for text in list_parsed_utters]
doc_dates = [re.search('parsed_utters_.+?_(.+?)\.csv', text).groups()[0] for text in list_parsed_utters]

def LoadRawText(file):
    raw_text = urllib.urlopen(file).read().decode("utf8")
    return raw_text

def DetectRawClimateDoc(text_file_path):
    climate_relevant = False
    text_file = LoadRawText(text_file_path)
    temp_text = text_file.replace('\n', ' ').lower()
    keys = ['climate change', 'global warming']
    if any(key in temp_text for key in keys):
        climate_relevant = True
    return climate_relevant

def DetectParsedClimateDoc(parsed_utter_file):
    climate_relevant = False
    df = pd.read_csv(parsed_utter_file)
    data = df.T.to_dict().values()
    temp_text = [row['text'].lower() for row in data]    
    temp_text = ' '.join(temp_text)
    temp_text = temp_text.replace('\n', ' ')
    keys = ['climate change', 'global warming']
    if any(key in temp_text for key in keys):
        climate_relevant = True
    return climate_relevant

def get_clim_parsed(list_parsed_utters):
    climate_relevant_parsed_files = []
    for doc in list_parsed_utters:
        climate_chk = DetectParsedClimateDoc(doc)
        if climate_chk == True:
            climate_relevant_parsed_files.append(doc)
            print doc
        else:
            pass
    return climate_relevant_parsed_files

def get_clim_texts(list_texts):
    '''
    Get file addresses of all raw texts that contain climate change related keywords
    '''
    climate_relevant_texts = []
    for doc in list_texts:
        climate_chk = DetectRawClimateDoc(doc)
        if climate_chk == True:
            climate_relevant_texts.append(doc)
            print doc
        else:
            pass
    return climate_relevant_texts

def get_unparsed_clim_texts(climate_relevant_texts, climate_relevant_parsed_files):
    '''
    Get file addresses of unparsed raw texts that are related to climate change
    '''
    parsed_names = []
    for file in climate_relevant_parsed_files:
        file_name = re.search('/parsed_utters_(.+?)_', file).groups()[0]
        parsed_names.append(file_name)
    all_climate_names = []
    for file in climate_relevant_texts:
        file_name = re.search('texts/text_(.+?)\.htm', file).groups()[0]
        all_climate_names.append(file_name)
    unparsed_names = list(set(all_climate_names) - set(parsed_names))
    unparsed_file_names = []
    for name in unparsed_names:
        new_file_name = '/home/constantine/Dropbox/congress_committees/data/texts/text_{}.htm'.format(name)
        unparsed_file_names.append(new_file_name)
    return unparsed_file_names

#===============================================================================
# Prepare climate-relevant text
#===============================================================================

# copy climate relevant parsed csvs to new folder

climate_relevant_parsed_files = get_clim_parsed(list_parsed_utters)

save_dir = '/home/constantine/Dropbox/congress_committees/data/climate_related/old_parsed'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

for doc_path in climate_relevant_parsed_files:
    name = re.search('parsed_utterances/(.+?)$', doc_path).groups()[0]
    src = doc_path
    dst = save_dir+'/{}'.format(name)
    copyfile(src, dst)


# copy climate related unparsed texts to new folder

climate_relevant_texts = get_clim_texts(list_texts)
unparsed_raw_texts = get_unparsed_clim_texts(climate_relevant_texts, climate_relevant_parsed_files)

save_dir = '/home/constantine/Dropbox/congress_committees/data/climate_related/old_unparsed'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

for doc_path in unparsed_raw_texts:
    name = re.search('texts/(.+?)$', doc_path).groups()[0]
    src = doc_path
    dst = save_dir+'/{}'.format(name)
    copyfile(src, dst)




