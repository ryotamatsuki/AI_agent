import streamlit as st
import requests
import re
import random

# ==========================
#   設定エリア
# ==========================
API_KEY = "AIzaSyDfyltY3n2p8Ia4qrWJKk8gU8ZBTxsGKWI"  # gemini-2.0-flash-001 用の有効なキー
MODEL_NAME = "gemini-2.0-flash-001"  

NAMES = ["ゆかり", "しんや", "みのる", "たかし", "けんじ", "あやこ", "りな"]

def call_gemini_api(prompt: str) -> str:
    """
    gemini-2.0-flash-001 モデルを呼び出し、
    指定のプロンプトに基づく回答を取得。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}

    print("[DEBUG] Prompt:\n", prompt)

    # ---- リクエスト送信 ----
    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print("[DEBUG] Network error:", e)
        return f"エラー: ネットワーク接続失敗 -> {str(e)}"

    print("[DEBUG] Status code:", response.status_code)
    print("[DEBUG] Response text:", response.text)

    if response.status_code != 200:
        return f"エラー: ステータス {response.status_code} -> {response.text}"

    try:
        rjson = response.json()
        candidates = rjson.get("candidates", [])
        if not candidates:
            return "回答が見つかりませんでした。(candidatesが空)"

        candidate0 = candidates[0]
        print("[DEBUG] candidate0:", candidate0)

        # 2.0-flash では "content" が dict の場合があり、"value" に文章が入ることがある
        content_val = candidate0.get("content", "")
        print("[DEBUG] content_val:", content_val, type(content_val))

        # 辞書の場合は "value" キーを使う
        if isinstance(content_val, dict):
            content_str = content_val.get("value", "")
            if not isinstance(content_str, str):
                content_str = str(content_str)
        elif isinstance(content_val, list):
            content_str = str(content_val)
        else:
            content_str = str(content_val)

        content_str = content_str.strip()
        if not content_str:
            return "回答が見つかりませんでした。(contentが空)"
        return content_str
    except Exception as e:
        print("[DEBUG] JSON parse error:", e)
        return f"エラー: JSON解析失敗 -> {str(e)}"

def remove_json_artifacts(text: str) -> str:
    """
    'parts': [{'text': ...}] など JSON 的な不要表記を除去
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return cleaned

def create_random_names() -> list:
    """日本人名をランダムに3名返す。"""
    return random.sample(NAMES, 3)

def display_text_in_box(text: str):
    """会話や回答を枠で表示"""
    st.markdown(
        f"""<div style="border:1px solid #ddd; border-radius:5px; padding:8px; margin-bottom:8px;">
        {text}
        </div>""",
        unsafe_allow_html=True
    )

# =============== Streamlit アプリ ===============
st.title("ぼくのともだち - 文字数制限なし")

# セッションデータ
if "names" not in st.session_state:
    st.session_state["names"] = []
if "initial_answers" not in st.session_state:
    st.session_state["initial_answers"] = {}
if "discussion" not in st.session_state:
    st.session_state["discussion"] = ""

question = st.text_area("最初の質問を入力してください", placeholder="ここに質問を入力")

# --------------------
#  ボタン1: 初回回答
# --------------------
if st.button("初回回答を取得"):
    if not question.strip():
        st.warning("質問を入力してください。")
    else:
        st.session_state["names"] = create_random_names()
        st.write("今回の登場人物:", ", ".join(st.session_state["names"]))

        answers_dict = {}
        for name in st.session_state["names"]:
            prompt = (
                f"{name}が以下の質問に回答してください。\n"
                f"質問: {question}\n"
                "制限は特になし。日本語で自由に答えてください。"
            )
            raw_answer = call_gemini_api(prompt)
            cleaned = remove_json_artifacts(raw_answer)
            # 文字数制限をなくし、結果そのまま使用
            if not cleaned.strip():
                cleaned = "（回答なし）"
            answers_dict[name] = cleaned
        
        st.session_state["initial_answers"] = answers_dict
        st.write("### 初回回答")
        for nm, ans in answers_dict.items():
            st.markdown(f"**{nm}**: {ans}")

        # 会話履歴を初期化
        st.session_state["discussion"] = ""

# --------------------
#  ボタン2: 会話を進める
# --------------------
if st.button("会話を進める"):
    if not st.session_state["initial_answers"]:
        st.warning("先に『初回回答を取得』してください。")
    else:
        prompt_discussion = (
            "これまでの会話:\n"
            f"{st.session_state['discussion']}\n\n"
            f"ユーザーの質問: {question}\n\n"
            "初回回答:\n"
        )
        for nm, ans in st.session_state["initial_answers"].items():
            prompt_discussion += f"{nm}: {ans}\n"

        prompt_discussion += (
            "\n上
