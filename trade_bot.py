import os
import re
import requests
from bs4 import BeautifulSoup

# --- Configuration ---
LEAGUE_URL = "https://www.pennantchase.com/league/baseball/home?lgid=691"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TRADES_FILE = "last_trades.txt"

# Team mention map matching your Discord role IDs
TEAM_NAME_MAP = {
    "Diamondbacks": "<@&773898276940152833>",
    "Braves": "<@&622615242978885632>",
    "Orioles": "<@&728717530096468149>",
    "Red Sox": "<@&1180931211858809023>",
    "Cubs": "<@&773897833211625473>",
    "White Sox": "<@&622615457299693578>",
    "Reds": "<@&773898419143442432>",
    "Indians": "<@&773898193041358879>",
    "Rockies": "<@&773898540321079316>",
    "Tigers": "<@&622615931625144341>",
    "Astros": "<@&962525228636987402>",
    "Royals": "<@&622614419486015510>",
    "Angels": "<@&622613488824483840>",
    "Dodgers": "<@&962525782977150996>",
    "Marlins": "<@&752626736125968474>",
    "Brewers": "<@&622613398701604865>",
    "Twins": "<@&728718027645780018>",
    "Mets": "<@&622613734896041994>",
    "Yankees": "<@&622952290428387329>",
    "Athletics": "<@&773897507272261683>",
    "Phillies": "<@&622614284979011595>",
    "Pirates": "<@&622615936234684416>",
    "Cardinals": "<@&622613261841596426>",
    "Padres": "<@&622618093868548097>",
    "Giants": "<@&622615034157203469>",
    "Mariners": "<@&622612991413714975>",
    "Rays": "<@&623340295517634560>",
    "Rangers": "<@&622613054642978817>",
    "Blue Jays": "<@&622615298322989070>",
    "Nationals": "<@&1180930959642722404>",
}

def format_mentions(text):
    for team, mention in TEAM_NAME_MAP.items():
        text = re.sub(rf'\b{re.escape(team)}\b', mention, text)
    return text

def get_current_trades():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get(LEAGUE_URL, headers=headers, timeout=10)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, 'html.parser')
        trades = []

        for element in soup.find_all(['li', 'div', 'p', 'tr']):
            text = element.get_text(separator=" ", strip=True)
            if re.search(r'\btrade\b', text, re.IGNORECASE) and 15 < len(text) < 500:
                clean_text = ' '.join(text.split())
                if clean_text not in trades:
                    trades.append(clean_text)

        return trades
    except Exception as e:
        print(f"Error fetching league page: {e}")
        return []

def read_seen_trades():
    if not os.path.exists(TRADES_FILE):
        return set()
    with open(TRADES_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def append_seen_trades(new_trades):
    with open(TRADES_FILE, 'a', encoding='utf-8') as f:
        for trade in new_trades:
            f.write(trade + '\n')

def send_discord_notification(message):
    try:
        r = requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
        r.raise_for_status()
        print("Discord notification sent.")
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

# --- Main Script ---
if not WEBHOOK_URL:
    print("Error: DISCORD_WEBHOOK_URL environment variable is not set.")
    exit(1)

current_trades = get_current_trades()
seen_trades = read_seen_trades()

new_trades = [t for t in current_trades if t not in seen_trades]

if new_trades:
    for trade in new_trades:
        formatted = format_mentions(trade)
        send_discord_notification(f"🚨 **Trade Alert:**\n{formatted}")
    append_seen_trades(new_trades)
    print(f"Posted {len(new_trades)} new trade(s).")
else:
    print("No new trades detected.")
