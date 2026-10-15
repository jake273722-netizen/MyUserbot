import os
import time
import random
import logging
import asyncio
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

# Dummy Web Server (Render Port Checker အတွက်)
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Background Thread အဖြစ် run ပေးခြင်း
threading.Thread(target=run_web_server, daemon=True).start()

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = "8642880112:AAEbnxIKjLmPmHTFUC5mGlihSiAKLFey1zA".strip()

# ✨ Main Admin ID 
MAIN_ADMIN_ID = 8986922249
MAIN_ADMIN_USERNAME = "hyungV1"  # 👈 မင်းရဲ့ Telegram Username

# 📂 Admin IDs များကို ဖိုင်ထဲတွင် သိမ်းဆည်းရန် (Render Restart ဖြစ်လျှင်လည်း မပျောက်စေရန်)
ADMIN_FILE = "admins.json"

def load_admins():
    if os.path.exists(ADMIN_FILE):
        try:
            with open(ADMIN_FILE, "r") as f:
                data = json.load(f)
                return set(data)
        except Exception as e:
            logging.error(f"Error loading admins: {e}")
    return {MAIN_ADMIN_ID}

def save_admins():
    try:
        with open(ADMIN_FILE, "w") as f:
            json.dump(list(ADMIN_IDS), f)
    except Exception as e:
        logging.error(f"Error saving admins: {e}")

# Bot ကို သုံးခွင့်ရှိသူတွေရဲ့ Admin IDs စာရင်း
ADMIN_IDS = load_admins()
ADMIN_IDS.add(MAIN_ADMIN_ID) # Main Admin အမြဲပါဝင်စေရန်

# Global State Variables (Group တစ်ခုချင်းစီအလိုက် ခွဲသိမ်းရန် ပြင်ဆင်ထားသည်)
targets = {}             
is_running = True           

del_targets = {}
mt_targets = {}             
mt_tasks = {}              
mt_delay = 2.0              

user_flow_state = {}

