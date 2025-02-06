import requests
import concurrent.futures
import re

# ====== 設定エリア ======
API_KEYS = [
     "AIzaSyBTNVkzjKD3sUNVUMlp_tcXWQMO-FpfrSo",  # gemini-2.0-flash-001 用
    "AIzaSyDfyltY3n2p8Ia4qrWJKk8gU8ZBTxsGKWI",  # 同じモデルにアクセスする複数のキー
    "AIzaSyCyHFSCTYR9T0a5zPn9yg-49eevJXqKP9g"
]

MODEL_NAME = "gemini-2.0-flash-001"

# 名前を3人分（ここでは固定）
NAMES = ["けんじ", "しんや", "たかし"]

def call_gemini_api(prompt: str, api_key: str) -> str:
    """
    gemini-2.0-flash-001 モデルに対し、指定の api_key を使って呼び出す。
    'content' が辞書の場合は 'value' を取り出して文字列化。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}

    print("[DEBUG] call_gemini_api >>>")
    print("API_KEY:", api_key[:10] + "...(省略)")
    print("Prompt:", prompt)
    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        return f"エラー: リクエスト送信失敗 -> {str(e)}"

    print("[DEBUG] Status:", response.status_code)
    print("[DEBUG] Response:", response.text)

    if response.status_code != 200:
        return f"エラー: {response.status_code} -> {response.text}"

    try:
        rjson = response.json()
        candidates = rjson.get("candidates", [])
        if not candidates:
            return "回答が見つかりません。(candidates空)"

        # 最初の候補から content を取り出す
        candidate0 = candidates[0]
        content_val = candidate0.get("content", "")
        if isinstance(content_val, dict):
            # { "parts": [...], "role": ... } のようなケース
            # さらに "value" がある場合は取り出す (可能性あり)
            content_str = content_val.get("value", "")
        else:
            content_str = str(content_val)

        content_str = content_str.strip()
        if not content_str:
            return "回答が見つかりません。(contentが空)"

        return remove_json_artifacts(content_str)
    except Exception as e:
        return f"エラー: JSON解析失敗 -> {str(e)}"

def remove_json_artifacts(text: str) -> str:
    """
    'parts': [{'text': ...}] などを簡易的に除去
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return cleaned.strip()

def make_prompt(name: str, question: str) -> str:
    """
    人ごとに違う prompt を作る例。ここでは単に「名前が回答する」という文面。
    """
    return (
        f"{name}が以下の質問に回答してください:\n"
        f"質問: {question}\n"
        "自由に考えてください。JSONやpartsなどは不要です。"
    )

def worker_task(name: str, question: str, api_key: str) -> str:
    """
    並列に実行するタスク。戻り値は "名前: 回答" の文字列。
    """
    prompt = make_prompt(name, question)
    result = call_gemini_api(prompt, api_key)
    return f"{name}: {result}"

def main():
    # 例: 3人に同じ質問を並行で投げる
    question = "官民共創施設を建てたいです。その名前を考えてください。愛媛県庁です。"

    # 3つのAPIキーを並列に使う例:
    # NAMES[i] + API_KEYS[i] でペアにする想定
    # 数が合わない場合は工夫が必要
    if len(API_KEYS) < 3:
        print("ERROR: API_KEYS が3つ以上必要です。")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i in range(3):
            # i番目の人 + i番目のキー
            f = executor.submit(worker_task, NAMES[i], question, API_KEYS[i])
            futures.append(f)

        # 結果を集める
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            print("=== 取得結果 ===")
            print(res)
            print()

if __name__ == "__main__":
    main()
