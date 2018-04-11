# This script takes raw text and meta data.  Parses the text.
'''
https://drakon-editor.com/ide/doc/prassinos/2
'''

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

# Functions

def LoadRawText(file):
    raw_text = urllib.urlopen(file).read().decode("utf8")
    return raw_text

def GetRawLines(text):
    raw_match = text.split('\n')
    # Clean known problems  x
    raw_match = [line.replace(' [presiding].', '.') for line in raw_match] # remove term embedded within name of speaker
    raw_match = [line.replace(' [continuing].', '.') for line in raw_match] # remove term embedded within name of speaker
    raw_match = [line.replace(' [as translated].', '.') for line in raw_match] # remove term embedded within name of speaker
    raw_match2 = [[i,j] for i,j in enumerate(raw_match)]
    return raw_match2

def GetDocName(file):
    name = re.search('(CHRG-.+?)\.', file).groups()[0]
    return name

def SpeakerCheck(text):
    speaker_present = True
    regex = GetHonorificsRegexes()
    regex = regex.replace('^\s+', '') # fix for full html search
    #print regex
    if re.search(regex, text, re.S) == None:
        speaker_present = False
    return speaker_present

def SingleDayCheck(name):
    singleday = True
    hearing_info = GetHearingInfo(name)
    if hearing_info[2] > 1:
        singleday = False
    return singleday

def DateDelimCheck(lines):
    DateDelim_present = False
    regexs = ['\[Whereupon.+?$', '\[Recess\.\]', '\s{5}\s+.+?[0-9], [0-9]{4}\.$|\s{5}\s+.+?[0-9], [0-9]{4}$']
    regexs = '(%s)' % '|'.join(regexs)
    for line in lines:
        if re.search(regexs, line[1]) != None:
            DateDelim_present = True
            break
    return DateDelim_present

def GetHearingInfo(name):
    text_file_path = '/home/constantine/Dropbox/congress_committees/data/texts/text_{}.htm'.format(name)
    mods_file_path = '/home/constantine/Dropbox/congress_committees/data/mods/mods_{}.xml'.format(name)
    text_file = LoadRawText(text_file_path)
    mods_file = LoadRawText(mods_file_path)
    text_file_size = float(os.path.getsize(text_file_path))/float(1000) #size of text file in kilobytes
    # hearing information
    held_dates = re.findall('<heldDate>(.+?)</heldDate>', mods_file, re.S)
    held_dates_num = len(held_dates)
    chamber = re.search('<chamber>(.+?)</chamber>', mods_file, re.S).groups()[0]
    congress = re.search('<congress>(.+?)</congress>', mods_file, re.S).groups()[0]
    session = re.search('<session>(.+?)</session>', mods_file, re.S).groups()[0]
    brackets = re.findall('(\[.+?\])', text_file, re.S)
    adjourn_key = [bracket for bracket in brackets if re.search('Whereupon.+?adjourned|concluded|reconvene', bracket, re.S)]
    adjourn_key_num = len(adjourn_key)
    # climate change keyword dummy
    clim_dum = 0
    temp_text = text_file.replace('\n', ' ').lower()
    keys = ['climate change', 'global warming']
    if any(key in temp_text for key in keys):
        clim_dum += 1
    # detect date delimiter
    lines = text_file.split('\n')
    date_delims = [line for line in lines if re.search('\s{5}.+?[0-9], [0-9]{4}(?:\.$|$)', line, re.S)]
    date_delims = [line.strip() for line in date_delims]
    date_delims = f7(date_delims)
    date_delims_num = len(date_delims)
    # number of witness tags
    witness_tags = re.findall('<witness>(.+?)</witness>', mods_file, re.S)
    witness_tags_num = len(witness_tags)
    return [name, text_file_size, held_dates_num, held_dates, chamber, 
            int(congress), clim_dum, adjourn_key_num, date_delims_num, 
            witness_tags_num]

def GetCommMemberInfo(name):
    mods_file_path = '/home/constantine/Dropbox/congress_committees/data/mods/mods_{}.xml'.format(name)
    mods_file = LoadRawText(mods_file_path)
    congMemberChk = re.search('<congMember', mods_file, re.S)
    lnfChk = re.search('authority-lnf', mods_file, re.S)
    if congMemberChk == None:
        member_info = ['na', 'na', 'na', 'na', 'na', 'na']
        return member_info
    if lnfChk == None:
        member_info = GetBadXmlMeta(mods_file)
        return member_info
    member_info = GetGoodXmlMeta(mods_file)
    return member_info

