import requests
from bs4 import BeautifulSoup
import re

def crawl_mercury_retrograde():
    """
    爬取丹尼爾天空網頁，並精確過濾出 2026 年的水星逆行時間資料
    """
    url = "https://www.taipeidaniel.idv.tw/articles-astrology-mercuryrd-2010-2029.htm"
    
    # 偽裝成瀏覽器發送請求
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8' # 強制指定編碼，防範中文字亂碼
        
        if response.status_code != 200:
            print(f"網頁請求失敗，錯誤代碼：{response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        all_text = soup.get_text()
        lines = all_text.split('\n')
        
        mercury_2026_events = []
        
        for line in lines:
            line = line.strip()
            # 條件：必須包含 2026，且有逆行或時間～符號
            if "2026" in line and ("逆行" in line or "～" in line or "~" in line):
                clean_line = re.sub(r'\s+', ' ', line) # 清洗掉多餘的空格
                
                # 防範重複加入相同的句子
                if clean_line not in mercury_2026_events:
                    mercury_2026_events.append(clean_line)
                
        return mercury_2026_events

    except Exception as e:
        print(f"爬取過程中發生錯誤: {e}")
        return None

# 當作獨立檔案執行時（py mercury_spider.py）才會跑下面這段測試
if __name__ == "__main__":
    print("🔮 獨立測試：開始爬取 2026 年水星逆行資料...")
    results = crawl_mercury_retrograde()
    if results:
        print(f"\n✅ 成功抓取到 {len(results)} 筆資料：")
        for idx, event in enumerate(results, 1):
            print(f"第 {idx} 波：{event}")
    else:
        print("❌ 未抓取到相關資料。")