Replies = [
    "ဖာသည်မသားလေးရယ် သေချာကိုက်လေ",
    "မင်းအမေသေတဲ့အကြောင်းတွေ ပြောနေတာလား",
    "ဖာသည်မသား မင်းမေအသုဘ လူမစီဘူးလား",
    "မင်းမေဖာသည်မဆိုတာ ငါကော ဘုရားကောသိတယ်",
    "ထိထိမိမိကိုက်လေ မအေလိုးခွေး",
    "နရင်းဖျက်ရိုက်လိုက်လို့ မူးပြီးကိုမေကိုလိုးသွားမယ်",
    "မင်းဘာလို့လန့်နေတာတုန်းဟ ခုမှအစပဲရှိသေးတာ",
    "သေချာကိုက်ထားငါကတော့ နာနာရိုက်မှာ မင်းလိုခွေးကို",
    "ဘယ်သူနိုင်လည်း စောင့်ကြည့်စရာမလိုဘူး ပွဲစကတည်းက ငါက အနိုင်ဘက်က",
    "ငါလိုးမခွေး မင်းမေစပဖြစ်တာလား",
    "သေချာကိုက်ပါဆို အဆွယ်ကျိုးပြနေတာလား",
    "မင်းမေစောက်ဖုတ် ငါလိုးမိသေးလား",
    "ကိုက်ထားလေရိုက်ဖားလေး",
    "မင်းဘဝကတုံးအောက်ကဖားပဲ",
    "မင်းက နူနေတာလား အနူမသား",
    "ပျော့လိုက်တဲ့ခွေး အပျင်းကိုမပြေဘူး",
    "ဖာသည်မသားလေး မင်းမေခွေးလိုးသွားတာလား",
    "ငါလိုးမစောက်ခြောက် မင်းဘာလို့ နွဲ့ပြနေတာလဲ",
    "တပည့်ကျော် တဘော်ကျဲ့ ကိုက်ထားမယ်",
    "အရမ်းကောင်းနေလည်း ဒုတိယပဲရမယ် ဖာသည်မသား",
    "ငါနိုင်နေတာလား အမြဲအနိုင်ပိုင်းနေတော့ ပျင်းနေပြီ",
    "ဖာသည်မသားလေးရယ်သေချာကိုက်လေ ဘာလို့ ငိုင်နေတာလဲ",
    "ငါက god လေ မင်းကတော့ dog ငါ့ချီးပဲစားနေ",
    "မင်းမာန်ဆွယ်လေးထုတ်ပြစမ်း မအေလိုး",
    "မင်းစောက်ရုပ်ကြီးဘာလို့ဆိုးနေတာလဲ စောက်ရုပ်ဆိုးကောင်",
    "မင်းမေစပထဲဝင်ပြေးမယ်မကြံနဲ့ သေချာကိုက်",
    "ငါက သခင်လေ မင်းကတော့ သမင်ပေါ့ ငါအမဲလိုက်တာပဲခံနေရမှာ",
    "ပြေးနိုင်သလောက်ပြေး ဘယ်လိုပြေးပြေး မင်းလွှတ်လမ်းမရှိဘူး",
    "မင်းအမေ အေကိုက်သေတာဆို",
    "ဖာသည်မကြီးရဲ့သား ဘာကျစ်တာလဲ",
    "လီးတောင့်နေပြီ မင်းအမေဖာသည်မစောက်ပါးစပ်လိုနေနတာ",
    "ဖာသည်မသား မင်းမေစောက်ခွက်ကိုသေးနဲ့ပန်းမယ်",
    "ငိုမနေနဲ့ မသနားဘူးငါက",
    "ကိုမေကိုလိုးလေး ကြိတ်ကြွေနေတာလား ငါ့ flow တွေက",
    "ဟိတ်ကောင် မအေလိုးခွေး",
    "မင်းမိဘငါလိုးတယ် ဘာဖြစ်လဲ",
    "အူကြောင်ကြားနဲ့ မအူမလည်နွားလုပ်မနေနဲ့",
    "တောသားလိုလို ဝဲစားလိုလိုနဲ့ အနူလက်နဲ့ခွေး",
    "မင်းကိုဆဲနေတာဖာသည်မသားရ ဘာလို့ကြောင်ကြည့်နေတာလဲ",
    "လန့်နေတာလား ငါ့ကို",
    "ဖာသည်မသားပေါက်စ",
    "မအေလိုးလေး သေချာလေးကိုက်ကြည့်ပါလား",
    "ငါပြန်ကိုက်မယ် မင်းအမေနို့သီးခေါင်းကို",
    "ကိုက်လေ ဖာသည်မသား",
    "မင်းမေစောက်ဖုတ်ကို ကုန်းယက်နေတာလားမင်းက",
    "ခွေးကြီး ခွေးလို အူပြစမ်း ခွေးမသား",
    "ဘာလို့ ခွေးဖြစ်ပြီး အူရမှာရှက်နေတာလဲ",
    "မင်းက သေချာကိုက် ငါက ဂဲနဲ့ထုမယ်",
    "အများကတော့ငါ့ကိုအရိုက်ဘုရင်လို့ပေးထားတာပဲမင်းငါ့ကိုနိုင်ချင်ရင်သေချာကိုက်မှရမယ်",
    "အဆွယ်ကျိုးကြီးနဲ့ မာန်ဖီပြမနေနဲ့",
    "ဖာသည်မသားခွေး မင်းကခွေးမသားလား",
    "မအေလိုးလေး သေချာကိုက်လိုက်ပါတော့လား",
    "မင်းဘာလို့ လက်မြှောက်ဒူးထောက်လုပ်နေတာလဲ",
    "မင်းအညံ့ခံလည်း ငါ့တပည့်အဖြစ်မခန့်ဘူး",
    "တောသားလိုလိုပွဲစားလိုလိုငါရှေ့မှာဂယောက်ဂယက်နဲ့လာလုပ်မနေနဲ",
    "ယောကျာ်းကြီးဖြစ်ပြီအခြောက်စိတ်ကိုစွန့်ပယ်ကြိုးစားချင်စိတ်မွေး",
    "ဖာသည်မသားကလေးကလားနဲ့လီးဖြစ်တာလားစောက်တောသားအထာမကျပဲလာတုပနေတယ်",
    "မင်းအခုခွေးလိုနွားလိုအဆဲခံနေရတာတောင်အ‌စွဲတောင်ချင်နေသေးတယ",
    "Text နဲ့စာရိုက်နေတာကိုထိလည်းမထိဘူးတဲ့ ဦးနှောက်ကြွက်ကိုက်ထားသလား ဂေါက်သီး ထိချင်ရင်လာခဲ့",
    "မင်းအမေဖင်ညိုညိုကြီးကို ငြင်ငြင်လေးနဲ့ဘုပေးလိုက်ပြီ",
    "ဟိတ်ကောင်မင်းအမေစောက်ဖုတ်ကိုထွန်းရွှေဝါလူးပီးသုတ်လိုးလိုးပေးမယ်ပူစပ်စပ်ဖြစ်နေအောင်",
    "ကန်ချက်တွေက အရမ်းပြင်းနေလို့ မခုခံနိုင်ဘူးလား ဖာသည်မသား",
    "မျက်လုံးကိုမှိတ်ထားငါ့ဆီကထွက်လာတဲ့auraတွေကိုမင်းခံနိုင်ရည်မရှိမှာဆိုးလို့",
    "ဖာသည်မရဲ့သားဝူးတူးတူးမလုပ်နဲ့ဖျက်ကန်လိုက်မယ်",
    "တော်တီနောင်တော်တီနောင်မင်းအမေဖင်ကြီးကပြောင်",
    "မင်းအမေအိကျိကြီး ငါစို့တယ်ဘာဖြစ်လဲ",  
    "မင်းအဖေခွေးကြီးကိုသွားပြောလေအက်တာ",
    "ငေးမနေနဲမင်းအမေဖာသည်မဆုံးပြီ",
    "ဟျောင့်ဖာသည်မသားကိုက်လိုက်တာလား",
    "မင်းစောက်ဆင့်နဲ့ပါးစပ်တောင်မဟနဲ့လက်နောက်ပြစ်ထား",
    "ဟိတ်ကောင်မအေလိုး၁၂၃ဆိုတာနဲ့ကိုယ်မေကိုယ်ပြန်လိုးဖို့အဆင်သင့်ပြင်ထားတော့",
    "ခွေးဝဲစားမသားကိုက်အားပျော့လှချည်လားကွ",
    "မင်းအမေကသာငါ့အပေါ်တက်ခွတာပါတပည့်",
    "မင်းရဲ့စောနကအစွယ်တွေဘယ်ဖျောက်လိုက်တာလဲဘောမ",
    "မအေလိုးပေါ်ပြူလာဖြစ်ချင်တာလားဒေါ်မူယာကမင်းအမေဆို",
    "မအေလိုးဝက်ကိုက်မှာသာကိုက်စကားပလ္လင်ခံမနေနဲ့နောက်ဆုံးမင်းဒီဘူတာပဲဆိုက်မှာ",
    "မအေလိုးခွေးမင်းအမေခွေးလိုးလိုက်လို့မင်းပါစိတ်မနှံ့တဲ့ခွေးဖြစ်တာဆို",
    "မင်းအမေဖင်ထဲငါ့လီးစိုက်ဝင်သွားလို့ရပ်ကွက်တကာအော်ကြီးဟစ်ကျယ်နဲ့လျှောက်အော်နေတာလားမအေလိုးရ",
    "မင်းစောက်ဦးနှောက်တစ်ခြမ်းပုတ်နေတာလား",
    "ငါကမင်းရန်သူမဟုတ်ဘူးမင်းမိတ်ဆွေမင်းအမေကိုလိုးမယ့်မိတ်ဆွေ",
    "1234ဆိုတာနဲ့ မင်းအမေစောက်ပတ်ကိုဖြဲထား ငါကအားနဲ့ပြေးလိုးမယ်",
    "ခွေးမသားသတ္တိရှိရင်မင်းအမေဖာသည်မကိုအော်ဆဲပြလိုက်ပါလား",
    "မင်းစကားအရမ်းများတယ်ငါ့လီးငုံထားပါလား",
    "ဟာလန့်တာမင်းအမေမင်းထလိုးတော့ငါလည်းလန့်တာပေါ့",
    "Telegram မှာ ငါဆရာပဲ မင်းအမေကိုလိုးတယ်ကွာ ဘယ်သူဘာပြောမလည်း",
    "မင်းမေစဖုတ်ကိုဆင်စီးပြီးမီးထုတ်ရမ်းဝင်တာတောင်မိူင်းမဆွံဘူးဆိုမအေလိုး",
    "အေးဒါဆိုလိပ်စာပြောမင်းအမေ ကို deliနဲ့ လှမ်းလိုးးခိုင်းပလိုက်မယ်",
    "ငါလိုးမခွေးအခြောက်လိုကိုက်မနေနဲ့ယောက်ကျားလိုဖိုက်",
    "မင်းအမေဖာသယ်မကြီးကို ဖာတန်းကပြန်ခေါ် နောက်ပီးရင် ဘိုးဘွားရိပ်သာပို့စမ်း",
    "ငါပြောတဲ့စာသားတွေကမင်းအတွက်အထီးကျန်ဆန်မူနဲ့ပြတ်သားနေတာမင်းဘာလိုတုံပြန်ရခက်နေတာလဲ",
    "ဖာသည်မသားယောင်ခြောယ်ကောင် မင်းဘွားအေငါလိုး",
    "စောက်ရူးရာ ကိုက်မယ်ဆိုသေချာကိုက် မထိတထိနဲ့လာမညှောင်နဲ့",
    "အဲ့တာမင်းမေဖာသည်မနာရေးဖိတ်စာလား",
    "အတွေးကမင်းမေလိုးတဲ့အ‌တွေးပဲရှိတာလား",
    "မင်းမေဖာသည်မကိုအများနဲ့ရောလိုးမယ်",
    "ဖာသည်မရဲ့သားဝူးတူးတူးမလုပ်နဲ့ဖျက်ကန်လိုက်မယ်",
    "ဟေ့ရောင်ဖာသည်မသား ခေါ်ရင်သေချာ‌ထူးကွာ မထူးရင်မင်းအမေစဖုတ်ထဲငါ့လီးစိမ်ထားရလိမ့်မယ်",
    "ဘာတွေလျှောက်ရေးနေတာ စောက်ရူးအကွပ်နက်",
    "မင်းမာန်စွယ်လေး ထုတ်ပြစမ်း ဖာသည်မသား",
    "ဖာသည်မသားလီးလိုနားတာလား",
    "ဖာသည်မသားဆိုဆက်တိုက်ကိုက်",
    "ငါလိုးမ ဖာသည်မ‌အကြီးစားရဲ့သားမင်းမိဘငါလိုးတော့ဘာကျစ်လို့လဲဟ",
    "အဲ့တာမင်းမေဖာသည်မနာရေးဖိတ်စာလား",
    "အတွေးကမင်းမေလိုးတဲ့အ‌တွေးပဲရှိတာလား",
    "မင်းမေဖာသည်မကိုအများနဲ့ရောလိုးမယ်",
    "ဖာသည်မရဲ့သားဝူးတူးတူးမလုပ်နဲ့ဖျက်ကန်လိုက်မယ်",
    "မင်းအမေအေကိုက်လို့သေပြီဆို👉😂",
    "မင်းမေဘယ်သူလိုးလိုး ငါမလိုးဘူး",
    "ဒီဂရုချက်ရဲ့ဘုရင်ကငါဘဲ မင်းက ငါ့လက်အောက်မာဘဲနေ🤧",
    "ကြာလေပျော့လေပါလား ဖယောင်းလေးရာ",
    "ဟျောင့်ခွေးသား မင်းကရိုးရိုးခွေးမဟုတ်ဘူး ဝဲစားနေတဲ့ခွေးဝဲစား",
    "ဖာသည်မသားလို့ပြောရင်လဲ မင်းအမေငါ့မယားနစ်နာဦးမယ်",
    "ကိုက်လေဟျောင့်ခွေး",
    "ကိုမေကိုလိုးသွားရမယ်နော်မအေလိုးလေး",
    "အေးမသိဘူးမင်းအမေဖာသည်မပဲ",
    "လန့်လိုက်တာ မင်းမေစပ့ငါလိုး",
    "ဘာလားပဲစောက်တောသား",
    "ဆင်ခြေတွေ လာပေးနေတာ မသနားဘူးငါက မနာလိုမှုတွေများပြီး မင်းငါစလို့ ကြိတ်ခိုးလောင်နေတာဆို ခွေးမျိုးတုံးချင်နေတာ ခွေးမသားက👉😂",
    "ငိုပြမနေနဲ့မင်းအမေဖာသယ်မကြီးသေမှငိုပလိုက်",
    "ဟျောင့်ဝက် မင်းအနူတောထဲကနေလမ်းပျောက်နေတုန်းဘဲမလား အဲ့တော့မကြိုးစားနဲ့အကုန်သဲထဲရေသုန်ဘဲ😂👌",
    "မအေလိုးလေးငါဆဲတိုင်းနာကျည်းပြီးပြန်ဆဲနေရတာနာကျည်းနေပြီလားတောသား",
    "စောက်ကျပ်ကိုမပြည့်ဘူး ကြက်မသား🤞😂",
    "ဟောင့် တယ်လီဂွမ်နံပတ်ဝမ်းဖင်ခေါင်းစတားဖာသည်မသားလေး",
    "ကဲပါထားလိုက်တော့ လိုးတော့မယ်မင်းအမေကို",
    "မအေလိုးကြက်ပေါက်စ ပိကျိပိကျိ‌နဲ့မင်းဘာတွေအော်နေတာလဲ",
    "မအေလိုးခွေး ဂုတ်မွှေသန်လားမင်း",
    "ဟောင့်ဘောမ ရပ်လိုက် လက်ပိုက် ရပြီ ဆက်ကိုက်",
    "ဟုမ်းမိတ်ဆိုပြီး မင်းအမေကိုအမုန်းကြိတ်ပေးရမှလား",
    "ဟိတ်ကောင်မင်းအမေစောက်ဖုတ်ပူရှိန်းပူရှိန်းနဲ့လိုးကောင်းလိုက်တာကွာ",
    "ဖာသည်မသားမင်းအမေစောက်ပက်တွေလာပြောနေတာလား👉😂",
    "ငါလိုးဖာသည်မသားမင်းအမေဝဲစားစောက်ဖုတ်ကို မန္တလေးတောင်ကနဂါးကြီးနှစ်ကောင်ပတ်ပီးနဂါးပတ်နဲ့လိုးပေးမယ်😁",
    "ဟိတ်ကောင်မင်းအမေစောက်ဖုတ်ကိုထွန်းရွှေဝါလူးပီးသုတ်လိုးလိုးပေးမယ်ပူစပ်စပ်ဖြစ်နေအောင်",
    "မင်းအမေဖာသည်မဆို👉😂",
    "ငါလိုးမ အာပေးတူ ဆဲတာပျော့လိုက်တာ ထိထိမိမိဆဲလေ🤞😏",
    "မင်းကယောင်္ကျားမှမဟုတ်ပဲဆဲတာတောင်အခြောက်လို‌ဆဲနေတာ",
    "မအေလိုးမင်းမေစောက်ပတ်သဲပတ်ပီးလိုးပေးမယ်ဂျောက်ဂျောက်နဲ့ မြည်နေအောင်😎",
    "မင်းမေဖာသည်မကိုအများနဲ့ရောလိုးမယ်",
    "တော်တီနောင်တော်တီနောင်မင်းအမေဖင်ကြီးကပြောင်",
    "မင်းအမေအိကျိကြီး ငါစို့တယ်ဘာဖြစ်လဲ",
    "မင်းအဖေခွေးကြီးကိုသွားပြောလေအက်တာ",
    "ငေးမနေနဲမင်းအမေဖာသည်မဆုံးပြီ",
    "ဟျောင့်ဖာသည်မသားကိုက်လိုက်တာလား",
    "မင်းစောက်ဆင့်နဲ့ပါးစပ်တောင်မဟနဲ့လက်နောက်ပြစ်ထား",
    "ဟိတ်ကောင်မအေလိုး၁၂၃ဆိုတာနဲ့ကိုယ်မေကိုယ်ပြန်လိုးဖို့အဆင်သင့်ပြင်ထားတော့",
    "ခွေးဝဲစားမသားကိုက်အားပျော့လှချည်လားကွ",
    "မင်းအမေကသာငါ့အပေါ်တက်ခွတာပါတပည့်",
    "မင်းရဲ့စောနကအစွယ်တွေဘယ်ဖျောက်လိုက်တာလဲဘောမ",
    "မအေလိုးပေါ်ပြူလာဖြစ်ချင်တာလားဒေါ်မူယာကမင်းအမေဆို",
    "မအေလိုးဝက်ကိုက်မှာသာကိုက်စကားပလ္လင်ခံမနေနဲ့နောက်ဆုံးမင်းဒီဘူတာပဲဆိုက်မှာ",
    "မအေလိုးခွေးမင်းအမေခွေးလိုးလိုက်လို့မင်းပါစိတ်မနှံ့တဲ့ခွေးဖြစ်တာဆို",
    "မင်းအမေဖင်ထဲငါ့လီးစိုက်ဝင်သွားလို့ရပ်ကွက်တကာအော်ကြီးဟစ်ကျယ်နဲ့လျှောက်အော်နေတာလားမအေလိုးရ",
    "မင်းစောက်ဦးနှောက်တစ်ခြမ်းပုတ်နေတာလား",
    "ငါကမင်းရန်သူမဟုတ်ဘူးမင်းမိတ်ဆွေမင်းအမေကိုလိုးမယ့်မိတ်ဆွေ",
    "1234ဆိုတာနဲ့ မင်းအမေစောက်ပတ်ကိုဖြဲထား ငါကအားနဲ့ပြေးလိုးမယ်",
    "ခွေးမသားသတ္တိရှိရင်မင်းအမေဖာသည်မကိုအော်ဆဲပြလိုက်ပါလား",
    "မင်းစကားအရမ်းများတယ်ငါ့လီးငုံထားပါလား",
    "ဟာလန့်တာမင်းအမေမင်းထလိုးတော့ငါလည်းလန့်တာပေါ့",
    "Telegram မှာ ငါဆရာပဲ မင်းအမေကိုလိုးတယ်ကွာ ဘယ်သူဘာပြောမလည်း",
    "မင်းမေစဖုတ်ကိုဆင်စီးပြီးမီးထုတ်ရမ်းဝင်တာတောင်မိူင်းမဆွံဘူးဆိုမအေလိုး",
    "အေးဒါဆိုလိပ်စာပြောမင်းအမေကို deli နဲ့ လှမ်းလိုးခိုင်းပလိုက်မယ်",
    "ငါလိုးမခွေးအခြောက်လိုကိုက်မနေနဲ့ယောက်ကျားလိုဖိုက်",
    "မင်းအမေဖာသယ်မကြီးကို ဖာတန်းကပြန်ခေါ် နောက်ပီးရင် ဘိုးဘွားရိပ်သာပို့စမ်း",
    "ငါပြောတဲ့စာသားတွေကမင်းအတွက်အထီးကျန်ဆန်မူနဲ့ပြတ်သားနေတာမင်းဘာလိုတုံပြန်ရခက်နေတာလဲ",
    "ဖာသည်မသားယောင်ခြောယ်ကောင် မင်းဘွားအေငါလိုး",
    "စောက်ရူးရာ ကိုက်မယ်ဆိုသေချာကိုက် မထိတထိနဲ့လာမညှောင်နဲ့",
    "အဲ့တာမင်းမေဖာသည်မနာရေးဖိတ်စာလား",
    "အတွေးကမင်းမေလိုးတဲ့အ‌တွေးပဲရှိတာလား",
    "မင်းမေဖာသည်မကိုအများနဲ့ရောလိုးမယ်",
    "ဖာသည်မရဲ့သားဝူးတူးတူးမလုပ်နဲ့ဖျက်ကန်လိုက်မယ်",
    "ဟေ့ရောင်ဖာသည်မသား ခေါ်ရင်သေချာထူးကွာ မထူးရင်မင်းအမေစဖုတ်ထဲငါ့လီးစိမ်ထားရလိမ့်မယ်",
    "ဘာတွေလျှောက်ရေးနေတာ စောက်ရူးအကွပ်နက်",
    "မင်းမာန်စွယ်လေး ထုတ်ပြစမ်း ဖာသည်မသား",
    "ဖာသည်မသားလီးလိုနားတာလား",
    "ဖာသည်မသားဆိုဆက်တိုက်ကိုက်",
    "ငါလိုးမ ဖာသည်မအကြီးစားရဲ့သား မင်းမိဘငါလိုးတော့ဘာကျစ်လို့လဲဟ",
    "ငါလိုးမဖာသယ်မသား မင်းဘယ်နားစောက်သုံးကျလို့လည်း",
    "ဒီလိုလုပ်မင်းအမေကိုငါကလိုးမယ်မင်းကvdရိုက်ထား",
    "ဟျောင့်၀က်မသားလက်နှေးပြီလား",
    "ဟျောင့်ကိုမေကိုလိုးတဲ့ဝက်ပြိတ္တာမျိုး",
    "မင်းအမေစောက်ပက်ကိုလေပေါ်ကနေတက်စိုက်ပြီးလိုးပစ်မယ်",
    "အထာမမိုက်တဲ့ငါလိုးမဝက်မိုက်🤞",
    "မင်းအမေစောက်စိကိုသံပုရာသီးနဲ့ညှစ်ပြီးကော်ပျံ့လိပ်ထဲညှပ်စားပစ်မယ်",
    "ငါလိုးမဖာသည်မသားမင်းအမေကိုကင်းမြှီးကောက်ထောင်လိုးမယ်",
    "မင်းအမေစပတ်ကို ဆားသိပ်ပီ နှပ်ထားအုန်းမှ ရမယ်😁",
    "မင်းအဖွားစက်ပက်ကျင်စက်နဲ့ထိုးခံရလို့ စမာန်ထနေတာလား",
    "ဟျောင့်မင်းစောက်ပေါက်ကိုဘာနဲ့ပိတ်ပေးရမလဲမင်းအမေစောက်ပက်နဲ့လား",
    "ဟျောင့်မင်းစောက်ခွက်ကဒစ်ရာဘယ်သူ့ဒစ်ရာလဲ😳",
    "မင်းအမေစောက်ပက်အယ်အယ်ကြီးကိုပိန္ဒဲသီးကြီးနဲ့ထုခြေပစ်မယ်ကွာ😳👈",
    "ယျောင့်စောက်၀က်ကြီးကိုက်ထားမယ်လေ",
    "မအေလိုးခွေးပင်ပန်းသွားပြီလားဖာသည်မသား",
    "ဟျောင့်ဖာသည်မသားကိုက်",
    "မင်းအမေသေတာလားအခုက",
    "ဖာသည်မသားအံဂတ်ကျွတ်အောင်ကိုက်",
    "ရိုးသားပြီးလိုးကား ကြည့်ပြီးမင်းအမေစောက်ပက်တည့်တည့်ငါ့လီးကြီးစိုက်ထည့်လိုက်ရမလား",
    "မင်းအမေစောက်ပက်ပလာတာကြီးကိုနံပြားရိုက်သလိုရိုက်ပစ်မယ်",
    "မင်းအမေစောက်ပက်ကိုဖြတ်ပြီးဘူးသီးနဲ့ရောပြီးချက်စားပစ်မယ်",
    "ဟျောင့်မင်းအမေကိုဝက်တက်လိုးတာလား",
    "မင်းအမေဖာသည်မစဖုတ်ကိုလှံနဲ့ဖြတ်စိုက်ပြီးအောင်ပွဲခံပစ်မယ်",
    "ငါလိုးမအဆီပိတ်ကိုက်ထား",
    "ဖာသည်မသားလေးမင်းအမေစောက်ဖုတ်ကိုလီးမှာဂေါ်လီကွင်းပြီးလိုးပစ်မယ်",
    "ဟျောင့်ခွေးမသားမင်းနှမစပ့ပြဲမကိုမုဒိန်းကျင့်ပစ်မယ်",
    "သွားကောင်းရင်ကိုက်လိုက်ခါးကောင်းရင်ကော့လိုက်ဖက်တီး😳😳",
    "မင်းအမေစောက်ကြက်မကိုပါးနားပိတ်ရိုက်ပြီးအသုဘချပစ်မယ်",
    "ဖာသည်မသားလေးအရှုံးပေးတော့မှာလား",
    "မင်းအမေဝက်ကျားမကျောကုန်းကြီးကိုကျဥ်စက်နဲ့တို့ပြီးဝက်ခြံထဲမှာဇီးတင်ပစ်မယ်",
    "ဟျောင့်ကိုက်မင်းကိုက်နေတာငါ့ဖိနပ်ကြီး😳",
    "တူတူရေဝါးဆိုပီးမင်းအမေစောက်ဖုတ်ကိုကြည့်မယ်",
    "မအေလိုးကိုက်ထားဖာသည်မသားကြောင်ကြည့်မနေနဲ့",
    "ဘမောတဲ့ဘောမ ဝဠ်ကြွေးရွှိသမျှအောင့်အီးသာခံလိုက်",
    "သာဓုနှစ်ကြိမ်ခေါ်လိုက်ဘောမ မင်းကိုနောက်တစ်ကြိမ်ပေးမခေါ်ဘူးမင်းဒီဘဝဒီမျှဝဠ်ကြွေးရှိသမျှကုန်အောင်သာဆပ်",
    "မအေလိုးစောက်သခေါရပ်ကြည့်မနေနဲ့မင်းအမေငါတက်လိုးလိုက်မယ်",
    "နှမလိုးဘောမကိုက်ဆိုကုန်းသာကိုက်နောက်အံကိုကြိတ်ထားရဲရဲသာကိုက်",
    "ဟိတ်ကောင်စောက်ဝက်စောက်ခွက်ကိုခြောက်ချက်တိတိရိုက်ခံရမယ်",
    "ဖာသည်မသားကိုက်ပါ",
    "ကိုမေကိုလိုးလေး",
    "စောက်ဖာသည်မသားသွားတွေကျိုးချင်နေတာလား",
    "ပါးပိတ်ရိုက်လိုက်မယ်ငါလိုးမသား",
    "တပည့်စောက်လုပ်ပေးမယ်ကိုက်",
    "မအေလိုးဘာသဘောလဲမင်းကခွေးတစ်ကောင်လိုအဆက်မပြတ်အူနေတော့မှာလား",
    "ဝူးဝူးဝါးဝါးငါလိုးမသား",
    "လှိမ့်ဆဲခံရလို့တင်းနေတာလား",
    "ရုပ်ပြိုင်ချောမလား",
    "‌ဘာမောတဲ့ဘောမ အဆဲခံရလို့ခံပျင်းနေပြီလား",
    "မင်းလိုကောင်ကိုဆဲရတာ ဘော့ဖြစ်တဲ့ငါတောင် ရွံတယ်",
    "ဇွဲသုတက မှာထားတယ် ဖာသည်မသားဆိုဆဲတဲ့ ဆိုလိုတာက မင်းကဖာသည်မသားပဲ",
    "ငါလိုးမသား လူကအဖြစ်မရှိဘူးခွေးလုံးလုံးဖြစ်မယ့်ကောင်",
    "ခွေးမသားလို့မပြောရဘူးခွေးစကားကတော့တတ်တယ်",
    "မင်းအမေဖာသည်မနို့ကြီးကိုလီးကြီးနဲ့တေ့ပေးရမလား",
    "ဟျောင့်ခွေးမင်းကိုက်နေတာငါ့လီးကြီး",
    "ဟျောင့်မျောက်ကြီးကြောက်ပြီလို့ပြောဟ",
    "လန့်လာပြီမင်းမေစောက်ပက်ပါပြေးလိုးချင်လာပြီ",
    "မျောက်လိုမင်းအမေကိုသစ်ပင်ပေါ်မှာတက်လ်ိုးမယ်",
    "ကို့ဘွားအေကိုလိုးလေးနော်မင်းအမေစောက်ပက်ကြီးကိုမုန့်မှတ်ပြီးစားပစ်မယ်",
    "ဟျောင့်စောက်ပေါလို့တော့မပြောရဘူးပေါချက်ကလက်လန်တယ်",
    "ဟျောင့်စောက်ပေါမင်းကိုခိုင်းစားနေတာ",
    "ရိပ်မိလားတော့မသိဘူးမင်းကိုခိုင်းစားနေတာဟ",
    "မအေလိုးမင်းအမေစောက်ပက်ကိုငါးမျှားချိတ်နဲ့ချိတ်ပစ်မယ်",
    "ဟျောင့်လာအုံးခွေးစကားလာပြော",
    "ပုပ်ပွနေတဲ့မင်းအမေဖာသည်မစောက်ဖုတ်ကြီးကိုမလိုးဘူး",
    "ဟျောင့် ဖာသည်မသားကြီးဆို မင်းက",
    "အလန့်တကြားကိုမေကိုထလိုးတဲ့ကောင်ကြီးလားမင်းက",
    "ငါ့အတွက်မင်းကိုပြစရာလီးတစ်ချောင်းပဲရှိတယ်",
    "မင်းကိုကိုမေကိုလိုးလို့စွတ်ဆွဲနေရင်မင်းစိတ်ဆိုးမှာလား",
    "မအေလိုးအခြောက် speed တင်ပြီးကိုက်ဖို့ပြင်",
    "မညောင်းရင်တစ်ညလုံးရေးမလားမပျောက်ကြေး",
    "ကိုမေကိုလိုးမင်းအမေစောက်ပက်ဂွနဲ့ရိုက်ပစ်",
    "လမ်းဘေးကကလေးတောင်မင်းထက်ဆဲတတ်တယ်😅👈",
    "ငါလျှာမထုတ်ဘူးလီးထုတ်ထားတယ်မင်းအမေကိုလိုးတော့မယ်",
    "မင်းဖေရောအမေရောကခွေးလားမင်းမေဖာသည်မကို လူရုပ်မပေါ်အောင် သမ မယ်",
    "ငါလိုးမစောက်ဖာသယ်မသား မင်းအမေစောက်ပတ် နဲ့ ငါလီးနဲ့က 2မီတာပဲ ကွာတော့တယ်နော်",
    "ငါလိုးမဖာသယ်မသားသေမယ် စောက်ဘောမ",
    "စောက်ကြောလာတင်းနေတယ်ငါလိုးမဖာသည်မ",
    "ဖာသည်မသားရုပ်ဆိုးအကျည်းတန်လိုက်တာ🤮",
    "ဟျောင့်ဝက် မင်းအနူတောထဲကနေလမ်းပျောက်နေတုန်းဘဲမလား အဲ့တော့မကြိုးစားနဲ့အကုန်သဲထဲရေသုန်ဘဲ😂👌",
    "ဖာသည်မသားဆိုပီပီဟန်ချီချီကိုက်ပလိုက်ကွာမာန်ဖီပီးတော့",
    "ဟျောင့်ခွေးငေးငိုင်မနေဘဲမင်းကဆက်ကိုက်",
    "ငါကလူမိုက်မင်းအမေကိုအသေဖိုက်မှာ",
    "မင်းနှမစောက်ပတ်ကိုခပ်နာနာလေးဖြဲထိုးတက်လိုးပလိုက်မယ်",
    "ဟျောင့်ခွေးဘီလူး",
    "မင်းစောက်ရုပ်ဆိုးတာငါသိပါတယ်စောက်ရုပ်ဆိုးကောင်ရ",
    "စောက်ဖာသည်မသားမင်းဇရှိရင်မင်းအမေစောက်ပေါမကိုဖာသည်မကြီးလို့အော်ဆဲပြစမ်းကွာ",
    "ခွေးမသား",
    "ဖာသည်မသားမင်းအဖေပါပေးတယ်ထိုးမာလား",
    "စောက်ခွက်တက်နင်းလိုက်မယ်",
    "ငါလိုးမစောက်သခေါယောက်ျားဖြစ်ပီးစောက်ပဲမများနဲ့",
    "မအေလိုးစောက်ထာစောက်ကန့်မရှိတဲ့ဂေးကြီးလားမင်းက",
    "မင်းအမေဖာသည်မကိုလူပုံအလယ်မှာလိင်ဆက်ဆံပစ်မယ်ကွာ😂🤞",
    "ငါလိုးမခွေး",
    "လီးဖစ်တာလားမင်းကလီးရုပ်နဲ့ဆောင့်ကန်လိုက်မယ်",
    "မအေလိုးကသခင်အသစ်ရအစာလေးဝတော့ခွေးတစ်ကောင်လိုပြန်ကိုက်တတ်ဖို့အစွယ်သွေးနေပီ",
    "မင်းပဲအဆဲခံနေရတယ်",
    "မင်းလည်းဘယ်ဘဝကအာကုသိုလ်လဲမသိဘူးဒီဘဝမာလာအဆဲခံနေရတယ်",
    "ဖာသယ်မသားတပည့်အစုတ်ပလုပ်ကောင်",
    "မင်းငါ့ကိုတားနိုင်မယ်လို့ထက်နေတာလား လှိုင်းတလူံးက သမုဒ္ဒရာကိုတားဖို့ ကြိုးစားသလိုပဲ",
    "ဘာလဲဖာသည်မသားမင်းကိုက်နေတာငါ့ခြေထောက်ကြီး",
    "ဘာတွေငေးငိုင်နေတာလဲကိုက်ရမှာမင်းအလုပ်",
    "ဖာသည်မသားမင်းအမေဖာသည်မကိုငါလိုးမိတာတောင်းပန်ပါတယ်",
    "ကိုက်တတ်ရင်သေချာကိုက် မထိတထိတော့မလုပ်ပါနဲ့ကွာ😹😹✌🏻",
    "လူကသာစောက်သုံးမကျတာပြောလိုက်ရင်စောက်ကြီးစောက်ကြယ်နဲ့",
    "ကိုက်မယ်ဆိုလဲကိုက်ကွာဝေ့ဝိုက်မနေနဲ့",
    "ငါကအထာဆျာပဲမင်းကိုလှိမ့်ရိုက်ပေးလိုက်တာမင်းအစွယ်တွေအကုန်ကျွတ်ထွက်ကုန်ပီ",
    "ဟျောင့်ခွေး😂",
    "ငါကအသေကြမ်းတာမင်းအမေစောက်ဖုတ်ကိုသွေးစိမ်းပန်းထွက်တဲ့အထိလိုးခွဲနိုင်တယ်",
    "ဖာသည်မသားကရုပ်ဆိုးသလောက်အတော်အကိုက်ကြမ်းတဲ့ကောင်",
    "မခင်ဘူးကွာကပ်ဖားယက်ဖားဆိုစောက်ဖာသည်မသား",
    "ငါဒီမှာဟဖာသည်မသားလာကိုက်",
    "ဘာငေးနေတာမkoက်ရဲဘူးလားကွီးကို",
    "မင်းကိုက် တာကိုကြည့်ချင်တယ် ဟိတ်ကောင် ငါလိုးမသား ငါ့ကိုကိုက်ပြကွာ",
    "ကမ္ဘာမှာဆွဲငင်အားရှိတယ်မင်းအမေမှာလည်းရှိတယ်လီးတစ်ချောင်းလောက်တွေ့တာနဲ့နီးတဲ့အပေါက်ထဲဇွတ်ဆွဲတာ",
    "မင်းနဲ့ပြောရတာက အောက်ခြေတောသားနဲ့ပြောနေရသလိုပဲ အိပ့အိပ့နဲ့",
    "ငါလိုးမသားပြေးကန်လိုက်လို့သေချင်းဆိုးနဲ့သေနေမယ်",
    "မင်းမေကိုမထင်ရင်မထင်သလိုလိုးတာလား",
    "မင်းငါ့ဆီကဘာလိုချင်နေတာလည်းငါလိုးမတောခွေးသေချာကိုက်လေ",
    "မင်းရဲ့စောက်သုံးမကျတဲ့ဘဝကိုနာကျည်းနေတာလား",
    "ဖာသည်မသား ဘယ်ကပေါက်ဖွားလာတာလည်း",
    "ငါလိုးမဖာသည်မသားမင်းအမေစောက်ပက်ကိုသံပဒက်နဲ့ပိတ်တိုက်ပေးလိုက်ရမလား",
    "မင်းအမေစောက်ပက်တည့်တည့်သေးပန်းပစ်မယ်",
    "ဖာသည်မသားမင်းထူးလေ",
    "ဟျောင့်ကိုက်လေနှမလိုးစောက်တောသားလာထား",
    "စောက်ရူးနားကန်း မင်းအမေကို ငါ့လိုးဟေး",
    "မင်းမေစောက်ပက်တွေးတောတာလားကွာငါလိုးမဖာသည်မသား",
    "မင်းအဖေစောက်တောသားကိုမေးကြည့်ဇွဲသုတဘာကောင်လဲဆိုတာ",
    "ငါလိုးမစောက်ရုပ်ဆိုးလူကြည့်တော့လီးရုပ်နဲ့ပြေးကန်လိုက်မယ်",
    "ဝက်သားကျွေးပေးလိုက်မယ်မအေလိုးကုလား",
    "ဖာသည်မသား ကပ်ဖားကောင်မင်းလိုခွေးကိုအသာအယာရိုက်မယ်",
    "ကင်းမြီးကောက်ထောင်ပြီးလိုးနေတာဘရို့အမေနဲ့",
    "မင်းအမေစောက်ပက်ကိုအတူတူလိုးကြရအောင်ဘရို",
    "ဟေဖာသည်မသားမင်းအမေသေတာငါကလီးလုပ်ရမှာလား",
    "ကြောက်ပြီလား မင်းဇကဒါပဲလား",
    "ငါ့အိမ်ကခွေးပေါက်နဲ့ပြိုင်ကိုက်ရင်တောင် မင်းကရှုံးမှာ",
    "ဇွဲသုတကြမ်းရင် မင်းအမေလည်းမနိုင်ဘူး ကုန်''ပြောရရင် ကုတင်ပါကျိုးတယ်",
    "နှမလိုးလေး ငါမင်းအမကိုမလိုးဘူး မဖားနဲ့",
    "ကြောက်လန့်နေတာလားစောက်ကုလား",
]

