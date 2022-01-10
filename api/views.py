from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

import os
import json

from kiteconnect import KiteConnect

import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate(os.path.join( settings.BASE_DIR, 'static/key.json' ))

firestore_db = firestore.client()

kite = KiteConnect(api_key="5ov2hsy5honz4378")
data = kite.generate_session("request_token_here", api_secret="44431oahmqfznkrnw9tu25bdahgvt4c2")
kite.set_access_token(data["access_token"])
