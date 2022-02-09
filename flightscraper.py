"""
This module contains the functions that will scrape flight date from the HTML of a 
provided webpage, and return any new flight data after the last flight provided.
"""

import urllib.request
from bs4 import BeautifulSoup

# Thie list is used to determine if a flight has been completed yet.
UNFINISHED = ['Scheduled', 'En Route']

def __add_space_between_time_and_timezone(time_strings):
	"""
	This function takes a generator object that contains strings holding a time and timezone and returns a string that
	contains the time and timezone separated by a space.

	:param time_strings: A generator object that contains strings holding a time and timezone.

	:return: a string containing the time and timezone from the time_strings param separated by a space.
	"""

	res = ""
	for string in time_strings:
		res += string
		res += ' '

	res = res[:-1]

	return res

def __get_html(flight_history_webpage):
	"""
	Makes an HTTP request to the provided webpage and returns the HTML of the webpage.

	:param flight_history_webpage:  The URL of the webpage to get the HTML from.

	:return: A string containing the HTML.
	"""

	try:
		html = urllib.request.urlopen(flight_history_webpage).read()
	except:
		print("Failed to get webpage: %s\n" % (flight_history_webpage))
		return

	return html

def __get_soup_from_html(webpage_request_result):
	"""
	Creates and returns a BeautifulSoup object from the HTML of the provided webpage.

	:param webpage_request_result: A string containing the HTML for a webpage.

	:return: A BeautifulSOup object created from the provided Response object.
	"""

	try:
		soup = BeautifulSoup(webpage_request_result, 'html.parser')
	except:
		print("Failed to load soup from html associated with webpage: %s\n" % (webpage_request_result.url))
		return

	return soup

def __get_airports_for_flight(flight):
	"""
	Uses the provided BeautifulSoup object that contains a table row for flight information and navigates the HTML
	to return the information of the origin and departure airports for the provided flight.

	:param flight: A BeautifulSoup object that contains a table row for flight information.

	:return: A list containing strings that represent the origin and destination for the flight.
	"""

	airports = flight.select('span[title]')

	if len(airports) == 0:
		return None, None

	return [airports[0]['title'], airports[1]['title']]

def __get_date_for_flight(flight):
	"""
	Uses the provided BeautifulSoup object that contains a table row for flight information and navigates the HTML
	to return the information of the date for the provided flight.

	:param flight: A BeautifulSoup object that contains a table row for flight information.

	:return: A string containing the date of the flight.
	"""

	date = flight.select('a[href]')

	if len(date) < 1:
		return

	return date[0].string

def __get_times_for_flight(flight):
	"""
	Uses the provided BeautifulSoup object that contains a table row for flight information and navigates the HTML
	to return the information on the departure and arrival times and the duration for the provided flight.

	:param flight: A BeautifulSoup object that contains a table row for flight information.

	:return: A list containing strings that represent departure time, arrival time, and duration of the flight.
	"""

	tabledata = flight('td')

	if len(tabledata) < 3:
		return None, None, None

	times = [tabledata[-3].stripped_strings, tabledata[-2].stripped_strings, tabledata[-1].string]

	# extract the time data from the departure and arrival <td> tags
	times[0] = __add_space_between_time_and_timezone(times[0])
	times[1] = __add_space_between_time_and_timezone(times[1])

	return times[0], times[1], times[2]

def __get_new_flight_data_from_soup(soup, previous_flight=None):
	"""
	Takes a BeautifulSoup object that contains the HTML of the webpage containing the flight history for an airplane
	and a dict containing a previous flight. Returns the relevant, recent flight information for flights that
	are new and have been completed. The returned flight information will be in order from oldest at index 0 to most recent at the last index.

	:param soup: A a BeautifulSoup object that contains the HTML of the webpage containing the flight history for an airplane
				 and a dict containing a previous flight.

	:param previous_flight: A dict containing the flight information for the last flight. Only flights that occur before the previous_flight
							 will be returned.

	:return: A list containing dicts with the relevant, recent flight information for flights that
			 are new and have been completed.
	"""

	flights_html = soup.select('tr[data-target]')

	if len(flights_html) == 0:
		print("Unable to find flight information on webpage. Check to see if the DOM has changed.\n")
		return

	flights = []

	for flight in flights_html:

		res = {}
		res["date"] = __get_date_for_flight(flight)
		res["origin"], res["destination"] = __get_airports_for_flight(flight)
		res["departure"], res["arrival"], res["duration"] = __get_times_for_flight(flight)

		for value in res.values():
			if value == None:
				print("Invalid flight information on webpage. Check to see if the DOM has changed.\nBad flight:\n%s" % res)
				return None

		if res["duration"] in UNFINISHED:
			continue

		if previous_flight != None:
			if previous_flight == res:
				break

		flights.append(res)

	flights.reverse()

	return flights


def get_new_finished_flight_data(flight_history_webpage, previous_flight = None):
	"""
	# Takes in the address for the history of a plane on XXXXX.com, and a dict containing information
	# for the last flight if there is one. Returns a list of dicts containing information on the flights
	# that have already been completed after the previous_flight.

	:param flight_history_webpage: The URL from XXXXX.com that contains the flight history for an airplane.

	:param previous_flight: A dict containing the flight information for the last flight recorded.

	:return: A list containing dicts with the relevant, recent flight information for flights that
		 are new and have been completed.
	"""

	res = __get_html(flight_history_webpage)
	if res == None:
		return

	soup = __get_soup_from_html(res)
	if soup == None:
		return

	recent_flights = __get_new_flight_data_from_soup(soup, previous_flight)
	if recent_flights == None:
		return

	return recent_flights