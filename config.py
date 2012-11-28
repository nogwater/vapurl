# VapURL - Expiring URL service.
# Copyright (c) 2009 Aaron McBride and John Lawlor
# MIT License (see LICENSE.txt)
# https://github.com/nogwater/vapurl

import os

# base config info

try:
  is_dev = os.environ['SERVER_SOFTWARE'].startswith('Dev')
except:
  is_dev = False

if is_dev:
    baseURL = 'http://' + os.environ['HTTP_HOST'] + '/'
else:
    baseURL = 'http://vapurl.com/'
