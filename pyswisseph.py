from kerykeion import KrInstance, OutputHelper

def calculate_ascendant(year, month, day, hour, minute, city="Taipei"):
    """
    輸入出生年月日、時分、以及出生城市（預設台北），精準計算上升星座
    """
    try:
        # 1. 建立一個占星實體（kerykeion 會自動處理 GMT 時差與經緯度修正）
        # 參數依序為：姓名(自訂), 年, 月, 日, 時, 分, 城市
        user_chart = KrInstance("User", year, month, day, hour, minute, city)
        
        # 2. 直接從星盤資料中抓取「第一宮宮頭 (First House Point)」，也就是上升點 (Ascendant)
        ascendant_info = user_chart.first_house
        
        # 3. 提取上升星座的中文名稱
        # 套件回傳的英文會是 "Aries", "Taurus" 等，我們用字典轉換成中文
        zodiac_mapping = {
            "Aries": "牡羊座 ♈", "Taurus": "金牛座 ♉", "Gemini": "雙子座 ♊",
            "Cancer": "巨蟹座 ♋", "Leo": "獅子座 ♌", "Virgo": "處女座 ♍",
            "Libra": "天秤座 ♎", "Scorpio": "天蠍座 ♏", "Sagittarius": "射手座 ♐",
            "Capricorn": "魔羯座 ♑", "Aquarius": "水瓶座 ♒", "Pisces": "雙魚座 ♓"
        }
        
        english_sign = ascendant_info.sign
        chinese_zodiac = zodiac_mapping.get(english_sign, "未知星座")
        position_degree = round(ascendant_info.position, 2) # 在該星座的第幾度
        
        return {
            "status": "success",
            "ascendant": chinese_zodiac,
            "degree": position_degree,
            "longitude": user_chart.lng, # 城市經度
            "latitude": user_chart.lat    # 城市緯度
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ======= 測試計算 =======
if __name__ == "__main__":
    # 測試：2026年6月3日 晚上 20:54 在台北出生的人
    result = calculate_ascendant(2026, 6, 3, 20, 54, "Taipei")
    
    if result["status"] == "success":
        print("🔮 上升星座計算成功！")
        print(f"經緯度座標：經度 {result['longitude']} / 緯度 {result['latitude']}")
        print(f"您的上升星座是：{result['ascendant']} （位於該星座 {result['degree']} 度）")
    else:
        print(f"計算失敗：{result['message']}")