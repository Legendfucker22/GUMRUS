from flask import Flask, render_template_string, request, jsonify
import requests
import re
import time

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # चेक करें कि दोनों फ़ाइलें मौजूद हैं या नहीं
        if 'cookies_file' not in request.files or 'comments_file' not in request.files:
            return jsonify({"status": "error", "message": "कृपया सभी फ़ाइलें अपलोड करें."})

        cookies_file = request.files['cookies_file']
        comments_file = request.files['comments_file']
        post_url = request.form['post_url']
        commenter_name = request.form['commenter_name']
        delay = int(request.form['delay'])

        # फ़ाइलों से डेटा पढ़ें
        cookies_data = cookies_file.read().decode('utf-8').splitlines()
        comments = comments_file.read().decode('utf-8').splitlines()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; RMX2144 Build/RKQ1.201217.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.71 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/375.1.0.28.111;]'
        }

        # कुकीज़ को वैलिडेट करें
        valid_cookies = []
        for cookie in cookies_data:
            try:
                response = requests.get('https://business.facebook.com/business_locations', headers=headers, cookies={'Cookie': cookie})
                if response.status_code == 200:
                    valid_cookies.append(cookie)
            except Exception:
                continue

        if not valid_cookies:
            return jsonify({"status": "error", "message": "कोई वैध कुकी नहीं मिली."})

        target_id = re.search(r'target_id=(\d+)', post_url)
        if not target_id:
            return jsonify({"status": "error", "message": "अमान्य फेसबुक पोस्ट URL."})

        target_id = target_id.group(1)
        x, cookie_index = 0, 0

        results = []

        while True:
            try:
                teks = comments[x].strip()
                comment_with_name = f"{commenter_name}: {teks}"

                current_cookie = valid_cookies[cookie_index]
                data = {
                    'message': comment_with_name,
                }

                response2 = requests.post(f'https://graph.facebook.com/{target_id}/comments/', data=data, cookies={'Cookie': current_cookie}).json()

                if 'id' in response2:
                    results.append({
                        "status": "success",
                        "comment": comment_with_name,
                        "cookie": current_cookie,
                        "message": "कमेंट सफलतापूर्वक पोस्ट हो गया।"
                    })
                else:
                    results.append({
                        "status": "failure",
                        "comment": comment_with_name,
                        "cookie": current_cookie,
                        "message": "कमेंट पोस्ट नहीं हुआ।"
                    })

                x = (x + 1) % len(comments)
                cookie_index = (cookie_index + 1) % len(valid_cookies)
                time.sleep(delay)

            except Exception as e:
                results.append({
                    "status": "error",
                    "comment": comment_with_name,
                    "cookie": current_cookie,
                    "message": f"त्रुटि: {str(e)}"
                })
                break

        return jsonify({"status": "completed", "results": results})

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Facebook Commenter</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #f5f7fa, #c3cfe2);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                form {
                    background: #ffffff;
                    padding: 2em;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    width: 100%;
                    max-width: 600px;
                }
                h2 {
                    text-align: center;
                    color: #333;
                }
                div + div {
                    margin-top: 1em;
                }
                label {
                    display: block;
                    margin-bottom: 8px;
                    color: #555;
                }
                input, textarea {
                    border: 1px solid #ddd;
                    font: 1em sans-serif;
                    width: 100%;
                    box-sizing: border-box;
                    padding: 10px;
                    border-radius: 5px;
                }
                button {
                    padding: 0.7em;
                    color: #fff;
                    background-color: #007BFF;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 1em;
                    width: 100%;
                    margin-top: 1em;
                }
                button:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <form method="POST" enctype="multipart/form-data">
                <h2>Facebook Commenter</h2>
                <div>
                    <label>Cookies File:</label>
                    <input type="file" name="cookies_file" required>
                </div>
                <div>
                    <label>Comments File:</label>
                    <input type="file" name="comments_file" required>
                </div>
                <div>
                    <label>Facebook Post URL:</label>
                    <input type="text" name="post_url" required>
                </div>
                <div>
                    <label>Commenter Name:</label>
                    <input type="text" name="commenter_name" required>
                </div>
                <div>
                    <label>Delay (in seconds):</label>
                    <input type="text" name="delay" required>
                </div>
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
    ''')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