def GetGoodXmlMeta(mods_file):
    member_info = []
    boxes = re.findall('<congMember(.+?)</congMember>', mods_file, re.S)
    for box in boxes:
        try:
            fullname  = re.search('authority-fnf">(.+?)</name>', box, re.S).groups()[0]
            last_name= re.search('authority-lnf">(.+?),', box, re.S).groups()[0]
            if re.search('bioGuideId=', box, re.S) == None:
                bioguide = 'na'
            else:
                bioguide = re.search('bioGuideId="(.+?)"', box, re.S).groups()[0]
            party = re.search('party="(.+?)"', box, re.S).groups()[0]
            state = re.search('state="(.+?)"', box, re.S).groups()[0]
            congress = re.search('congress="(.+?)"', box, re.S).groups()[0]
            chamber = re.search('chamber="(.+?)"', box, re.S).groups()[0]
            member_info.append([last_name, fullname, bioguide, party, state, congress, chamber])
        except:
            member_info = ['na', 'na', 'na', 'na', 'na', 'na']
            #print "Meta-data parsing error in {}".format(name)
    return member_info

def GetBadXmlMeta(mods_file):
    member_info = []
    party = "na"
    bioguide = "na"
    boxes = re.findall('<congMember(.+?)</congMember>', mods_file, re.S)
    for box in boxes:
        boxtext = box.replace(', Jr.', '')
        boxtext = boxtext.replace(' (I)', '')
        boxtext = boxtext.replace(' JR.', '')
        fullname = re.search('"parsed">(.+?) of', boxtext, re.S).groups()[0].title()
        last_name= re.search('\s([A-Za-z-]+$)', fullname, re.S).groups()[0]
        state = re.search('state="(.+?)"', box, re.S).groups()[0]
        chamber = re.search('chamber="(.+?)"', box, re.S).groups()[0]
        congress = re.search('congress="(.+?)"', box, re.S).groups()[0]
        member_info.append([last_name, fullname, bioguide, party, state, congress, chamber])
    return member_info

def FixBracketDateDelims(lines):
    nlines = []
    for x in xrange (len(lines)):
        if '[Whereupon' in lines[x][1] and ']' not in lines[x][1]:
            nline = lines[x][1] + lines[x+1][1]
            if ']' in lines[x+2][1]:
                nline = nline + lines[x+2][1]
                lines[x+2][1] = '[FIXED]'
            lines[x+1][1] = '[FIXED]'
            nlines.append([lines[x][0], nline])
        else:
            nlines.append(lines[x])
    return nlines

def GetHonorificsRegexes():
    honorifics = ['Mr\.', 'Ms\.', 'Mrs\.', 'Miss\.', 'Miss', 'Dr\.', 'Prof\.', 'Professor', 
                  'Rev\.', 'Rt\. Hon\.', 'Gen\.', 'General', 'Admiral', 'Adm.', 'Vice Admiral', 'Rear Admiral', 
                  'Fleet Admiral', 'Commander', 'Warrant Officer', 'Chief Warrant Officer', 'Sergeant', 'Sgt\.', 'Staff Sergeant', 
                  'Corporal', 'Cpl\.', 'Lance Corporal', 'Specialist', 'Spc\.', 'Master Sergeant',
                  'Chairman', 'Chairwoman', 'Mayor', 'Governor', 'Gov\.', 'Sgt\. Major', 
                  'Sgt\.', 'Lieutenant', 'Lt\.', 'Captain', 'Cpt.', 'Capt\.', 'Major', 'Maj\.', 
                  'Lieutenant Colonel', 'Lt\. Colonel', 'Colonel', 'Col.', 'Brigadier General', 
                  'Major General', 'Lt\. General', 'Lieutenant General', 'Lt\. Gen.', 'Sir', 'Lady', 'Viscount', 
                  'Lord', 'Senator', 'Congressman', 'Congresswoman', 'Secretary', 'Ambassador', 'Director', 'Undersecretary', 'Deputy Director']
    honorifics2 = ['The Chairman', 'The Chairwoman']
    hon_regexs = ['^\s+{}\s\w+\.'.format(title) for title in honorifics] # Last names with one token.
    hon_regexs2 = ['^\s+\d{1,3}\. '+str(title)+'\s\w+\.' for title in honorifics] # Last names in Q&A itemized list.
    hon_regexs3 = ['^\s+{}\s\w+\s\w+\.'.format(title) for title in honorifics] # Last names with two tokens.  Eg: "Ms. Wasserman Schultz"
    hon_regexs4 = ['^\s+{}\.'.format(title) for title in honorifics2]
    hon_regexs.extend(hon_regexs2)
    hon_regexs.extend(hon_regexs3)
    hon_regexs.extend(hon_regexs4)
    combined = '(%s)' % '|'.join(hon_regexs)
    return combined

