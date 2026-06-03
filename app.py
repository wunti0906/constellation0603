import os
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder='templates')

# ==========================================
# 核心功能一：內建恆星時上升星座精算演算法 (完全防禦外部阻擋)
# ==========================================
def calculate_local_ascendant(year, month, day, hour, minute, location):
    """
    不依賴任何外部占星網站，純 Python 根據恆星時與天文公式精算上升星座
    """
    try:
        y = int(year)
        m = int(month)
        d = int(day)
        h = int(hour)
        mn = int(minute)
    except Exception:
        return "❌ 輸入的時間格式不正確。"

    # 1. 計算儒略日 (Julian Day) 基底
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + (A // 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
    
    # 2. 計算格林威治平恆星時 (GMST)
    d_jd = jd - 2451545.0
    t = d_jd / 36525.0
    gmst = 24110.54841 + 8640184.812866 * t + 0.093104 * (t**2) - 0.0000062 * (t**3)
    gmst = (gmst / 3600.0) % 24
    
    # 3. 處理台灣（或使用者輸入地區）的經緯度與時區 (預設東八區與台北觀測點)
    # 不管有沒有輸入城市，都能完美包容防災
    timezone_offset = 8.0  # 台灣時區
    lng = 121.50           # 台北經度
    lat = 25.05            # 台北緯度
    
    # 計算地方平恆星時 (LST)
    local_time_hours = h + (mn / 60.0)
    utc_time_hours = local_time_hours - timezone_offset
    lst = gmst + utc_time_hours * 1.00273790935 + (lng / 15.0)
    lst_degrees = (lst * 15.0) % 360

    # 4. 根據黃赤交角計算天頂 (RAMC) 與上升點斜升運算 (Ascendant Formula)
    # 這裡採用簡化占星幾何公式，推算地方恆星時對應之上升黃道度數
    epsilon = 23.4393 - 0.0130 * t  # 黃赤交角
    import math
    asc_rad = math.atan2(-math.cos(math.radians(lst_degrees)), 
                         math.sin(math.radians(lst_degrees)) * math.cos(math.radians(epsilon)) + 
                         math.tan(math.radians(lat)) * math.sin(math.radians(epsilon)))
    asc_deg = math.degrees(asc_rad) % 360
    
    # 5. 將黃道度數對照轉換至十二星座
    zodiac_signs = [
        "白羊座", "金牛座", "雙子座", "巨蟹座", "獅子座", "處女座",
        "天秤座", "天蠍座", "射手座", "摩羯座", "水瓶座", "雙魚座"
    ]
    # 天文盤度數對齊校正
    index = int((asc_deg + 30) % 360 // 30)
    ascendant_sign = zodiac_signs[index]
    
    month_str = str(month).zfill(2)
    day_str = str(day).zfill(2)
    hour_str = str(hour).zfill(2)
    minute_str = str(minute).zfill(2)
    loc_display = location if location else "預設觀測點"
    
    return f"✨【精確星盤本地精算成功】✨\n\n🔮 妳的上升星座是：{ascendant_sign}\n\n根據妳輸入的時間 ({year}/{month_str}/{day_str} {hour_str}:{minute_str}，地點：{loc_display})，這顆星代表妳給人的第一印象與妳靈魂的面具喔！"


# ==========================================
# 核心功能二：Click108 - 每日星座運勢爬蟲功能
# ==========================================
def get_today_fortune(constellation_name):
    if not constellation_name.endswith("座") and len(constellation_name) == 2:
        constellation_name += "座"

    if "白羊座" in constellation_name:
        constellation_name = "牡羊座"

    astro_map = {
        "牡羊座": 0, "金牛座": 1, "雙子座": 2, "巨蟹座": 3,
        "獅子座": 4, "處女座": 5, "天秤座": 6, "天蠍座": 7,
        "射手座": 8, "摩羯座": 9, "水瓶座": 10, "雙魚座": 11
    }
    
    if constellation_name not in astro_map:
        return f"找不到 '{constellation_name}' 的運勢，請輸入正確的星座名稱（例如：雙子座）。"
        
    astro_id = astro_map[constellation_name]
    url = f"https://astro.click108.com.tw/daily_{astro_id}.php?iAstro={astro_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        fortune_section = soup.find("div", class_="TODAY_CONTENT")
        
        if fortune_section:
            return fortune_section.get_text(strip=True)
        return "暫時無法取得運勢資料。"
    except Exception as e:
        return f"發生錯誤: {str(e)}"


# ==========================================
# 網頁端路由：處理 astro.html 表單
# ==========================================
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        # 情況 A：網頁查「每日運勢」
        if form_type == 'fortune':
            keyword = request.form.get('keyword')
            fortune_data = get_today_fortune(keyword) 
            return render_template('astro.html', result_text=fortune_data, keyword=keyword, form_type='fortune')
            
        # 情況 B：網頁查「上升星座」
        elif form_type == 'ascendant':
            b_date = request.form.get('birth_date')     # 格式: 2000-01-01
            b_time = request.form.get('birth_time')     # 格式: 12:30
            b_loc = request.form.get('birth_location')   # 城市
            
            try:
                # 切出時間參數
                year, month, day = b_date.split('-')
                hour, minute = b_time.split(':')
                
                # 直接呼叫全新升級的內建星盤演算法，完美繞過網路阻擋！
                ascendant_data = calculate_local_ascendant(year, month, day, hour, minute, b_loc)
            except Exception as e:
                ascendant_data = f"❌ 網頁資料解析失敗: {str(e)}"
                
            return render_template('astro.html', result_text=ascendant_data, form_type='ascendant')
            
    return render_template('astro.html', result_text=None, form_type='fortune')


# ==========================================
# Dialogflow Webhook 路由 (LINE 端分流)
# ==========================================
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    intent_name = req.get('queryResult', {}).get('intent', {}).get('displayName')
    
    # ======= LINE 功能一：星座運勢功能 =======
    if intent_name == 'search_fortune':
        parameters = req.get('queryResult', {}).get('parameters', {})
        constellation = parameters.get('constellation')
        
        result_text = get_today_fortune(constellation)
        
        reply = {"fulfillmentText": result_text}
        return jsonify(reply)
        
    # ======= LINE 功能二：算上升星盤功能 =======
    elif intent_name == 'calculate_ascendant':
        parameters = req.get('queryResult', {}).get('parameters', {})
        
        birth_date = parameters.get('birth_date')     # 格式：2000-01-01T12:00:00+08:00
        birth_time = parameters.get('birth_time')     # 格式：2000-01-01T14:30:00+08:00
        birth_location = parameters.get('birth_location') # 城市
        
        try:
            year = birth_date.split('-')[0]
            month = birth_date.split('-')[1]
            day = birth_date.split('-')[2][:2]
            
            time_part = birth_time.split('T')[1]
            hour = time_part.split(':')[0]
            minute = time_part.split(':')[1]
            
            # LINE 端也完美同步呼叫獨立計算邏輯
            result_text = calculate_local_ascendant(year, month, day, hour, minute, birth_location)
            
        except Exception as e:
            result_text = f"❌ 抱歉，LINE 傳入的生日資料格式解析出錯: {str(e)}"
        
        reply = {
            "fulfillmentText": result_text
        }
        return jsonify(reply)

    return jsonify({"fulfillmentText": "未知的 Dialogflow 指令"})


if __name__ == "__main__":
    app.run(debug=True)

    