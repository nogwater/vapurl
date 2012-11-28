# VapURL - Expiring URL service.
# Copyright (c) 2009 Aaron McBride and John Lawlor
# MIT License (see LICENSE.txt)
# https://github.com/nogwater/vapurl

from google.appengine.ext import db

class VapUrl(db.Model):
    name = db.StringProperty(multiline=False)
    link = db.LinkProperty() #db.StringProperty(multiline=False)
    vaporized = db.BooleanProperty()
    create_datetime = db.DateTimeProperty(auto_now_add=True)
    exp_datetime = db.DateTimeProperty()
    visits_max = db.IntegerProperty()
    visits_remaining = db.IntegerProperty()

class ErrorMessage(db.Model):
    text = db.StringProperty(multiline=True)
    create_datetime = db.DateTimeProperty(auto_now_add=True)

class Counter(db.Model):
    type = db.StringProperty(multiline=False)
    period_start_time = db.DateTimeProperty()
    count = db.IntegerProperty()