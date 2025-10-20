# 🔑 **API Keys Setup Guide**

**Complete guide to get all your API keys for GoodRunss integrations**

---

## ✅ **Already Completed**
- ✅ Stripe (you've added your keys)
- ✅ Google Maps (you've added your key)

---

## 📋 **What You Need to Add**

### **1. Google Services (Gmail + Calendar)** 🔴 PRIORITY

**Get from:** https://console.cloud.google.com/

**Steps:**
1. Go to Google Cloud Console
2. Create a new project (or select "GoodRunss")
3. Enable these APIs:
   - Gmail API
   - Google Calendar API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Application type: "Web application"
6. Add redirect URI: `http://localhost:8001/auth/google/callback`
7. Copy your **Client ID** and **Client Secret**

**Add to .env:**
```bash
GOOGLE_CLIENT_ID=your_actual_client_id_here
GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
```

---

### **2. Twilio SMS** 🔴 PRIORITY

**Get from:** https://console.twilio.com/

**Steps:**
1. Sign up for Twilio (free trial available)
2. Get your **Account SID** and **Auth Token** from dashboard
3. Get a Twilio phone number (free with trial)

**Add to .env:**
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

---

### **3. Instagram** 🟡 OPTIONAL

**Get from:** https://developers.facebook.com/apps/

**Steps:**
1. Create a Facebook Developer account
2. Create a new app
3. Add "Instagram Basic Display" product
4. Get your **App ID** and **App Secret**

**Add to .env:**
```bash
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret
```

---

### **4. Zoom** 🟡 OPTIONAL

**Get from:** https://marketplace.zoom.us/

**Steps:**
1. Sign up for Zoom Developer account
2. Create a "Server-to-Server OAuth" app
3. Get your **Account ID**, **Client ID**, and **Client Secret**

**Add to .env:**
```bash
ZOOM_API_KEY=your_zoom_client_id
ZOOM_API_SECRET=your_zoom_client_secret
ZOOM_ACCOUNT_ID=your_zoom_account_id
```

---

### **5. Snapchat** 🟡 OPTIONAL

**Get from:** https://kit.snapchat.com/

**Steps:**
1. Create Snapchat Developer account
2. Create a new app
3. Add "Login Kit" product
4. Get your **App ID** and **Client Secret**

**Add to .env:**
```bash
SNAPCHAT_APP_ID=your_snapchat_app_id
SNAPCHAT_CLIENT_SECRET=your_snapchat_client_secret
```

---

### **6. TikTok** 🟡 OPTIONAL

**Get from:** https://developers.tiktok.com/

**Steps:**
1. Create TikTok Developer account
2. Create a new app
3. Add "Login Kit" and "Share Kit"
4. Get your **Client Key** and **Client Secret**

**Add to .env:**
```bash
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
```

---

## 🎯 **Priority Order**

### **Must Have (Launch Essential):**
1. ✅ **Stripe** - Already done
2. ✅ **Google Maps** - Already done
3. 🔴 **Google (Gmail + Calendar)** - For bookings & notifications
4. 🔴 **Twilio** - For SMS notifications

### **Nice to Have (Post-Launch):**
5. 🟡 **Instagram** - Social sharing
6. 🟡 **Zoom** - Virtual training
7. 🟡 **Snapchat** - Viral growth
8. 🟡 **TikTok** - Viral growth

---

## 📝 **How to Add Keys**

### **Option 1: Use TextEdit (GUI)**
```bash
open -a TextEdit /Users/anthonyedwards/Backend2/.env
```
Then find the placeholder and replace it with your real key.

### **Option 2: Use Terminal (nano)**
```bash
cd /Users/anthonyedwards/Backend2
nano .env
```
Edit, then press `Ctrl+X` → `Y` → `Enter` to save.

---

## 🔄 **After Adding Keys**

**1. Save the .env file (Command+S in TextEdit)**

**2. Restart your server:**
```bash
# Kill existing server
kill $(lsof -t -i:8001)

# Start fresh
cd /Users/anthonyedwards/Backend2 && source venv/bin/activate && python main.py
```

**3. Verify integrations:**
```bash
curl http://localhost:8001/integrations/status
```

---

## ✅ **Verification Checklist**

After adding each key, check:
- [ ] Key is added to `.env` file
- [ ] No extra spaces or quotes around the key
- [ ] Server restarted
- [ ] Integration shows `"enabled": true` in status

---

## 🆘 **Troubleshooting**

**Integration still showing `enabled: false`?**
1. Check for typos in `.env`
2. Make sure no extra spaces
3. Restart server (kill and restart)
4. Check server logs for import errors

**Can't find `.env` file?**
```bash
cd /Users/anthonyedwards/Backend2
ls -la .env
```

---

## 💡 **Pro Tips**

1. **Start with Priority APIs first** - Get Gmail, Calendar, and Twilio working before social media integrations
2. **Test as you go** - Add one API, restart server, test, then move to next
3. **Free trials** - Most services offer free trials or developer tiers
4. **Security** - NEVER commit your `.env` file to GitHub (it's already in `.gitignore`)

---

**Need help? Your backend is at:** http://localhost:8001/docs



