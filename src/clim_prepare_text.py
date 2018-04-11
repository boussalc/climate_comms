# This script take parsed utterances from com_hearings_parse.py and 
# completes meta-data acquisition.

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


