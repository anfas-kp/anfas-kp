import os
import sys
import datetime
import urllib.request
import json
import xml.etree.ElementTree as ET

def fetch_github_data(username, token):
    headers = {
        "User-Agent": "Python-Streak-Generator",
        "Content-Type": "application/json"
    }
    if token:
        headers["Authorization"] = f"token {token}"
        
    query = """
    query($user: String!) {
      user(login: $user) {
        createdAt
        contributionsCollection {
          contributionYears
        }
      }
    }
    """
    
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"user": username}}).encode('utf-8'),
        headers=headers
    )
    
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        years = data['data']['user']['contributionsCollection']['contributionYears']
    except Exception as e:
        print(f"Error fetching contribution years: {e}")
        years = [datetime.datetime.now().year]

    all_days = {}
    
    for year in years:
        year_query = """
        query($user: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $user) {
            contributionsCollection(from: $from, to: $to) {
              contributionCalendar {
                totalContributions
                weeks {
                  contributionDays {
                    date
                    contributionCount
                  }
                }
              }
            }
          }
        }
        """
        from_date = f"{year}-01-01T00:00:00Z"
        to_date = f"{year}-12-31T23:59:59Z"
        
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({
                "query": year_query, 
                "variables": {"user": username, "from": from_date, "to": to_date}
            }).encode('utf-8'),
            headers=headers
        )
        
        try:
            res = urllib.request.urlopen(req)
            y_data = json.loads(res.read().decode('utf-8'))
            calendar = y_data['data']['user']['contributionsCollection']['contributionCalendar']
            for week in calendar['weeks']:
                for day in week['contributionDays']:
                    all_days[day['date']] = day['contributionCount']
        except Exception as e:
            print(f"Error fetching year {year}: {e}")
            
    return all_days

def calculate_stats(all_days):
    if not all_days:
        return 0, (0, "", ""), (0, "", ""), "Sep 3, 2024"
        
    sorted_dates = sorted(all_days.keys())
    total_contributions = sum(all_days.values())
    first_contrib_date = sorted_dates[0] if sorted_dates else "2024-09-03"
    
    # Convert first_contrib_date to readable format
    try:
        dt = datetime.datetime.strptime(first_contrib_date, "%Y-%m-%d")
        first_date_str = dt.strftime("%b %d, %Y")
    except:
        first_date_str = "Sep 3, 2024"

    # Compute Longest Streak
    longest_streak = 0
    longest_start = ""
    longest_end = ""
    
    curr_l_streak = 0
    curr_l_start = ""
    
    for date_str in sorted_dates:
        count = all_days[date_str]
        if count > 0:
            if curr_l_streak == 0:
                curr_l_start = date_str
            curr_l_streak += 1
            if curr_l_streak > longest_streak:
                longest_streak = curr_l_streak
                longest_start = curr_l_start
                longest_end = date_str
        else:
            curr_l_streak = 0
            
    # Compute Current Streak
    today = datetime.date.today()
    current_streak = 0
    curr_start = ""
    curr_end = ""
    
    check_date = today
    # If today has 0 contributions, check if yesterday was active
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    if all_days.get(today_str, 0) == 0 and all_days.get(yesterday_str, 0) == 0:
        current_streak = 0
        curr_start = today_str
        curr_end = today_str
    else:
        if all_days.get(today_str, 0) == 0:
            check_date = today - datetime.timedelta(days=1)
            
        curr_end = check_date.strftime("%Y-%m-%d")
        c_date = check_date
        while True:
            d_str = c_date.strftime("%Y-%m-%d")
            if all_days.get(d_str, 0) > 0:
                current_streak += 1
                curr_start = d_str
                c_date -= datetime.timedelta(days=1)
            else:
                break
                
    def format_range(start_str, end_str):
        if not start_str or not end_str:
            return ""
        try:
            d1 = datetime.datetime.strptime(start_str, "%Y-%m-%d").strftime("%b %d, %Y")
            d2 = datetime.datetime.strptime(end_str, "%Y-%m-%d").strftime("%b %d, %Y")
            if start_str == end_str:
                return datetime.datetime.strptime(start_str, "%Y-%m-%d").strftime("%b %d")
            return f"{d1} - {d2}"
        except:
            return f"{start_str} - {end_str}"
            
    return total_contributions, (current_streak, curr_start, curr_end), (longest_streak, longest_start, longest_end), first_date_str

