import os
import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='templates')

# 黃道十二星座標準順序（用於順移計算）
ZODIAC_LIST = [
    "白羊座", "金牛座", "雙子座", "巨蟹座", "獅子座", "處女座",
    "天秤座", "天蠍座", "射手座", "摩羯座", "水瓶座", "雙魚座"
]

# ==========================================
# 爬蟲模組：2026 年水星逆行資料爬取
# ==========================================
def crawl_mercury_retrograde():
    """
    爬取丹尼爾天空網頁，並精確過濾出 2026 年的水星逆行時間資料
    """
    url = "https://www.taipeidaniel.idv.tw/articles-astrology-mercuryrd-2010-2029.htm"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.encoding = 'utf-8' 
        
        if response.status_code != 200:
            print(f"【水逆爬蟲】網頁請求失敗，錯誤代碼：{response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        all_text = soup.get_text()
        lines = all_text.split('\n')
        
        mercury_2026_events = []
        for line in lines:
            line = line.strip()
            if "2026" in line and ("逆行" in line or "～" in line or "~" in line):
                clean_line = re.sub(r'\s+', ' ', line) 
                if clean_line not in mercury_2026_events:
                    mercury_2026_events.append(clean_line)
                
        return mercury_2026_events
    except Exception as e:
        print(f"【水逆爬蟲】爬取過程中發生錯誤: {e}")
        return None

# ======= 全域變數：優化系統效能（系統開機時只爬一次） =======
print("🚀 [系統啟動] 正在預先爬取 2026 年水逆資料並記錄至記憶體...")
MERCURY_DATA_2026 = crawl_mercury_retrograde()

if MERCURY_DATA_2026:
    print(f"✅ [系統啟動成功] 已成功載入 {len(MERCURY_DATA_2026)} 筆水逆行事曆資料！")
else:
    print("⚠️ [系統警告] 水逆資料載入失敗，請確認網路連線或目標網頁是否更動。")
# =========================================================


# ==========================================
# 核心功能一：24小時制 - 上升星座口訣公式推算
# ==========================================
def get_sun_sign(month, day):
    """根據月日判斷出生的太陽星座"""
    m, d = int(month), int(day)
    if (m == 3 and d >= 21) or (m == 4 and d <= 19): return "白羊座"
    if (m == 4 and d >= 20) or (m == 5 and d <= 20): return "金牛座"
    if (m == 5 and d >= 21) or (m == 6 and d <= 21): return "雙子座"
    if (m == 6 and d >= 22) or (m == 7 and d <= 22): return "巨蟹座"
    if (m == 7 and d >= 23) or (m == 8 and d <= 22): return "獅子座"
    if (m == 8 and d >= 23) or (m == 9 and d <= 22): return "處女座"
    if (m == 9 and d >= 23) or (m == 10 and d <= 23): return "天秤座"
    if (m == 10 and d >= 24) or (m == 11 and d <= 22): return "天蠍座"
    if (m == 11 and d >= 23) or (m == 12 and d <= 21): return "射手座"
    if (m == 12 and d >= 22) or (m == 1 and d <= 19): return "摩羯座"
    if (m == 1 and d >= 20) or (m == 2 and d <= 18): return "水瓶座"
    return "雙魚座"

def calculate_formula_ascendant(month, day, hour_str, minute_str):
    """
    全面採用標準 24 小時制（0 ~ 23 點）計算：
    1. 基準點：清晨 06:00 (以 24 點鐘制度計算為 360 分鐘) 出生，上升星座 = 太陽星座。
    2. 每往後延遲 120 分鐘（2個小時），上升星座向後順移一個星座。
    3. 【保底防呆】若遇到不知道時間，則固定以中午 12:00（24制）進行盲測。
    """
    is_unknown_time = False
    h_str = str(hour_str).strip()
    m_str = str(minute_str).strip()
    
    # 檢查是否啟動預設中午 12 點保底機制
    if not h_str or any(k in h_str for k in ['不知', '忘記', '不確', 'none', 'None', 'null', '不知道']):
        h = 12
        m = 0
        is_unknown_time = True
    else:
        try:
            h = int(h_str)
            m = int(m_str)
            
            # 確保輸入的小時符合 24 小時制規範（防範前端髒資料）
            if h < 0 or h > 23:
                h = 12
                m = 0
                is_unknown_time = True
        except ValueError:
            h = 12
            m = 0
            is_unknown_time = True
    
    sun_sign = get_sun_sign(month, day)
    base_index = ZODIAC_LIST.index(sun_sign)
    
    # 將出生時間換算成當天的總分鐘數
    birth_time_in_minutes = h * 60 + m
    base_time_in_minutes = 6 * 60  # 清晨 06:00
    
    # 計算時間差（24小時制循環防呆）
    time_diff = birth_time_in_minutes - base_time_in_minutes
    if time_diff < 0:
        time_diff += 1440  # 處理 00:00 ~ 05:59 跨過午夜的分鐘補償
        
    shift_steps = time_diff // 120
    final_index = (base_index + shift_steps) % 12
    ascendant_sign = ZODIAC_LIST[final_index]
    
    emoji_map = {
        "白羊座": "白羊座 ♈", "金牛座": "金牛座 ♉", "雙子座": "雙子座 ♊",
        "巨蟹座": "巨蟹座 ♋", "獅子座": "獅子座 ♌", "處女座": "處女座 ♍",
        "天秤座": "天秤座 ♎", "天蠍座": "天蠍座 ♏", "射手座": "射手座 ♐",
        "摩羯座": "摩羯座 ♑", "水瓶座": "水瓶座 ♒", "雙魚座": "雙魚座 ♓"
    }
    
    display_sign = emoji_map[ascendant_sign].replace("白羊", "牡羊")
    display_sun = sun_sign.replace("白羊", "牡羊")
    time_display = f"{str(h).zfill(2)}:{str(m).zfill(2)}"
    
    result = (
        f"✨ 妳的上升星座是：{display_sign}✨\n\n"
        f"1️⃣ 妳的生日是 {month}月{day}日，太陽星座為【{display_sun}】。\n"
        f"上升星座代表妳出生時，東方地平線正升起的星座，是妳的外在人格面具"
    )
    
    if is_unknown_time:
        result += (
            "\n\n💡【貼心提示】\n"
            "因為妳不確定具體出生時間，系統已自動使用中午 2:00進行。"
        )
        
    return result

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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
        
        if form_type == 'fortune':
            keyword = request.form.get('keyword')
            fortune_data = get_today_fortune(keyword) 
            return render_template('astro.html', result_text=fortune_data, keyword=keyword, form_type='fortune')
            
        elif form_type == 'ascendant':
            b_date = request.form.get('birth_date')     
            b_time = request.form.get('birth_time')     
            
            try:
                year, month, day = b_date.split('-')
                if b_time:
                    hour, minute = b_time.split(':')
                else:
                    hour, minute = "不知道", "不知道" 
                    
                ascendant_data = calculate_formula_ascendant(month, day, hour, minute)
            except Exception as e:
                ascendant_data = f"網頁資料解析失敗: {str(e)}"
                
            return render_template('astro.html', result_text=ascendant_data, form_type='ascendant')
            
    return render_template('astro.html', result_text=None, form_type='fortune')


# ==========================================
# Dialogflow Webhook 路由（完美相容 24 小時制解析）
# ==========================================
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    intent_name = req.get('queryResult', {}).get('intent', {}).get('displayName')
    
    # LINE 功能一：星座運勢
    if intent_name == 'search_fortune':
        parameters = req.get('queryResult', {}).get('parameters', {})
        constellation = parameters.get('constellation', '')
        result_text = get_today_fortune(constellation)
        return jsonify({"fulfillmentText": result_text})
        
    # LINE 功能二：算上升星座（改為相容 24H 機制）
    elif intent_name == 'calculate_ascendant':
        parameters = req.get('queryResult', {}).get('parameters', {})
        
        raw_date = parameters.get('birth_date', '')
        raw_time = parameters.get('birth_time', '')
        
        birth_date = str(raw_date).strip()  
        birth_time = str(raw_time).strip()  
        
        # 💥 除錯日誌：幫妳在終端機印出 Dialogflow 丟過來的真實長相，方便排查
        print("====== 🔍 [Dialogflow 參數除錯] ======")
        print(f"原始 birth_date: {raw_date}")
        print(f"原始 birth_time: {raw_time}")
        print("=======================================")

        def is_invalid(val):
            return not val or '$' in val or '@' in val or 'sys.' in val or val.lower() == 'none' or val == ''

        # 1. 檢查日期
        if is_invalid(birth_date):
            return jsonify({"fulfillmentText": "請問妳的出生年月日是？（例如：2005-09-06）"})
            
        # 2. 檢查時間並判斷使用者是否說了「不知道時間」
        resolved_query = req.get('queryResult', {}).get('queryText', '')
        user_says_unknown = any(k in resolved_query for k in ['不知道', '忘記了', '不確定', '不曉得', '查不到'])
        
        if is_invalid(birth_time) and not user_says_unknown:
            return jsonify({"fulfillmentText": "請問妳是在幾點幾分出生的呢？（例如：14:20）如果不知道，請輸入不知道"})
            
        try:
            # ---- A. 日期精確解析 ----
            if 'T' in birth_date:
                birth_date = birth_date.split('T')[0]
            if '-' in birth_date:
                year, month, day = birth_date.split('-')
            elif len(birth_date) == 8 and birth_date.isdigit():
                year, month, day = birth_date[0:4], birth_date[4:6], birth_date[6:8]
            else:
                raise ValueError("未知的日期格式")

            # ---- B. 24小時制時間精確解析 ----
            if user_says_unknown:
                hour_str, minute_str = "不知道", "不知道"
            else:
                hour_str, minute_str = "12", "00"
                # 處理 Dialogflow 經典 ISO 字串: 2026-06-04T14:30:00+08:00
                if 'T' in birth_time:
                    time_part = birth_time.split('T')[1]  # 拿 14:30:00+08:00
                    time_clean = time_part.split('+')[0]  # 拿 14:30:00
                    hour_str = time_clean.split(':')[0]
                    minute_str = time_clean.split(':')[1]
                elif ':' in birth_time:
                    # 處理標準 14:30 格式
                    parts = birth_time.split(':')
                    hour_str = parts[0]
                    minute_str = parts[1]
                elif len(birth_time) == 4 and birth_time.isdigit():
                    # 處理 1430 格式
                    hour_str, minute_str = birth_time[0:2], birth_time[2:4]

            # 3. 呼叫全面更新為 24H 的推算公式
            result_text = calculate_formula_ascendant(month, day, hour_str, minute_str)
            
        except Exception as e:
            result_text = f"抱歉，輸入的生日格式出錯: {str(e)}"
        
        return jsonify({"fulfillmentText": result_text})

    # LINE 新增功能三：查詢 2026 水逆行事曆
    elif intent_name == 'ask_mercury_retrograde':
        if MERCURY_DATA_2026:
            reply_text = "⚠️ 【2026 星座行事曆】\n幫你查到今年的水逆時間囉！：\n\n"
            for idx, event in enumerate(MERCURY_DATA_2026, 1):
                reply_text += f"🔮 第 {idx} 波水逆：\n{event}\n\n"
            reply_text += "💡 溫馨提示：水逆期間容易思緒混亂、心情低落還有通訊不良或設備損壞，多點耐心、對自己要好點歐！"
        else:
            reply_text = "抱歉，目前無法連線行星曆資料庫，晚點再幫你查！"
            
        return jsonify({"fulfillmentText": reply_text})

    return jsonify({"fulfillmentText": "未知的 Dialogflow 指令"})


if __name__ == "__main__":
    app.run(debug=True)