import requests
import json
import os
import time
from dotenv import load_dotenv

# Token Cache file
TOKEN_CACHE_FILE = 'token_cache.json'

def get_cached_token(client_id, client_secret):
    # Check if we have a valid cached token
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, 'r') as f:
                cache = json.load(f)
                # Check if token is still valid (cached within last 20 hours)
                if time.time() - cache.get('timestamp', 0) < 20 * 3600:
                    print("Using cached TDX Access Token.")
                    return cache.get('token')
        except Exception:
            pass

    print("Requesting new Access Token from TDX...")
    token_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    # Simple retry for token
    for attempt in range(3):
        try:
            res = requests.post(token_url, data=token_data, timeout=10)
            if res.status_code == 200:
                token = res.json().get('access_token')
                # Save to cache
                with open(TOKEN_CACHE_FILE, 'w') as f:
                    json.dump({'token': token, 'timestamp': time.time()}, f)
                print("New Token retrieved and cached successfully.")
                return token
            elif res.status_code == 429:
                print(f"Token request rate limited (429). Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"Failed to get token: {res.text}")
                return None
        except Exception as e:
            print(f"Error getting token: {e}")
            time.sleep(5)
    return None

def fetch_with_backoff(url, headers, description):
    print(f"Starting to fetch: {description}")
    backoff = 5
    for attempt in range(5):
        try:
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code == 200:
                print(f"Successfully fetched {description}!")
                return res.json()
            elif res.status_code == 429:
                print(f"Rate limited (429) while fetching {description}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2
            else:
                print(f"Failed to fetch {description}. Status code: {res.status_code}. Response: {res.text}")
                return None
        except Exception as e:
            print(f"Error fetching {description}: {e}. Retrying in {backoff} seconds...")
            time.sleep(backoff)
            backoff *= 2
    print(f"Exceeded maximum retries for {description}.")
    return None

def main():
    load_dotenv()
    client_id = os.getenv('TDX_CLIENT_ID')
    client_secret = os.getenv('TDX_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("Error: TDX_CLIENT_ID and TDX_CLIENT_SECRET must be configured in .env")
        return

    # 1. Get Token (Cached)
    token = get_cached_token(client_id, client_secret)
    if not token:
        print("Failed to obtain TDX Token.")
        return

    headers = {'Authorization': f'Bearer {token}'}

    # 2. Fetch All Routes
    routes_url = "https://tdx.transportdata.tw/api/basic/v2/Bus/Route/City/Taichung?$format=JSON"
    raw_routes = fetch_with_backoff(routes_url, headers, "Taichung Bus Routes")
    
    if not raw_routes:
        print("Failed to download routes.")
        return

    # Process routes
    processed_routes = []
    seen = set()
    for item in raw_routes:
        route_id = item.get("RouteID")
        if not route_id or route_id in seen:
            continue
        seen.add(route_id)
        name_zh = item.get("RouteName", {}).get("Zh_tw", "")
        dep_zh = item.get("DepartureStopNameZh", "")
        dest_zh = item.get("DestinationStopNameZh", "")
        
        # Format names like "300路"
        name_display = name_zh if name_zh.endswith("路") or "路" in name_zh else f"{name_zh}路"
        
        processed_routes.append({
            "id": route_id,
            "name": name_display,
            "departure": dep_zh,
            "destination": dest_zh,
            "desc": f"{name_zh}路：{dep_zh} - {dest_zh}" if dep_zh and dest_zh else name_zh
        })
    processed_routes.sort(key=lambda x: x["id"])

    # 3. Fetch All Stops (StopOfRoute)
    stops_url = "https://tdx.transportdata.tw/api/basic/v2/Bus/StopOfRoute/City/Taichung?$format=JSON"
    stops_data = fetch_with_backoff(stops_url, headers, "Taichung Bus Stops (StopOfRoute)")
    
    if not stops_data:
        print("Failed to download stops.")
        return

    # Save routes and stops to project folders
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'app', 'static', 'data')
    os.makedirs(data_dir, exist_ok=True)

    routes_file = os.path.join(data_dir, 'routes.json')
    stops_file = os.path.join(data_dir, 'stops.json')

    with open(routes_file, 'w', encoding='utf-8') as f:
        json.dump(processed_routes, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(processed_routes)} processed routes to {routes_file}")

    with open(stops_file, 'w', encoding='utf-8') as f:
        json.dump(stops_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(stops_data)} raw StopOfRoute items to {stops_file}")

    print("Re-organization of local data completed successfully!")

if __name__ == '__main__':
    main()
