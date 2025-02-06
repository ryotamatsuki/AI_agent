import requests
import re
import concurrent.futures

# ============== 設定エリア ==============
API_KEYS = [
    "AIzaSyBTNVkzjKD3sUNVUMlp_tcXWQMO-FpfrSo",  # gemini-2.0-flash-001 用
    "AIzaSyDfyltY3n2p8Ia4qrWJKk8gU8ZBTxsGKWI",  # 同じモデルにアクセスする複数のキー
    "AIzaSyCyHFSCTYR9T0a5zPn9yg-49eevJXqKP9g"
]

MODEL_NAME = "gemini-2.0-flash-001"
NAMES = ["けんじ", "しんや", "たかし"]

def call_gemini_api(prompt: str, api_key: str) -> str:
    """
    gemini-2.0-flash-001 モデルを呼び出し。
    'content' が辞書の場合は 'value' キーを取り出す。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            return f"エラー: {response.status_code} {response.text}"

        rjson = response.json()
        candidates = rjson.get("candidates", [])
        if not candidates:
            return "回答が見つかりません。(candidatesが空)"

        candidate0 = candidates[0]
        content_val = candidate0.get("content", "")
        if isinstance(content_val, dict):
            # もし辞書型なら .get("value") を使う
            content_str = content_val.get("value", "")
        else:
            content_str = str(content_val)
        content_str = content_str.strip()
        if not content_str:
            return "回答が見つかりません。(contentが空)"
        return content_str
    except Exception as e:
        return f"エラー: {str(e)}"

def remove_json_artifacts(text: str) -> str:
    if not isinstance(text, str):
        text = str(text) if text else ""
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    return re.sub(pattern, "", text, flags=re.DOTALL)

def task(name: str, question: str, api_key: str) -> str:
    """
    1人分の回答を並列で取るためのタスク。
    """
    prompt = (
        f"{name}が下記の質問に回答してください:\n"
        f"質問: {question}\n"
        "長さの制限はありません。"
    )
    raw = call_gemini_api(prompt, api_key)
    cleaned = remove_json_artifacts(raw)
    return f"{name}: {cleaned}"

def main():
    question = "官民共創施設を建てたいです。その名前を考えください。\n愛媛県庁です。"

    # 3つのタスクを並列に実行
    # それぞれ NAMES[i] と API_KEYS[i] を対応付ける例 (キー数と名前数が同じ前提)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i in range(3):
            futures.append(executor.submit(task, NAMES[i], question, API_KEYS[i]))

        # 結果を取得
        for f in concurrent.futures.as_completed(futures):
            result = f.result()  # "けんじ: 〇〇" のような形式
            print(result)

if __name__ == "__main__":
    main()