def build_streak_svg(total_contribs, current_streak_tuple, longest_streak_tuple, first_date_str, is_dark=True):
    width, height = 1180, 195
    
    bg_color = "#0A101F" if is_dark else "#F8FAFC"
    border_color = "#1E293B" if is_dark else "#E2E8F0"
    title_color = "#22D3EE" if is_dark else "#0891B2"
    ring_color = "#A78BFA" if is_dark else "#7C3AED"
    fire_color = "#10B981" if is_dark else "#059669"
    sub_color = "#94A3B8" if is_dark else "#475569"
    num_color = "#F8FAFC" if is_dark else "#0F172A"
    divider_color = "#1E293B" if is_dark else "#E2E8F0"
    
    curr_streak, c_start, c_end = current_streak_tuple
    long_streak, l_start, l_end = longest_streak_tuple
    
    today_str = datetime.date.today().strftime("%b %d")
    
    # Format streak dates
    if curr_streak > 0:
        try:
            d1 = datetime.datetime.strptime(c_start, "%Y-%m-%d").strftime("%b %d")
            d2 = datetime.datetime.strptime(c_end, "%Y-%m-%d").strftime("%b %d")
            curr_date_label = d1 if d1 == d2 else f"{d1} - {d2}"
        except:
            curr_date_label = today_str
    else:
        curr_date_label = today_str

    if long_streak > 0:
        try:
            d1 = datetime.datetime.strptime(l_start, "%Y-%m-%d").strftime("%b %d, %Y")
            d2 = datetime.datetime.strptime(l_end, "%Y-%m-%d").strftime("%b %d, %Y")
            long_date_label = f"{d1} - {d2}"
        except:
            long_date_label = ""
    else:
        long_date_label = ""

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none">
    <style>
        .title {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-weight: 600; font-size: 14px; fill: {title_color}; }}
        .num {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-weight: 700; font-size: 32px; fill: {num_color}; }}
        .sub {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-weight: 400; font-size: 11px; fill: {sub_color}; }}
    </style>
    
    <!-- Card Background -->
    <rect width="{width}" height="{height}" rx="10" fill="{bg_color}" stroke="{border_color}" stroke-width="1"/>
    
    <!-- Vertical Dividers -->
    <line x1="393" y1="35" x2="393" y2="160" stroke="{divider_color}" stroke-width="1"/>
    <line x1="786" y1="35" x2="786" y2="160" stroke="{divider_color}" stroke-width="1"/>
    
    <!-- Column 1: Total Contributions -->
    <g transform="translate(196, 0)">
        <text x="0" y="80" text-anchor="middle" class="num">{total_contribs}</text>
        <text x="0" y="108" text-anchor="middle" class="sub">Total Contributions</text>
        <text x="0" y="128" text-anchor="middle" class="sub">{first_date_str} - Present</text>
    </g>
    
    <!-- Column 2: Current Streak -->
    <g transform="translate(590, 0)">
        <!-- Ring & Flame Icon -->
        <circle cx="0" cy="72" r="38" fill="none" stroke="{ring_color}" stroke-width="4"/>
        <path d="M-1,-2 C-3,-6 -1,-10 2,-13 C5,-16 4,-20 1,-23 C8,-20 12,-14 10,-8 C14,-11 14,-15 13,-18 C18,-13 18,-4 13,2 C10,6 4,7 0,4 C-4,7 -9,6 -11,2 C-14,-3 -13,-11 -8,-16 C-7,-13 -5,-10 -1,-7 Z" fill="{fire_color}" transform="translate(0, 72) scale(0.95)"/>
        
        <text x="0" y="78" text-anchor="middle" class="num" style="font-size: 20px;">{curr_streak}</text>
        <text x="0" y="130" text-anchor="middle" class="title">Current Streak</text>
        <text x="0" y="150" text-anchor="middle" class="sub">{curr_date_label}</text>
    </g>
    
    <!-- Column 3: Longest Streak -->
    <g transform="translate(983, 0)">
        <text x="0" y="80" text-anchor="middle" class="num">{long_streak}</text>
        <text x="0" y="108" text-anchor="middle" class="sub">Longest Streak</text>
        <text x="0" y="128" text-anchor="middle" class="sub">{long_date_label}</text>
    </g>
</svg>'''

    # Validate XML
    ET.fromstring(svg)
    return svg

def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("PAT_1")
    username = "anfas-kp"
    
    print(f"Fetching contribution data for {username}...")
    all_days = fetch_github_data(username, token)
    total_c, curr_s, long_s, first_d = calculate_stats(all_days)
    
    print(f"Stats Calculated:")
    print(f" - Total Contributions: {total_c}")
    print(f" - Current Streak: {curr_s[0]} days ({curr_s[1]} to {curr_s[2]})")
    print(f" - Longest Streak: {long_s[0]} days ({long_s[1]} to {long_s[2]})")
    
    dark_svg = build_streak_svg(total_c, curr_s, long_s, first_d, is_dark=True)
    light_svg = build_streak_svg(total_c, curr_s, long_s, first_d, is_dark=False)
    
    os.makedirs("assets", exist_ok=True)
    with open("assets/streak-dark.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg)
    with open("assets/streak-light.svg", "w", encoding="utf-8") as f:
        f.write(light_svg)
        
    print("Generated assets/streak-dark.svg and assets/streak-light.svg successfully!")

if __name__ == "__main__":
    main()