def f7(seq): # To remove duplicates while preserving order
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def GetDateDelimType(lines):
    bracket_delim_present = False
    for line in lines:
        if '[Whereupon' in line[1]:
            bracket_delim_present = True
    return bracket_delim_present

def GetDateDelims(lines):
    ddlines = [] #date delimiter lines
    for line in lines:
        lline = line[1].lower()
        regx_committee = re.search("\[whereupon.+?(?:committ|subcom|mittee|hearing|task force|roundtable|meeting|panel|briefing|matter)", lline, re.S)
        regx_same_day = re.search("(?:same day)", lline, re.S)
        if regx_committee != None and regx_same_day == None:
            ddlines.append(line)
    return ddlines

def GetSimpleDateDelims(lines):
    ddlines = []
    for line in lines:
        lline = line[-1].lower()
        if re.search("\[whereupon", lline, re.S) != None:
            ddlines.append(line)
    return ddlines

def OkDateDelimCheck(ddlines, meta_data):
    ddlines_ok = False
    if len(ddlines) == meta_data[2]:
        ddlines_ok = True
    return ddlines_ok

def ChunkTextDateDelims(lines, ddlines):
    dd_text_chunks = []
    for x in xrange(len(ddlines)):
        temp_text = []
        current_date_delim = ddlines[x]
        current_is_first = False
        if current_date_delim == ddlines[0]:
            current_is_first = True
        else:
            pass
        if current_is_first == True:
            for line in lines:
                if line[0] <= current_date_delim[0]:
                    temp_text.append(line[1])
        else:
            prev_date_delim = ddlines[x-1]
            for line in lines:
                if line[0] > prev_date_delim[0] and line[0] <= current_date_delim[0]:
                    temp_text.append(line[1])
        temp_text = '\n'.join(temp_text)
        dd_text_chunks.append(temp_text)
    return dd_text_chunks

def GetChunkDates(name, meta_data, dd_text_chunks):
    chunk_dates = []
    meta_dates = meta_data[3]
    for x in xrange(len(dd_text_chunks)):
        chunk_dates.append([name, meta_dates[x], dd_text_chunks[x]])
    return chunk_dates

def GetDocDate(name, meta_data, text):
    chunk_dates = [name, meta_data[3][0], text]
    return [chunk_dates]

def GetLines(text_date):
    text = text_date[2].split('\n')
    text = [line.replace(' [presiding].', '.') for line in text] # remove term embedded within name of speaker
    text = [line.replace(' [continuing].', '.') for line in text] # remove term embedded within name of speaker
    text = [line.replace(' [as translated].', '.') for line in text] # remove term embedded within name of speaker
    lines = [[text_date[0], text_date[1], i, j] for i,j in enumerate(text)]
    return lines

def GetSpeakerDelims(lines):
    combined = GetHonorificsRegexes()
    speaker_delims = []
    for line in lines:
        if re.match(combined, line[-1]):
            speaker_delims.append(line)
    speaker_delims = [line for line in speaker_delims if '......' not in line[-1]]
    return speaker_delims

def GetStatementDelims(lines):
    regex = '(^.+?follows.\]|^.+?follow.\])'
    statement_delims = []
    for line in lines:
        if re.match(regex, line[-1]):
            statement_delims.append(line)
    return statement_delims

