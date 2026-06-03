import os
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder='templates')

# ==========================================
# 核心功能一：內建恆星時上升星座精算演算法
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
    
    # 3. 預設台灣觀測點 (東八區)
    timezone_offset = 8.0  
    lng = 121.50           
    lat = 25.05            
    
    # 計算地方平恆星時 (LST)
    local_time_hours = h + (mn / 60.0)
    utc_time_hours = local_time_hours - timezone_offset
    lst = gmst + utc_time_hours * 1.00273790935 + (lng / 15.0)
    lst_degrees = (lst * 15.0) % 360

    # 4. 根據黃赤交角計算天頂與上升點斜升運算
    epsilon = 23.4393 - 0.0130 * t  
    import math
    asc_rad = math.atan2(-math.cos(math.radians(lst_degrees)), 
                         math.sin(math.radians(lst_degrees)) * math.cos(math.radians(epsilon)) + 
                         math.tan(math.radians(lat)) * math.sin(math.radians(epsilon)))
    asc_deg = math.degrees(asc_rad) % 360
    
    # 5. 轉換至十二星座
    zodiac_signs = [
        "白羊座", "金牛座", "雙子座", "巨蟹座", "獅子座", "處女座",
        "天秤座", "天蠍座", "射手座", "摩羯座", "水瓶座", "雙魚座"
    ]
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
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
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
                year, month, day = b_date.split('-')
                hour, minute = b_time.split(':')
                ascendant_data = calculate_local_ascendant(year, month, day, hour, minute, b_loc)
            except Exception as e:
                ascendant_data = f"❌ 網頁資料解析失敗: {str(e)}"
                
            return render_template('astro.html', result_text=ascendant_data, form_type='ascendant')
            
    return render_template('astro.html', result_text=None, form_type='fortune')


# ==========================================
# Dialogflow Webhook 路由 (強力容錯版)
# ==========================================
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    intent_name = req.get('queryResult', {}).get('intent', {}).get('displayName')
    
    # ------- LINE 功能一：星座運勢功能 -------
    if intent_name == 'search_fortune':
        parameters = req.get('queryResult', {}).get('parameters', {})
        constellation = parameters.get('constellation', '')
        result_text = get_today_fortune(constellation)
        return jsonify({"fulfillmentText": result_text})
        
    # ------- LINE 功能二：算上升星盤功能 -------
    elif intent_name == 'calculate_ascendant':
        parameters = req.get('queryResult', {}).get('parameters', {})
        
        # 1. 讀取 Dialogflow 傳過來的原始參數
        raw_date = parameters.get('birth_date', '')
        raw_time = parameters.get('birth_time', '')
        raw_location = parameters.get('birth_location', '')
        
        # 將它們轉成字串，方便做後續防禦判斷
        birth_date = str(raw_date).strip()  
        birth_time = str(raw_time).strip()  
        
        # 2. 【核心防禦】檢查變數是否尚未填寫或破圖
        def is_invalid(val):
            return not val or '$' in val or '@' in val or 'sys.' in val or val.lower() == 'none' or val == ''

        if is_invalid(birth_date):
            return jsonify({"fulfillmentText": "請問妳的出生年月日是呢？（例如：20050906）"})
            
        if is_invalid(birth_time):
            return jsonify({"fulfillmentText": "收到日期了！那請問妳是在幾點幾分出生的呢？（例如：10:00）"})
            
        if is_invalid(str(raw_location)):
            return jsonify({"fulfillmentText": "最後一步囉！請問妳的出生城市在哪裡呢？（例如：台北市、嘉義縣）"})
            
        # 3. 資料到齊，開始進行極致的防呆格式解析
        try:
            # ---- A. 日期解析 ----
            if 'T' in birth_date:
                birth_date = birth_date.split('T')[0]
            if '-' in birth_date:
                year, month, day = birth_date.split('-')
            elif len(birth_date) == 8 and birth_date.isdigit():
                year, month, day = birth_date[0:4], birth_date[4:6], birth_date[6:8]
            else:
                raise ValueError("未知的日期格式")

            # ---- B. 時間解析 & 24小時制修正防呆 ----
            # Dialogflow 常把 "10:00" 自動當成 "22:00" (晚上10點)
            hour_str, minute_str = "12", "00"
            if 'T' in birth_time:
                time_part = birth_time.split('T')[1]
                hour_str = time_part.split(':')[0]
                minute_str = time_part.split(':')[1]
            elif ':' in birth_time:
                hour_str, minute_str = birth_time.split(':')
            elif len(birth_time) == 4 and birth_time.isdigit():
                hour_str, minute_str = birth_time[0:2], birth_time[2:4]

            hour = int(hour_str)
            minute = int(minute_str)

            # 【黃金防呆線】如果 Dialogflow 擅自判定為晚上 (22點)，但原對話文字中沒有提到"晚上/下午/PM"
            # 或者是妳在右側測試時單純打 "10:00"，我們自動幫她校正回早上的 10 點！
            resolved_query = req.get('queryResult', {}).get('queryText', '')
            if hour > 12 and not any(k in resolved_query for k in ['晚', '下午', 'pm', 'PM', '夜']):
                hour = hour - 12

            # 重新補零轉回字串
            final_hour = str(hour).zfill(2)
            final_minute = str(minute).zfill(2)

            # ---- C. 出生城市精準萃取 ----
            # 如果接收到的是字典（Dict），從中抓出 'admin-area' 或 'city'，避免噴出整串 JSON
            clean_location = "未知城市"
            if isinstance(raw_location, dict):
                clean_location = raw_location.get('admin-area') or raw_location.get('city') or raw_location.get('subadmin-area') or "未知城市"
            else:
                clean_location = str(raw_location)

            # 4. 呼叫解算函數，噴出完美成果！
            result_text = calculate_local_ascendant(year, month, day, final_hour, final_minute, clean_location)
            
        except Exception as e:
            result_text = f"❌ 抱歉，輸入的生日格式解析出錯: {str(e)}"
        
        return jsonify({"fulfillmentText": result_text})

    return jsonify({"fulfillmentText": "未知的 Dialogflow 指令"})


if __name__ == "__main__":
    app.run(debug=True)



    