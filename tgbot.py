import requests

def send_telegram_alert(bot_token, chat_id, photo_path, caption=""):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto?chat_id={chat_id}"
    params = {"caption": caption}
    with open(photo_path, 'rb') as img:
        response = requests.post(url, files={'photo': img}, params=params)

    if response.status_code == 200:
        print(f"Alert sent successfully to {chat_id}!")
    else:
        print(f"Failed to send alert to {chat_id}. Status code: {response.status_code}")