shuffled_replies = []

def get_random_reply():
    global shuffled_replies
    if not Replies:
        return "No replies available."
    
    if not shuffled_replies:
        shuffled_replies = list(Replies)
        random.shuffle(shuffled_replies)
        
    return shuffled_replies.pop()

def is_admin(update: Update) -> bool:
    user = update.effective_user
    return user is not None and user.id in ADMIN_IDS

async def admin_only(update: Update) -> bool:
    if not is_admin(update):
        message = update.effective_message
        if message:
            await message.reply_text("Sir Zwe Thuta ka min ah fay lrr")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if not is_admin(update):
        if user:
            user_flow_state[user.id] = 1
        await message.reply_text(" https://t.me/+odchGTDKNgVjYWE1 Gpထဲ @urPaPiibot လို့ Mt  ပြီး ကိုကို လို့ခေါ်ရင် ပါမစ်ရနည်းပြောပြမယ်")
        return

    await update.effective_message.reply_text(
        "🤖 Bot is online!\n\n"
        "--- Admin Commands ---\n"
        "/adm (reply) - Grant bot access to a user (Main Admin only)\n"
        "/unadm (reply/ID) - Remove bot access from a user (Main Admin only)\n"
        "/admlist - Show all current admins list (Main Admin only)\n\n"
        "--- Auto Reply Commands ---\n"
        "/target USER_ID - Add user for auto-reply in THIS group\n"
        "/remove USER_ID - Remove user from auto-reply & MT list in THIS group\n"
        "/list - Show all targets in THIS group\n"
        "/stop - Pause auto-reply\n\n"
        "--- Auto Delete Commands ---\n"
        "/del (reply/ID) - Add user to auto-delete list in THIS group\n"
        "/undel (reply/ID) - Remove user from auto-delete list in THIS group\n\n"
        "--- Continuous Mention (MT) Commands ---\n"
        "/mt USER_ID - Start infinite MT spamming in THIS group\n"
        "/stopmt - Stop continuous MT spamming in THIS group\n"
        "/speed SECONDS - Set MT speed\n\n"
        "--- Utility Commands ---\n"
        "/id - Show Group ID & Replied User ID\n"
        "/status - Show status"
    )