def GetUtters(speaker_delims, statement_delims, ddlines, lines):
    utter_lines = []
    for x in xrange(len(speaker_delims)):
        temp_text = []
        current_speaker = speaker_delims[x]
        speaker_is_last = False
        if current_speaker == speaker_delims[-1]:
            speaker_is_last = True
        if speaker_is_last == False:
            current_speaker_start = current_speaker[2]
            next_speaker = speaker_delims[x+1]
            for line in lines[current_speaker_start:]:
                if line is not next_speaker and line not in statement_delims:
                    temp_text.append(line[-1])
                else:
                    break
        else:
            current_speaker_start = current_speaker[2]
            for line in lines[current_speaker_start:]:
                if len(ddlines) > 0:
                    if line not in statement_delims and line is not ddlines[-1]:
                        temp_text.append(line[-1])
                    else:
                        break
                else:
                    if line not in statement_delims:
                        temp_text.append(line[-1])
                    else:
                        break
        temp_text = ' '.join(temp_text)
        utter_lines.append(temp_text)
    return utter_lines

def GetStatements(speaker_delims, statement_delims, lines):
    statement_lines = []
    for x in xrange(len(statement_delims)):
        temp_text = []
        current_statement = statement_delims[x]
        statement_is_last = False
        if current_statement == statement_delims[-1]:
            statement_is_last = True
        if statement_is_last == False:
            current_statement_start = current_statement[2]
            next_statement = statement_delims[x+1]
            for line in lines[current_statement_start:]:
                if line is not next_statement and line not in speaker_delims:
                    temp_text.append(line[-1])
                else:
                    break
        else:
            current_statement_start = current_statement[2]
            for line in lines[current_statement_start:]:
                if line not in speaker_delims:
                    temp_text.append(line[-1])
                else:
                    break
        temp_text = ' '.join(temp_text)
        statement_lines.append(temp_text)
    return statement_lines


def SaveEvalCopy(lines_of_eval_text):
    save_path = '/home/constantine/Dropbox/congress_committees/data/evaluation/evalcopy_{}.csv'.format(name)
    labels = ['evaluation_text']
    df = pd.DataFrame(lines_of_eval_text, columns=labels)
    df.to_csv(save_path, encoding='utf-8', index=False)
    print "Evaluation text written to disk at:  {}".format(save_path)

def GetCleanUtters(utterances, comm_members, name, date):
    cleaned_utterances = []
    hon_regex = GetHonorificsRegexes()
    for text in utterances:
        extracted_speaker = re.search(hon_regex, text, re.S).groups()[0].strip()
        extracted_speaker = re.sub('\d{1,3}\.\s', '', extracted_speaker)
        extracted_speaker_ln = re.search('\s(.+?)\.', extracted_speaker).groups()[0] #last name
        new_text = text.replace(extracted_speaker, '')
        new_text = re.sub(' +', ' ', new_text)
        #new_text = re.sub('\[.+?\]', '', new_text)
        if ' [Deleted.] [Deleted.] ' in new_text:
            new_text = '[Deleted.]'
        other_junk = ['<GRAPHIC(S) NOT AVAILABLE IN TIFF FORMAT>']
        [new_text.replace(junk, '') for junk in other_junk] # remove other junk text
        for member in comm_members:
            if extracted_speaker_ln == member[0]:
                matched_comm_member = member
                break
            else:
                matched_comm_member = ['na', 'na', 'na', 'na', 'na', 'na', 'na']
        cleaned_utterances.append([name, date, extracted_speaker_ln, extracted_speaker, matched_comm_member[1], matched_comm_member[2], 
                                   matched_comm_member[3], matched_comm_member[4], matched_comm_member[5], matched_comm_member[6], new_text])
    return cleaned_utterances

def SaveUtters(clean_utterances, name, date):
    save_path = '/home/constantine/Dropbox/congress_committees/data/parsed_utterances/parsed_utters_{}_{}.csv'.format(name, date)
    labels = ['filename', 'date', 'last_name', 'extracted_name', 'full_name', 'bioguide', 'party', 'state', 'congress', 'chamber', 'text']
    df = pd.DataFrame(clean_utterances, columns=labels)
    df.to_csv(save_path, encoding='utf-8', index=False)

def SaveStatements(statements, name, date):
    save_path = '/home/constantine/Dropbox/congress_committees/data/parsed_statements/parsed_statements_{}_{}.csv'.format(name, date)
    labels = ['statements']
    df = pd.DataFrame(statements, columns=labels)
    df.to_csv(save_path, encoding='utf-8', index=False)

