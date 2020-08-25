import requests
from bs4 import BeautifulSoup
from dateutil import rrule
from datetime import datetime, timedelta
import json
import os

gist_id = os.getenv('GIST_ID')
github_token = os.getenv('GH_TOKEN')

yearly_price = 60000000
years = 4
total_price = yearly_price * years
price_per_year = total_price / 4
price_per_month = price_per_year / 12
price_per_week = price_per_month / 4
price_per_day = price_per_week / 7
price_per_hour = price_per_day / 24
price_per_minute = price_per_hour / 60
price_per_second = price_per_minute / 60
cost_tally = 0

tax_rate = 0.5
tax_rate_source = 'https://cepos.dk/abcepos-artikler/0246-en-almindelig-dansker-betaler-ca-50-pct-af-sin-loen-i-skatter-og-afgifter/'
average_income = 326048
average_income_source = 'https://www.dst.dk/da/Statistik/Publikationer/gennemsnitsdanskeren'
average_income_per_month = average_income / 12
average_hours_in_month = 140
average_income_per_hour = average_income_per_month / average_hours_in_month

now = datetime.now()
start = datetime(2019, 11, 1) # LOUD started to get funding from November 1st 2019

data = {
	'audience': [],
	'cost': [],
	'total_cost_so_far': rrule.rrule(rrule.WEEKLY, dtstart=start, until=now).count() * price_per_week,
	'price_per_hour': price_per_hour,
	'tax': {
		'rate': tax_rate,
		'source': tax_rate_source,
	},
	'income': {
		'average': average_income,
		'source': average_income_source,
		'hourly': average_income_per_hour
	},
}

def store_data(data):
	payload = {
		"files": {
			"loud.json": {
				"description": "testing",
				"filename": "loud.json",
				"content": json.dumps(data),
			}
		}
	}

	headers = {
		'Authorization': 'token ' + github_token,
		'Accept': 'application/vnd.github.v3+json',
	}
	r = requests.patch('https://api.github.com/gists/{}'.format(gist_id), json=payload, headers=headers)
	print('Status code', r.status_code)
	print('Response', r.json())
	return r.status_code


for dt in rrule.rrule(rrule.WEEKLY, dtstart=start, until=now):
	cost_tally += price_per_week
	
	data['cost'].append({
		'date': dt.isoformat(),
		'tally': cost_tally,
	})
	
	weekly_coverage = 0
	target_name = 'Radio Loud'
	url = 'http://tvm.tns-gallup.dk/tvm/rpm/{}/rpm{}{}.htm'.format(dt.year, str(dt.year)[:2], dt.isocalendar()[1])
	response = requests.get(url)

	if response.status_code != 200:
		continue

	soup = BeautifulSoup(response.text, 'html.parser')
	table = soup.findChildren(class_='list')[0]
	rows = table.findChildren(['tr'])
	for row in rows:
		name_cell = row.findChildren('td', class_='left')
		
		if not name_cell:
			continue

		if name_cell[0].text == target_name:
			cells = row.findChildren('td', class_='right')
			weekly_audience = (float(cells[0].text.replace(',', '.')) * 1000) + (float(cells[1].text.replace(',', '.')) * 1000)
			price = price_per_week
			
			if weekly_audience:
				price = price_per_week / weekly_audience

			data['audience'].append({
				'date': dt.isoformat(),
				'weekly_audience': weekly_audience,
				'price_per_audience': price,
			})
			continue

store_data(data)