async def adm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or user.id != MAIN_ADMIN_ID:
        await message.reply_text("min ka Ztt ma hoke buu kmkl")
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text("Please reply to a user's message to grant them access using /adm.")
        return

    target_user = message.reply_to_message.from_user
    if target_user.is_bot:
        await message.reply_text("Cannot grant access to a bot.")
        return

    ADMIN_IDS.add(target_user.id)
    save_admins()
    
    if target_user.id in user_flow_state:
        del user_flow_state[target_user.id]

    await message.reply_text(f"✅ Successfully granted bot access to {target_user.full_name} (ID: {target_user.id})")

async def unadm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or user.id != MAIN_ADMIN_ID:
        await message.reply_text("min ka ztt ma hoke buu kmkl yay")
        return

    target_user_id = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    elif context.args:
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            await message.reply_text("Usage: /unadm USER_ID (or reply to user)")
            return

    if not target_user_id:
        await message.reply_text("Please reply to a user's message or provide a USER_ID to /unadm.")
        return

    if target_user_id == MAIN_ADMIN_ID:
        await message.reply_text("⛔ Cannot remove Main Admin!")
        return

    if target_user_id in ADMIN_IDS:
        ADMIN_IDS.remove(target_user_id)
        save_admins()
        await message.reply_text(f"❌ Successfully removed bot access from ID: {target_user_id}")
    else:
        await message.reply_text("This user is not an admin.")

