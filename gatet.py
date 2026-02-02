import random

def Tele(ccx):
    """Simulated card checker for testing"""
    try:
        ccx = ccx.strip()
        parts = ccx.split("|")
        
        if len(parts) < 4:
            return "Invalid format"
        
        card_num = parts[0]
        
        # Simulate different responses based on card number
        last_digit = card_num[-1] if card_num else '0'
        
        responses = {
            '0': 'Payment Successful!',
            '1': 'Card declined',
            '2': 'Insufficient funds',
            '3': 'Security code is incorrect',
            '4': 'Invalid card number',
            '5': 'Card expired',
            '6': 'Processing error',
            '7': 'Your card does not support this type of purchase',
            '8': 'Payment Successful!',
            '9': 'Declined'
        }
        
        result = responses.get(last_digit, 'Declined')
        
        # Add random delay to simulate processing
        import time
        time.sleep(random.uniform(0.5, 1.5))
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
