import os
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder='templates')

# --- 保持你原本的爬蟲函式不變 ---
def get_today_fortune(constellation_name):
    astro_map = {
        "牡羊座": 0, "金牛座": 1, "雙子座": 2, "巨蟹座": 3,
        "獅子座": 4, "處女座": 5, "天秤座": 6, "天蠍座": 7,
        "射手座": 8, "摩羯座": 9, "水瓶座": 10, "雙魚座": 11
    }
    
    if constellation_name not in astro_map:
        return None
        
    astro_id = astro_map[constellation_name]
    url = f"https://astro.click108.com.tw/daily_{astro_id}.php?iAstro={astro_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        fortune_section = soup.find("div", class_="TODAY_CONTENT")
        
        if fortune_section:
            return fortune_section.get_text(strip=True)
        return "暫時無法取得運勢資料。"
    except Exception as e:
        return f"發生錯誤: {str(e)}"

# --- 原本的網頁路由保持不變 ---
@app.route("/", methods=["GET", "POST"])
def astro_search():
    fortune = None
    search_keyword = ""
    if request.method == "POST":
        search_keyword = request.form.get("keyword", "").strip()
        if search_keyword:
            if not search_keyword.endswith("座"):
                search_keyword += "座"
            fortune = get_today_fortune(search_keyword)
    return render_template("astro.html", fortune=fortune, keyword=search_keyword)


# ================= 新增：Dialogflow Webhook 路由 =================
@app.route("/webhook", methods=["POST"])
def webhook():
    # 1. 取得 Dialogflow 傳來的 JSON 資料
    req = request.get_json(silent=True, force=True)
    
    # 2. 解析出所需的參數 (從 intent 的 parameters 中取得 constellation)
    # 注意：請確保你在 Dialogflow 裡面設定的 Parameter Name 叫做 "constellation"
    try:
        parameters = req.get('queryResult', {}).get('parameters', {})
        constellation = parameters.get('constellation', '')
    except Exception:
        constellation = ''

    # 3. 防呆處理：補上「座」字
    if constellation and not constellation.endswith("座"):
        constellation += "座"

    # 4. 呼叫爬蟲抓取運勢
    if constellation in ["牡羊座", "金牛座", "雙子座", "巨蟹座", "獅子座", "處女座", "天秤座", "天蠍座", "射手座", "摩羯座", "水瓶座", "雙魚座"]:
        fortune_text = get_today_fortune(constellation)
        reply = f"【{constellation}的今日運勢】\n{fortune_text}"
    else:
        # 如果使用者沒說星座，或者 Dialogflow 還沒抓到星座參數
        reply = "請告訴我你想查詢什麼星座的運勢呢？（例如：雙子座）"

    # 5. 回傳 Dialogflow 要求的標準 JSON 格式
    response_fulfillment = {
        "fulfillmentText": reply
    }
    
    return jsonify(response_fulfillment)

if __name__ == "__main__":
    app.run(debug=True)





    