# ✨ Main Admin တစ်ယောက်တည်းသာ /admlist စစ်လို့ရအောင် ပြင်ဆင်ထားခြင်း
async def admlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or user.id != MAIN_ADMIN_ID:
        await message.reply_text("min ka ztt ma hoke buu kmkl yay")
        return

    result = "🛡️ **Bot Admin List**:\n\n"
    result += f"👑 **Main Admin ID:** `{MAIN_ADMIN_ID}` (@{MAIN_ADMIN_USERNAME})\n\n"
    result += "📋 **Other Authorized Admins:**\n"

    other_admins = [uid for uid in ADMIN_IDS if uid != MAIN_ADMIN_ID]
    
    if other_admins:
        for idx, admin_id in enumerate(other_admins, 1):
            try:
                chat_member = await context.bot.get_chat(admin_id)
                name = chat_member.full_name or "Unknown"
                username = f" (@{chat_member.username})" if chat_member.username else ""
                result += f"{idx}. {name}{username} — `{admin_id}`\n"
            except Exception:
                result += f"{idx}. Unknown User — `{admin_id}`\n"
    else:
        result += "No additional admins added yet.\n"

    await message.reply_text(result, parse_mode="Markdown")

async def target_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    chat_id = update.effective_chat.id
    message = update.effective_message

    if chat_id not in targets:
        targets[chat_id] = set()

    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if user is None or user.is_bot:
            await message.reply_text("Cannot select this account.")
            return

        targets[chat_id].add(user.id)
        return

    if not context.args:
        await message.reply_text("Usage: /target USER_ID")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await message.reply_text("USER_ID must be numeric.")
        return

    targets[chat_id].add(user_id)