def WriteError(error_type, error_description, name):
    path = '/home/constantine/Dropbox/congress_committees/data/parsed_errors/'
    file = open(path+'{}_{}.txt'.format(error_type, name), 'wb')
    file.write(error_description)
    file.close

def ImportYamlData(yaml_file_dir):
    with open(yaml_file_dir, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

def GetGitBios(list_of_bio_files):
    meta = ImportYamlData(list_of_bio_files[0])
    for file in list_of_bio_files[1:]:
        meta_historical = ImportYamlData(file)
        meta.extend(meta_historical)
    return meta

def Parse(names, git_bio_files):
    print "Loading GitHub @unitedstates congress-legislators bio files ..."
    #git_bios = GetGitBios(git_bio_files)
    print "GitHub @unitedstates congress-legislators data loaded."
    utter_data = []
    for count, name in enumerate(names, 1):
        if count % 1000 == 0:
            pcomplete = (float(count) / float(len(names)))*100
            print "{}% Complete.".format(pcomplete)
        print name
        file = '/home/constantine/Dropbox/congress_committees/data/texts/text_{}.htm'.format(name)
        text = LoadRawText(file)
        name = GetDocName(file)
        meta_data = GetHearingInfo(name)
        comm_members = GetCommMemberInfo(name)
        #check if there are speakers in the text.  If not, error1 (no information).
        speaker_present = SpeakerCheck(text)
        if speaker_present == False:
            error_type = 'Error1'
            error_description = 'The file does not contain a speaker. This is likely not a transcript. Discard.'
            WriteError(error_type, error_description, name)
            #print '{} for file {}'.format(error_type, name)
            continue
        #check if the transcript covers a single day.  If not, clean.  Else, begin parsing.
        single_day = SingleDayCheck(name)
        if single_day == False:
            lines = GetRawLines(text)
            lines = FixBracketDateDelims(lines)
            #check if date delimiters are present in the transcript.  If none, error2 (need to manually parse).
            date_delim_present = DateDelimCheck(lines)
            if date_delim_present == False:
                error_type = 'Error2'
                error_description = 'The transcript contains information over multiple days, but there are no bracketed date delimiters. Need to manually parse.'
                WriteError(error_type, error_description, name)
                #print '{} for file {}'.format(error_type, name)
                continue
            ddlines = GetDateDelims(lines)
            #check if number of extracted date delimiter matches number of days from meta-data.  If not, error3 (need to manually parse).
            ddlines_ok = OkDateDelimCheck(ddlines, meta_data)
            if ddlines_ok == False:
                error_type = 'Error3'
                error_description = 'The transcript contains information over multiple days, and it also contains bracketed date delimiters. However, the number of days in the meta data do not match the number of date delimiters. Need to manually parse.'
                WriteError(error_type, error_description, name)
                #print '{} for file {}'.format(error_type, name)
                continue
            dd_text_chunks = ChunkTextDateDelims(lines, ddlines)
            text_date = GetChunkDates(name, meta_data, dd_text_chunks)
        else:
            text_date = GetDocDate(name, meta_data, text)
        for text in text_date:
            date = text[1]
            lines = GetLines(text)
            speaker_delims = GetSpeakerDelims(lines)
            statement_delims = GetStatementDelims(lines)
            ddlines = GetSimpleDateDelims(lines)
            #Get Utterances
            utterances = GetUtters(speaker_delims, statement_delims, ddlines, lines)
            clean_utterances = GetCleanUtters(utterances, comm_members, name, date)
            SaveUtters(clean_utterances, name, date)
            utter_data.append(clean_utterances)
            #Get Statements
            statements = GetStatements(speaker_delims, statement_delims, lines)
            SaveStatements(statements, name, date)

#===============================================================================
# PARSE FILES
#===============================================================================
git_bio_files = ['/home/constantine/Dropbox/congress_committees/src/legislators-current.yaml', 
                     '/home/constantine/Dropbox/congress_committees/src/legislators-historical.yaml']
list_texts = glob.glob('/home/constantine/Dropbox/congress_committees/data/texts/text_*.htm')
names = [re.search('text_(.+?).htm', text).groups()[0] for text in list_texts]
names = [name for name in names if 'GPO-' not in name]
Parse(names, git_bio_files)
