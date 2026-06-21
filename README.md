# Support Desk — Ticket System

Ek mukammal support ticket system jisme **students sawal poochte hain** aur **admin (aap)
jawab dete hain**. Dono ka login alag hai aur har taraf apna data mehfooz hai.

## Is system mein kya hai

- Student signup/login — apna account khud banayen
- Student naya ticket (sawal) bana sakta hai, Normal ya Urgent priority k saath
- Student apni purani tickets dekh sakta hai aur unhi mein reply kar sakta hai
- Student apna **password khud badal sakta hai** (email change nahi ho sakta — security k liye)
- Admin login — sab tickets ek jagah dekhe (Open / Answered / Closed filter k saath)
- Admin har ticket par reply de sakta hai — reply dete hi status khud "Answered" ho jata hai
- Admin **Students** page se kisi bhi student ka email/naam dekh kar uska **password reset** kar sakta hai
- Ticket aur reply dono mein **file attach** kar sakte hain (image, PDF, Word doc, etc — 10MB tak)
- Ticket aur reply dono mein **voice note record** kar sakte hain (seedha browser se microphone use kar k)
- Ticket band (Closed) aur dobara khol (Reopen) karne ka option, dono taraf se
- Har data real database (SQLite) mein permanently save hota hai
- Ek **guaranteed default admin account** khud-ba-khud ban jata hai jab app pehli dafa chalta hai (neeche dekhein)

## Files ka khaka

```
support_ticket_system/
├── app.py                 # Pura backend logic (routes, database models)
├── requirements.txt       # Python packages ki list
├── Procfile                # Hosting platforms (Railway/Render) k liye
├── templates/              # Saare HTML pages
└── static/css/style.css    # Design
```

## Pehle apne computer par chala kar dekhein (optional)

```bash
cd support_ticket_system
pip install -r requirements.txt
python3 app.py
```

Phir browser mein `http://localhost:5000` kholein.

## Admin account kaise milega

Render k free plan mein "Shell" access nahi hota, is liye admin account **khud-ba-khud** ban jata hai jab app pehli dafa start hoti hai. Default details ye hain:

```
Email:    admin@supportdesk.com
Password: Admin@12345
```

**Zaroori:** Login hone k baad turant `/admin/students` se ya code mein change kar k password badal lein, taake koi aur is fix password se login na kar sake. Agar future mein aap k paas Shell access ho (paid Render plan ya kisi aur host par), to ye command se bhi naya admin bana sakte hain:

```bash
flask --app app.py create-admin
```

## Website par live kaise lagayen

Aap k paas ye aasan (aur muft) options hain. Sab se simple **Render.com** hai:

1. Ye saari files ek GitHub repository mein daal dein
2. [render.com](https://render.com) par account banayein aur "New Web Service" choose karein
3. Apni GitHub repo connect karein
4. Render khud `requirements.txt` aur `Procfile` dekh kar setup kar lega
5. Deploy hone k baad jo link milega, wahi aap ki live website hai
6. Terminal/Shell tab mein ja kar `flask --app app.py create-admin` chala kar apna admin account banayein

**Railway.app** aur **PythonAnywhere** bhi isi tarah kaam karte hain.

### Zaroori: SECRET_KEY set karein

Live website par jaane se pehle environment variable `SECRET_KEY` zaroor set karein
(ek lambi random string), warna sessions secure nahi rahenge. Render/Railway dono mein
ye "Environment Variables" section mein add ho jata hai.

## Database

Filhal SQLite use ho raha hai (ek file `instance/tickets.db` mein sab data save hota hai) —
ye school/institute level traffic k liye bilkul kaafi hai aur kisi alag setup ki zaroorat
nahi. Agar aage chal kar bohat zyada users ho jayen, to isi code ko PostgreSQL par
shift kiya ja sakta hai (sirf ek line `SQLALCHEMY_DATABASE_URI` badalni hogi).

## Customize karna

- Rang/design: `static/css/style.css` mein `:root` k variables badal dein
- Naam "Support Desk": `templates/base.html` mein `brand` class dhoond k apna institute
  ka naam likh dein