async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    chat_id = update.effective_chat.id
    message = update.effective_message
    user_id = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif context.args:
        try:
            user_id = int(context.args[0])
        except ValueError:
            await message.reply_text("Usage: /del USER_ID (or reply to user)")
            return

    if not user_id:
        await message.reply_text("Please reply to a user or provide USER_ID.")
        return

    if chat_id not in del_targets:
        del_targets[chat_id] = set()

    del_targets[chat_id].add(user_id)
    await message.reply_text(f"🗑️")

async def undel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    chat_id = update.effective_chat.id
    message = update.effective_message
    user_id = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif context.args:
        try:
            user_id = int(context.args[0])
        except ValueError:
            await message.reply_text("Usage: /undel USER_ID (or reply to user)")
            return

    if not user_id:
        await message.reply_text("Please reply to a user or provide USER_ID.")
        return

    if chat_id in del_targets and user_id in del_targets[chat_id]:
        del_targets[chat_id].remove(user_id)
        await message.reply_text(f"✅")
    else:
        await message.reply_text("This user is not in the Auto-Delete list.")

async def list_targets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    chat_id = update.effective_chat.id
    result = "📋 **This Group Target List**:\n\n"
    
    result += "🔹 **Auto-Reply Targets:**\n"
    group_targets = targets.get(chat_id, set())
    if group_targets:
        result += "\n".join(f"• ID: {uid}" for uid in sorted(group_targets)) + "\n"
    else:
        result += "No auto-reply targets selected in this group.\n"

    result += "\n"
    result += "🗑️ **Auto-Delete Targets:**\n"
    group_del_targets = del_targets.get(chat_id, set())
    if group_del_targets:
        result += "\n".join(f"• ID: {uid}" for uid in sorted(group_del_targets)) + "\n"
    else:
        result += "No auto-delete targets in this group.\n"

    result += "\n"
    result += "🔸 **Continuous MT Targets:**\n"
    group_mt_targets = mt_targets.get(chat_id, {})
    if group_mt_targets:
        result += "\n".join(f"• {uname} (ID: {uid})" for uid, uname in group_mt_targets.items()) + "\n"
    else:
        result += "No active MT targets in this group.\n"

    await update.effective_message.reply_text(result, parse_mode="Markdown")

