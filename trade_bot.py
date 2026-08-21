import os
import re
import requests
from bs4 import BeautifulSoup

# --- Configuration ---
LEAGUE_URL = "https://www.pennantchase.com/league/baseball/home?lgid=691"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TRADES_FILE = "last_trades.txt"

# Team mention map using full "City Nickname" format
TEAM_NAME_MAP = {
    "Arizona Diamondbacks": "<@&773898276940152833>",
    "Atlanta Braves": "<@&622615242978885632>",
    "Baltimore Orioles": "<@&728717530096468149>",
    "Boston Red Sox": "<@&1180931211858809023>",
    "Chicago Cubs": "<@&773897833211625473>",
    "Chicago White Sox": "<@&622615457299693578>",
    "Cincinnati Reds": "<@&773898419143442432>",
    "Cleveland Guardians": "<@&773898193041358879>",
    "Cleveland Indians": "<@&773898193041358879>",
    "Colorado Rockies": "<@&773898540321079316>",
    "Detroit Tigers": "<@&622615931625144341>",
    "Houston Astros": "<@&962525228636987402>",
    "Kansas City Royals": "<@&622614419486015510>",
    "Los Angeles Angels": "<@&622613488824483840>",
    "Los Angeles Dodgers": "<@&962525782977150996>",
    "Miami Marlins": "<@&752626736125968474>",
    "Milwaukee Brewers": "<@&622613398701604865>",
    "Minnesota Twins": "<@&728718027645780018>",
    "New York Mets": "<@&622613734896041994>",
    "New York Yankees": "<@&622952290428387329>",
    "Oakland Athletics": "<@&773897507272261683>",
    "Philadelphia Phillies": "<@&622614284979011595>",
    "Pittsburgh Pirates": "<@&622615936234684416>",
    "St. Louis Cardinals": "<@&622613261841596426>",
    "San Diego Padres": "<@&622618093868548097>",
    "San Francisco Giants": "<@&622615034157203469>",
    "Seattle Mariners": "<@&622612991413714975>",
    "Tampa Bay Rays": "<@&623340295517634560>",
    "Texas Rangers": "<@&622613054642978817>",
    "Toronto Blue Jays": "<@&622615298322989070>",
    "Washington Nationals": "<@&1180930959642722404>",
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

        timeline_items = soup.find_all("div", class_="timeline-item")

        for item in timeline_items:
            header_span = item.find("span", class_="fw-bold")
            if not header_span or header_span.get_text(strip=True).lower() != "trade":
                continue

            details_div = item.find("div", class_="font-16")
            if not details_div:
                continue

            for commish in details_div.find_all("div", class_="commishLink"):
                commish.decompose()

            for br in details_div.find_all("br"):
                br.replace_with("\n")

            trade_text = details_div.get_text().strip()
            cleaned_lines = [line.strip() for line in trade_text.splitlines() if line.strip()]
            normalized_trade = "\n".join(cleaned_lines)

            if normalized_trade and normalized_trade not in trades:
                trades.append(normalized_trade)

        return trades
    except Exception as e:
        print(f"Error fetching page: {e}")
        return []

def read_seen_trades():
    if not os.path.exists(TRADES_FILE):
        return set()
    with open(TRADES_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        return set(trade.strip() for trade in content.split("\n---\n") if trade.strip())

def append_seen_trades(new_trades):
    with open(TRADES_FILE, 'a', encoding='utf-8') as f:
        for trade in new_trades:
            f.write(trade + '\n---\n')

def send_discord_notification(message):
    try:
        r = requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
        r.raise_for_status()
        print("Discord notification sent.")
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

# --- Main Execution ---
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
