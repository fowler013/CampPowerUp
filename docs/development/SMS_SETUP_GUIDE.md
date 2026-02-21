# SMS Setup Guide for Camp Power-Up Communication System

This guide will help you set up SMS functionality using Twilio for the Camp Power-Up communication system.

## 📱 Twilio Account Setup

### Step 1: Create a Twilio Account
1. Go to [twilio.com](https://www.twilio.com)
2. Click "Sign up for free"
3. Fill out the registration form
4. Verify your email address and phone number

### Step 2: Get Your Account Credentials
1. Log into your Twilio Console
2. From the dashboard, note down:
   - **Account SID** (starts with "AC...")
   - **Auth Token** (click the eye icon to reveal)

### Step 3: Get a Phone Number
1. In the Twilio Console, go to **Phone Numbers** > **Manage** > **Buy a number**
2. Choose your country and search for available numbers
3. Select a number that supports SMS
4. Complete the purchase (free trial includes credit)

## 🔧 Configure Camp Power-Up

### Option 1: Environment Variables (Recommended)
Set these environment variables in your system:

```bash
export TWILIO_ACCOUNT_SID="your_account_sid_here"
export TWILIO_AUTH_TOKEN="your_auth_token_here"
export TWILIO_PHONE_NUMBER="your_twilio_phone_number"
```

### Option 2: Direct Configuration
Edit the `SMS_CONFIG` in `communication/app.py`:

```python
SMS_CONFIG = {
    'account_sid': 'your_account_sid_here',
    'auth_token': 'your_auth_token_here',
    'from_number': '+1234567890'  # Your Twilio phone number
}
```

## 📋 Testing SMS Functionality

### Quick Test Script
Create a test script to verify SMS is working:

```python
from communication.app import SMSSender

# Initialize SMS sender
sms = SMSSender()

# Send a test SMS
success, message = sms.send_sms('+1234567890', 'Test SMS from Camp Power-Up!')
print(f"Success: {success}, Message: {message}")
```

### Test from Browser
1. Start the communication system: `python communication/app.py`
2. Go to `http://localhost:5000/send_message`
3. Select "📱 SMS Message"
4. Enter a test phone number in "Custom Phone Numbers"
5. Write a short test message
6. Click "📱 Send SMS Now"

## 🚨 Important Notes

### Phone Number Format
- Use international format: `+1234567890`
- The system will auto-format most US numbers
- Supported formats: `(555) 123-4567`, `555-123-4567`, `+1-555-123-4567`

### Message Limits
- **Character Limit**: 160 characters per SMS
- **Free Trial**: Twilio provides free credit for testing
- **Costs**: Check Twilio pricing for production usage

### Error Handling
- If Twilio credentials aren't configured, SMS will be simulated
- Check console logs for detailed error messages
- Invalid phone numbers will be rejected with clear error messages

## 🔍 Troubleshooting

### Common Issues

**"Twilio credentials not configured"**
- Verify your Account SID and Auth Token are correct
- Make sure environment variables are set properly
- Check that the credentials don't contain extra spaces

**"Invalid phone number"**
- Ensure phone numbers are in valid format
- Use international format (+1 for US numbers)
- Remove any special characters except +, -, (), and spaces

**"Authentication failed"**
- Double-check your Auth Token
- Ensure your Account SID is correct
- Try regenerating your Auth Token in Twilio Console

### Testing Without Real SMS
The system will simulate SMS sending if Twilio isn't configured, which is useful for:
- Development and testing
- Demonstrations
- When you don't have Twilio credits

## 💰 Pricing Information

### Twilio Costs (as of 2025)
- **US SMS**: ~$0.0075 per message
- **International SMS**: Varies by country
- **Phone Number**: ~$1.15/month for US numbers

### Free Trial
- Twilio provides free credit for new accounts
- Perfect for testing and small-scale usage
- Upgrade when ready for production

## 🔐 Security Best Practices

1. **Use Environment Variables**: Never commit credentials to code
2. **Rotate Tokens**: Periodically regenerate your Auth Token
3. **Monitor Usage**: Set up billing alerts in Twilio Console
4. **Validate Recipients**: Always validate phone numbers before sending

## 📞 Support

- **Twilio Documentation**: [twilio.com/docs](https://www.twilio.com/docs)
- **Twilio Support**: Available through their console
- **Camp Power-Up Issues**: Check console logs and error messages

---

🎉 **Your SMS system is now ready!** Parents can receive important camp updates, emergency notifications, and daily summaries via SMS.