async def remove_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    chat_id = update.effective_chat.id
    message = update.effective_message
    user_id = None
    target_name = None

    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user
        user_id = replied_user.id
        target_name = replied_user.first_name
    elif context.args:
        try:
            user_id = int(context.args[0])
        except ValueError:
            await message.reply_text("Usage: /remove USER_ID")
            return

    if not user_id:
        await message.reply_text("Please reply to a user or provide USER_ID.")
        return

    group_mt = mt_targets.get(chat_id, {})
    if user_id in group_mt and not target_name:
        target_name = group_mt[user_id]

    removed_from_targets = False
    removed_from_mt = False

    if chat_id in targets and user_id in targets[chat_id]:
        targets[chat_id].remove(user_id)
        removed_from_targets = True

    if chat_id in del_targets and user_id in del_targets[chat_id]:
        del_targets[chat_id].remove(user_id)

    if chat_id in mt_targets and user_id in mt_targets[chat_id]:
        del mt_targets[chat_id][user_id]
        removed_from_mt = True
        
        if not mt_targets[chat_id]:
            if chat_id in mt_tasks and mt_tasks[chat_id]:
                mt_tasks[chat_id].cancel()
                del mt_tasks[chat_id]

    if removed_from_targets or removed_from_mt:
        display_name = target_name if target_name else str(user_id)
        user_mention_link = f'<a href="tg://user?id={user_id}">{display_name}</a>'
        await message.reply_text(f"ngo ma ny nk ftmt: {user_mention_link}", parse_mode="HTML")
    else:
        await message.reply_text("D kmkl ma shi thyy buu ha")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running
    if not await admin_only(update):
        return

    is_running = False
    await update.effective_message.reply_text("ftmt twy ngo p lrr ha")

