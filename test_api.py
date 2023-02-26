import os
import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.environ.get('OPENWEATHER_KEY')
TRIPADVISOR_KEY = os.environ.get('TRIPADVISOR_KEY')

def get_user_lat_lng():
    city = 'rochester'
    state = 'mn'
    endpoint = 'http://api.openweathermap.org/geo/1.0/direct'
    # params = {'q':location, 'appid':os.environ.get('OPENWEATHER_KEY')}
    test_url = f'http://api.openweathermap.org/geo/1.0/direct?q={city},{state},US&appid={API_KEY}'
    response = requests.get(test_url)
    lat = response.json()[0]['lat']
    lng = response.json()[0]['lon']
    lat_lng = f'{lat},{lng}'
    print(lat_lng)

# get_user_lat_lng()

# url = "https://api.content.tripadvisor.com/api/v1/location/nearby_search?latLong=44.016369%2C-92.475395&key=CE1248873AC44326A46432DBCF867E62&category=attractions&language=en"

# headers = {"accept": "application/json"}

# response = requests.get(url, headers=headers)
# print(response.json())

def search_nearby(category: str):
    '''User to extract location. Category for attractions or restaurants'''
    lat_lng = '44.0234387,-92.4630182'
    search_nearby_url = "https://api.content.tripadvisor.com/api/v1/location/nearby_search?"
    headers = {"accept": "application/json"}
    params = {'latLong':lat_lng, 'key':TRIPADVISOR_KEY, 'category':category, 'language':'en'}
    response = requests.get(search_nearby_url, headers=headers, params=params)
    location_ids = [loc_id['location_id'] for loc_id in response.json()['data']]
    loc_details = []
    for loc_id in location_ids:
        details_url = f"https://api.content.tripadvisor.com/api/v1/location/{loc_id}/details?language=en&currency=USD&key={TRIPADVISOR_KEY}"
        response = requests.get(details_url, headers=headers)
        loc_details.append(response.json())
    print(loc_details)
    
    return response.json()['data']

results = search_nearby('attractions')

print(results)
