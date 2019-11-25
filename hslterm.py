#!/usr/bin/env python3

import requests
import json
import argparse
import string
import datetime
import pytz
from terminaltables import AsciiTable
from termcolor import colored, cprint

########## Function and constant definitions ####################################

API_URL= 'https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql'

def printBanner(banner_color, banner_bg_color): 
    print(colored(" _   _ _____ _       _____                   ", banner_color, banner_bg_color))
    print(colored("| | | /  ___| |     |_   _|                  ", banner_color, banner_bg_color))
    print(colored("| |_| \ `--.| |       | | ___ _ __ _ __ ___  ", banner_color, banner_bg_color))
    print(colored("|  _  |`--. \ |       | |/ _ \ '__| '_ ` _ \ ", banner_color, banner_bg_color))
    print(colored("| | | /\__/ / |____   | |  __/ |  | | | | | |", banner_color, banner_bg_color))
    print(colored("\_| |_\____/\_____/   \_/\___|_|  |_| |_| |_|", banner_color, banner_bg_color))
    print()

def fetch_stop_id(stop_number):
  stop_id_query_template = string.Template("""query {
    stops(name: "$stop_number") {
      gtfsId
      name
      code
      lat
      lon
    }
  }""")
  prepared_stop_id_query= stop_id_query_template.substitute(stop_number=stop_number)
  response = requests.post(API_URL, json={'query': prepared_stop_id_query})

  if(response.status_code == 404):
    raise Exception('Error while retrieving the stop ID')

  jsonResponse = json.loads(response.text)
  return jsonResponse['data']['stops'][0]['gtfsId']
  

def fetch_timetable(stop_id): 

  timetable_query_template = string.Template("""query {
    stop(id: "$stop_id") {
      name
        stoptimesWithoutPatterns {
        scheduledArrival
        realtimeArrival
        arrivalDelay
        scheduledDeparture
        realtimeDeparture
        departureDelay
        realtime
        realtimeState
        serviceDay
        headsign
        trip {
          route {
            shortName
          }
        }
      }
    }  
  }""")

  prepared_query = timetable_query_template.substitute(stop_id=stop_id)

  response = requests.post(API_URL, json={'query': prepared_query})
  return response

def parse_timetable(response):
  jsonData = json.loads(response.text)
  stop_name = jsonData['data']['stop']['name']
  departureTransports = jsonData['data']['stop']['stoptimesWithoutPatterns']
  
  transports = []

  for transport in departureTransports: 
    departure_time = transport['realtimeDeparture']
    service_day = transport['serviceDay']
    headsign = transport['headsign']
    route_code = transport['trip']['route']['shortName']
    transports.append(Transport(stop_name, route_code, headsign, service_day, departure_time))

  return transports

def print_schedule_for_stop(transports, color, background_color):
    table_data = [
        ['Route', 'Departure Time', 'Headsign'],
    ]

    for trnsprt in transports:
      table_data.append([trnsprt.route_code, trnsprt.get_departure_time(), trnsprt.headsign])

    table = AsciiTable(table_data)
    try:
      print(colored('+------- ' + transports[0].stop_name + ' -------+', color, background_color))
      print(colored(table.table, color, background_color))
    except KeyError:
      print('\nSomething funny with your color selection, couldn\'t display. Checkout ANSI terminal color codes.\n')
      print(table.table)
      pass

##############################################################

class Transport:

    local_tz = pytz.timezone('Europe/Helsinki')

    def __init__(self, stop_name, route_code, headsign, service_day, departure_time):
        self.stop_name = stop_name
        self.route_code = route_code
        self.departure_time = departure_time
        self.service_day = service_day
        self.headsign = headsign
    
    def get_departure_time(self):
        return self.get_current_day_midnight()
    
    def get_current_day_midnight(self):
        tz_aware_datetime = datetime.datetime.fromtimestamp(self.service_day + self.departure_time)
        localizedDateTime = pytz.utc.localize(tz_aware_datetime, is_dst=None)
        return localizedDateTime.strftime('%H:%M')

##############################################################

#### *** Main execution *** ####
parser = argparse.ArgumentParser(description='HSL Term - Terminal timetable for HSL (Helsingin Seudun Liikenne) transportations')
parser.add_argument('stop_ID', type=str, help='Stop number to query timetable for (eq. 1517) ')
parser.add_argument('-bc', type=str, help='Banner color (ANSI Color formatting) ')
parser.add_argument('-bbg', type=str, help='Banner background color (ANSI Color formatting) ')
parser.add_argument('-tc', type=str, help='Timetable color (ANSI Color formatting) ')
parser.add_argument('-tbg', type=str, help='Timetable background color (ANSI Color formatting) ')
args = parser.parse_args()

printBanner(args.bc, args.bbg)

try:
  stop_id = fetch_stop_id(args.stop_ID)
  response = fetch_timetable(stop_id)
  transports = parse_timetable(response)
  if(transports.count == 0):
    print('Zero results found')
  else:
    print_schedule_for_stop(transports, args.tc, args.tbg)
except Exception as err:
  print('Error habbened, ei viddu :DDD')
  print(err)
  pass