async def continuous_mt_loop(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    global mt_targets, mt_delay, mt_tasks

    def get_combined_mentions_and_text():
        group_mt = mt_targets.get(chat_id, {})
        mentions = " ".join([f'<a href="tg://user?id={uid}">{uname}</a>' for uid, uname in group_mt.items()])
        random_text = get_random_reply()
        return f"{mentions} {random_text}"

    try:
        burst_tasks = []
        for _ in range(6):
            if chat_id not in mt_targets or not mt_targets[chat_id]:
                break
            full_msg = get_combined_mentions_and_text()
            burst_tasks.append(
                context.bot.send_message(chat_id=chat_id, text=full_msg, parse_mode="HTML")
            )
        
        if burst_tasks:
            await asyncio.gather(*burst_tasks, return_exceptions=True)

        while chat_id in mt_targets and mt_targets[chat_id]:
            full_msg = get_combined_mentions_and_text()

            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=full_msg,
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"MT Loop Error in chat {chat_id}: {e}")
                await asyncio.sleep(1)

            if mt_delay > 0:
                await asyncio.sleep(mt_delay)
    except asyncio.CancelledError:
        pass

async def mt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global mt_targets, mt_tasks

    if not await admin_only(update):
        return

    chat_id = update.effective_chat.id
    message = update.effective_message
    target_user_id = None
    target_username = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        target_user_id = user.id
        target_username = user.first_name
    elif context.args:
        try:
            target_user_id = int(context.args[0])
            target_username = str(target_user_id)
        except ValueError:
            await message.reply_text("Usage: /mt USER_ID (or reply to user)")
            return

    if not target_user_id:
        await message.reply_text("Please reply to a user or provide USER_ID for /mt.")
        return

    if chat_id not in mt_targets:
        mt_targets[chat_id] = {}

    mt_targets[chat_id][target_user_id] = target_username
    
    if chat_id not in mt_tasks or mt_tasks[chat_id] is None or mt_tasks[chat_id].done():
        mt_tasks[chat_id] = asyncio.create_task(
            continuous_mt_loop(chat_id, context)
        )

async def stopmt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global mt_targets, mt_tasks

    if not await admin_only(update):
        return

    chat_id = update.effective_chat.id

    if chat_id in mt_targets:
        del mt_targets[chat_id]

    if chat_id in mt_tasks and mt_tasks[chat_id]:
        mt_tasks[chat_id].cancel()
        del mt_tasks[chat_id]

    await update.effective_message.reply_text("kmkl lyy twy ngo ny p htin loh stop pyy lyk tr 😹")

async def speed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global mt_delay

    if not await admin_only(update):
        return

    if not context.args:
        await update.effective_message.reply_text(
            f"Current MT Speed Delay: {mt_delay} seconds.\nUsage: /speed 1 (to set speed)"
        )
        return

    try:
        new_speed = float(context.args[0])
        mt_delay = max(0.0, new_speed)
        await update.effective_message.reply_text("%")
    except ValueError:
        await update.effective_message.reply_text("Please provide a valid number (e.g. /speed 1).")

async def auto_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running

    if not update.effective_user or not update.effective_message:
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    message = update.effective_message
    text = message.text or message.caption or ""

    user_id = user.id

    group_del_targets = del_targets.get(chat_id, set())
    if user_id in group_del_targets:
        try:
            await message.delete()
        except Exception as e:
            logging.error(f"Failed to delete message: {e}")
        return

    group_targets = targets.get(chat_id, set())

    if user_id in ADMIN_IDS:
        if is_running and user_id in group_targets:
            reply_text = get_random_reply()
            await message.reply_text(reply_text)
        return

    current_step = user_flow_state.get(user_id, 0)

    if current_step == 5:
        return

    if "ကိုko" in text.lower() or "@urPaPibotကိုကို" in text or f"@{context.bot.username}" in text:
        user_flow_state[user_id] = 2
        await message.reply_text("ဗျာ အာဘွားပေးမို့လား ပေးလိုက် အာဘွား ဆိုပြီး", reply_to_message_id=message.message_id)
        return

    if current_step == 2:
        if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
            if "အာဘွား" in text:
                user_flow_state[user_id] = 3
                await message.reply_text("ဟီး Bot ဆိုပေမယ့်နည်းနည်းတောင်ရှက်လာပြီ 😭", reply_to_message_id=message.message_id)
                return

    if current_step == 3:
        user_flow_state[user_id] = 4
        await message.reply_text("မင်း မိန်းကလေးတော့ဟုတ်ပါတယ်နော် ငါလိုးမ gay ကြီးလားမသိဘူး", reply_to_message_id=message.message_id)
        return

    if current_step == 4:
        user_flow_state[user_id] = 5
        await message.reply_text(f"လာတောင်း ကိုကို့စီကို @{MAIN_ADMIN_USERNAME}", reply_to_message_id=message.message_id)
        return

    if is_running and user_id in group_targets:
        reply_text = get_random_reply()
        await message.reply_text(reply_text)

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    message = update.effective_message
    chat = update.effective_chat

    result = f"Group/Chat ID: {chat.id}"

    if message.reply_to_message and message.reply_to_message.from_user:
        result += f" FtmtID: {message.reply_to_message.from_user.id}"
    else:
        result += "\n(No message replied to check user ID)"

    await message.reply_text(result)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    chat_id = update.effective_chat.id
    ar_state = "Enabled" if is_running else "Paused"
    
    group_mt = mt_targets.get(chat_id, {})
    mt_state = f"Running ({len(group_mt)} targets in this GP)" if group_mt else "Stopped"

    group_targets = targets.get(chat_id, set())
    group_del = del_targets.get(chat_id, set())

    await update.effective_message.reply_text(
        f"🤖 Bot Status (This GP):\n"
        f"• Auto-Reply: {ar_state} ({len(group_targets)} targets)\n"
        f"• Auto-Delete: {len(group_del)} targets\n"
        f"• Continuous MT: {mt_state}\n"
        f"• MT Speed Delay: {mt_delay}s"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Bot error: %s", context.error)

async def post_shutdown(application: Application):
    global mt_tasks, mt_targets
    mt_targets.clear()
    for chat_id, task in list(mt_tasks.items()):
        if task:
            task.cancel()
    mt_tasks.clear()
    print("Bot has successfully shut down.")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Set your bot token in the environment.")

    app = Application.builder().token(BOT_TOKEN).post_shutdown(post_shutdown).build()

    # Commands Registration
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adm", adm_command))
    app.add_handler(CommandHandler("unadm", unadm_command))
    app.add_handler(CommandHandler("admlist", admlist_command))
    app.add_handler(CommandHandler("target", target_command))
    app.add_handler(CommandHandler("del", del_command))
    app.add_handler(CommandHandler("undel", undel_command))
    app.add_handler(CommandHandler("list", list_targets))
    app.add_handler(CommandHandler("remove", remove_target))
    app.add_handler(CommandHandler("stop", stop_command))
    
    # Continuous MT Commands
    app.add_handler(CommandHandler("mt", mt_command))
    app.add_handler(CommandHandler("stopmt", stopmt_command))
    app.add_handler(CommandHandler("speed", speed_command))

    # General Commands
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("status", status_command))

    # Message Handler
    app.add_handler(MessageHandler(filters.TEXT | filters.ATTACHMENT, auto_reply_handler))

    app.add_error_handler(error_handler)

    print("Bot is starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
