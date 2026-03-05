# encoding:utf-8
import os
import sys
import json
import requests
from datetime import datetime, timezone, timedelta
from html import escape

# PushPlus官方API地址（已修正为HTTPS，避免http请求失败）
PUSHPLUS_API = "https://www.pushplus.plus/send"
BEIJING_TZ = timezone(timedelta(hours=8))

def send_notification(token, title, content, template="markdown"):
    """发送PushPlus通知"""
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": template,
    }
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8")
    try:
        response = requests.post(PUSHPLUS_API, data=body, headers=headers, timeout=30)
        result = response.json()
        if result.get("code") == 200:
            print(f"推送成功: {title}")
        else:
            print(f"推送失败: {result.get('msg')}")
        return result
    except Exception as e:
        print(f"推送请求异常: {e}")
        return {"code": -1, "msg": str(e)}

def get_wb3_calendar_data():
    """获取Web3日历数据"""
    print(f"[LOG] 开始获取 Web3 日历数据: {datetime.now()}")
    url = "https://www.chaincatcher.com/pc/calendar/v2/list"
    
    # 准备请求数据（使用北京时间）
    today = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
    print(f"[LOG] 请求日期: {today}")
    payload = {
        "eventType": 5,
        "eventDateStart": today,
        "eventDateEnd": today
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        print("[LOG] 发起 API 请求...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"[ERROR] API 请求失败，状态码: {response.status_code}")
            return None
            
        data = response.json()
        result_code = data.get('result', 0)
        if result_code != 1:
            print(f"[ERROR] API 返回错误结果码: {result_code}, 消息: {data.get('message', 'Unknown')}")
            return None
        
        calendar_data = data.get('data', [])
        print(f"[LOG] 获取到 {len(calendar_data)} 条日历数据")
        
        # 生成Markdown格式内容（适配PushPlus的markdown模板）
        markdown_content = generate_markdown_content(calendar_data)
        return markdown_content
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] 响应不是有效的JSON格式: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 获取数据时发生未知错误: {e}")
        return None

def generate_markdown_content(data):
    """生成Markdown格式的Web3日历内容"""
    if not data:
        content = """### 📅 Web3每日重大事件
今日暂无重大Web3事件

---
> 数据来源：链捕手 | 推送时间：{time}
""".format(time=datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S'))
        return content
    
    # 构建Markdown表格
    markdown = """### 📅 Web3每日重大事件

| 日期 | 事件 |
|------|------|
"""
    for item in data:
        event_date = escape(str(item.get('eventDate', '')))
        title = escape(str(item.get('title', '')))
        markdown += f"| {event_date} | {title} |\n"
    
    markdown += f"""
---
> 数据来源：链捕手 | 推送时间：{datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}
"""
    return markdown

def main():
    # 获取PushPlus Token
    token = os.environ.get("PUSHPLUS_TOKEN")
    if not token:
        print("错误: 未设置 PUSHPLUS_TOKEN 环境变量")
        sys.exit(1)

    # 获取当前时间（北京时间）
    now = datetime.now(BEIJING_TZ)
    title = f"Web3每日重大事件 - {now.strftime('%m月%d日')}"

    # 获取Web3日历数据
    web3_content = get_wb3_calendar_data()
    
    # 处理数据获取失败的情况
    if not web3_content:
        web3_content = f"""### 📅 Web3每日重大事件
❌ 今日无法获取Web3日历数据

**错误原因**：API请求失败或数据解析异常
**尝试时间**：{now.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

---
> 此消息由 GitHub Actions 自动发送
"""

    # 发送PushPlus通知
    send_notification(token, title, web3_content)

if __name__ == "__main__":
    main()
