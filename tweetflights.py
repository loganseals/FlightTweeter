"""
This module will get the last flight tweeteed out by a provided Twitter account,
scrape the webpage that contains the flight history for the provided tailnumber, and
tweet out any new flights that have been completed.
"""

import tweepy
import flightscraper as fs
import time
import json

# These variables are used to create the WEBPAGE_ADDRESS for the history page of a plane with the provided
# tailnumber. Tailnumber replaced to prevent use.
TAILNUMBER = 'XXXXX'

# Replaced WEBPAGE_PREFIX to prevent use to scrape web data that goes against website user agreement.
WEBPAGE_PREFIX = 'XXXXXXXXXXX'
WEBPAGE_SUFFIX = '/history'

WEBPAGE_ADDRESS = WEBPAGE_PREFIX + TAILNUMBER + WEBPAGE_SUFFIX

# This is the number of tweets to get from the provided user's account.
MAX_RESULTS = 5

# These constants define how the tweets for each flight will look
# They are used in the _get_next_data_after_separator(), convert_flight_to_display_string(),
# and convert_display_string_to_flight() functions.
PREFIX = "***New Flight***\n\n"
DATE = "Date"
ORIGIN = "Origin"
DESTINATION = "Destination"
ARRIVAL = "Arrival"
DEPARTURE = "Departure"
DURATION = "Duration"
SEPARATOR = ": "


def __get_info_from_json_file(filename):
	"""
	Takes in a filename and returns the JSON data contained within the file.

	:param filename: The name of the file whose content contains JSON.

	:return: The JSON data contained in the provided file.
	"""

	try:
		with open(filename, "r") as file:
			info = json.load(file)

		return info

	except: 
		print("Unable to get authorization information from: %s" % filename)

def __get_next_data_after_separator_from_string(separator, str):
	"""
	Takes in a separator and a string that contains the separator argument. Returns the string that is after 
	the separator and before the next '\n' character, and the input string with everything
	from the beginning of the string to the first '\n' character removed.

	:param separator: A string to search the str param for and get the information after.

	:param str: The string to search for the separator param.

	:return: The string that is after the separator and before the next '\n' character if one exists, and
			 None if it does not exist. Also returns the string with all characters up to the first '\n'
			 character removed if it exists, and None if it does not exist.
	"""

	first_separator_index = str.find(separator)
	end_of_line_index = str.find('\n')

	if first_separator_index < 0:
		return None, None
	if end_of_line_index < 0:
		return str[first_separator_index + len(SEPARATOR):], ""
	if first_separator_index > end_of_line_index:
		return None, None

	return str[first_separator_index + len(SEPARATOR):end_of_line_index], str[end_of_line_index + 1:]

def __convert_flight_to_display_string(flight):
	"""
	Takes in a dict that contains the date, origin, destination, departure, arrival, and duration keys that
	hold the data for a particular flight. Returns the data in a string. This is directly connected
	with _convert_display_string_to_flight() function(they are inverses of each other). Any changes to this function
	should have an equal change in the _convert_display_string_to_flight() function.

	:param flight: A dict that contains the date, origin, destination, departure, arrival, and duration keys that
				   hold the data for a particular flight.

	:return: A string with the flight data.
	"""

	res = PREFIX

	res += DATE+SEPARATOR+flight["date"]+ '\n'
	res += ORIGIN+SEPARATOR+flight["origin"]+ '\n'
	res += DESTINATION+SEPARATOR+flight["destination"]+ '\n'
	res += DEPARTURE+SEPARATOR+flight["departure"]+ '\n'
	res += ARRIVAL+SEPARATOR+flight["arrival"]+ '\n'
	res += DURATION+SEPARATOR+flight["duration"]

	return res

def __convert_display_string_to_flight(str):
	"""
	Takes in a string containing the date, origin, destination, departure, arrival, and duration data for a particular flight. 
	Returns the corresponding data as a dict. This is directly connected
	with _convert_flight_to_display_string function(they are inverses of each other). Any changes to this function
	should have an equal change in the _convert_flight_to_display_string function.

	:param str: A string containing the date, origin, destination, departure, arrival, and duration data for a particular flight. 

	:return: Returns the flight data contained in the string as a dict or None if the provided string does not contain
			 the required PREFIX at the beginning.
	"""

	if not str.startswith(PREFIX):
		return None

	str = str[len(PREFIX):]

	flight = {}
	flight["date"], str = __get_next_data_after_separator_from_string(SEPARATOR, str)
	flight["origin"], str = __get_next_data_after_separator_from_string(SEPARATOR, str)
	flight["destination"], str = __get_next_data_after_separator_from_string(SEPARATOR, str)
	flight["departure"], str = __get_next_data_after_separator_from_string(SEPARATOR, str)
	flight["arrival"], str = __get_next_data_after_separator_from_string(SEPARATOR, str)
	flight["duration"], str = __get_next_data_after_separator_from_string(SEPARATOR, str)

	return flight

def __send_flight_tweets(client, flights):
	"""
	Takes in a tweepy client object, with consumer_key, consumer_secret from the developer account and the access_token, and access_token_secret
	of the account to tweet from already entered and a list of dicts that contain the flight information. The function will convert the
	flight dicts to strings, and then tweet them from the user's account.

	:param client: A tweepy client object, with consumer_key, consumer_secret from the developer account and the access_token, 
				   and access_token_secret of the account to tweet from already entered.

	:param flights: A list of dicts containing flight information of flights to be tweeted.

	:return: None
	"""

	for flight in flights:
		
		flight_string = __convert_flight_to_display_string(flight)

		try:
			response = response = client.create_tweet(text=flight_string)
		except:
			print("Unable to send tweet. Attempted to tweet flight:\n%s" % flight)
			return

def __get_last_flight(client, user_id):
	"""
	Takes in a tweepy client object with the developer account bearer_token already entered and the Twitter ID of the account
	to get the tweets from. Returns the last flight that was tweeted from the user's account as a dict that contains the
	flight information.

	:param client: A tweepy client object with the developer account bearer_token already entered and the Twitter ID of the account
	to get the tweets from.

	:param user_id: An integer or string that contains the Twitter ID of the account to get the recent tweets from.

	:return: A boolean that is False if the function was unable to access the Twitter API and True if it was able to access the
			 the Twitter API. A dict that contains the flight information of the last flight tweeted or None if the last tweets
			 do not contain flight information.
	"""

	try:
		response = client.get_users_tweets(id=user_id, max_results=MAX_RESULTS)
	except:
		print("Unable to get twitter account's last tweet.\n")
		return False, None

	for tweet in response.data:
		if tweet.text.startswith(PREFIX):
			last_flight = __convert_display_string_to_flight(tweet.text)
			return True, last_flight

	return True, None


def main():
	auth = __get_info_from_json_file('auth.json')

	client = tweepy.Client(consumer_key = auth["API_KEY"], 
						   consumer_secret = auth["API_KEY_SECRET"],
						   access_token = auth["ACCESS_TOKEN"],
						   access_token_secret = auth["ACCESS_TOKEN_SECRET"],
						   bearer_token = auth["BEARER_TOKEN"])

	result, last_flight = __get_last_flight(client, auth["TWITTER_ID"])
	if not result:
		return

	new_flights = fs.get_new_finished_flight_data(WEBPAGE_ADDRESS, last_flight)
	if new_flights == None:
		return

	__send_flight_tweets(client, new_flights)

main()

