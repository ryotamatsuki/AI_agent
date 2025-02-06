import streamlit as st
import requests
import re
import random

# ==========================
#   設定エリア
# ==========================
API_KEY = "AIzaSyDfyltY3n2p8Ia4qrWJKk8gU8ZBTxsGKWI"  # gemini-2.0-flash-001 用の有効なキー
MODEL_NAME = "gemini-2.0-flash-001"  # 2.0-flash 向けモデル

NAMES = ["ゆかり", "しんや", "みのる", "たかし", "けんじ", "あやこ", "りな"]

# ==========================
#   関数定義
# ==========================

def call_gemini_api(prompt: str) -> str:
    """
    gemini-2.0-flash-001 モデルを呼び出し、指定のプロンプトに基づく回答を取得。
    content が dict の場合は 'value' キーを取り出す。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}

    print("[DEBUG] Sending prompt:\n", prompt)

    # ---- リクエスト送信 ----
    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print("[DEBUG] Network error:", e)
        return f"エラー: ネットワーク接続失敗 -> {str(e)}"

    print("[DEBUG] Status code:", response.status_code)
    print("[DEBUG] Response text:", response.text)

    # ---- ステータスチェック ----
    if response.status_code != 200:
        return f"エラー: ステータス {response.status_code} -> {response.text}"

    # ---- JSON解析 ----
    try:
        rjson = response.json()
        candidates = rjson.get("candidates", [])
        if not candidates:
            return "回答が見つかりませんでした。(candidatesが空)"

        candidate0 = candidates[0]
        print("[DEBUG] candidate0:", candidate0)

        # candidate0["content"] が文字列でなく dict の可能性
        content_val = candidate0.get("content", "")
        print("[DEBUG] content_val:", content_val, type(content_val))

        # 辞書の場合、キー "value" を取り出すか、文字列化する
        if isinstance(content_val, dict):
            # 例: {"type": "text", "value": "ここに文章..."} など
            content_str = content_val.get("value", "")
            if not isinstance(content_str, str):
                content_str = str(content_str)
        elif isinstance(content_val, list):
            # リストの場合も文字列化
            content_str = str(content_val)
        else:
            # 文字列 or 空
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
    モデルが 'parts': [{'text': ...}] や 'role': 'model' といったJSONらしき表記を返した場合に除去。
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return cleaned

def short_text(text: str, limit=50) -> str:
    """
    指定文字数(デフォルト50)までに切り詰める。空や非文字列にも対応。
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    t = text.strip().replace("\n", " ")
    return t if len(t) <= limit else t[:limit] + "…"

def create_random_names() -> list:
    """日本人名をランダムに3名返す。"""
    return random.sample(NAMES, 3)

def display_text_in_box(text: str):
    """テキストをHTML枠で囲んで表示。"""
    st.markdown(
        f"""<div style="border:1px solid #ddd; border-radius:5px; padding:8px; margin-bottom:8px;">
        {text}
        </div>""",
        unsafe_allow_html=True
    )

# =============== Streamlit アプリ ===============
st.title("ぼくのともだち - Gemini 2.0-flash会話")

# セッションステート
if "names" not in st.session_state:
    st.session_state["names"] = []
if "initial_answers" not in st.session_state:
    st.session_state["initial_answers"] = {}
if "discussion" not in st.session_state:
    st.session_state["discussion"] = ""

question = st.text_area("最初の質問を入力してください", placeholder="ここに質問を入力")

# ------- ボタン1: 初回回答を取得 -------
if st.button("初回回答を取得"):
    if not question.strip():
        st.warning("質問を入力してください。")
    else:
        # 3名の名前を割り当て
        st.session_state["names"] = create_random_names()
        st.write("今回の登場人物:", ", ".join(st.session_state["names"]))

        # 各人の回答を短く取得
        answers_dict = {}
        for name in st.session_state["names"]:
            prompt = (
                f"{name}が以下の質問に短く(50文字程度)回答してください。\n"
                f"質問: {question}\n"
                "雑談よりもユーザーの悩み・疑問に答えてください。"
            )
            raw_answer = call_gemini_api(prompt)
            cleaned = remove_json_artifacts(raw_answer)
            short_ans = short_text(cleaned)
            if not short_ans.strip():
                short_ans = "（回答なし）"
            answers_dict[name] = short_ans
        
        st.session_state["initial_answers"] = answers_dict
        st.write("### 初回回答")
        for nm, ans in answers_dict.items():
            st.markdown(f"**{nm}**: {ans}")

        # 会話履歴を初期化
        st.session_state["discussion"] = ""

# ------- ボタン2: 会話を進める -------
if st.button("会話を進める"):
    if not st.session_state["initial_answers"]:
        st.warning("先に『初回回答を取得』してください。")
    else:
        # プロンプト作成
        discussion_prompt = (
            "これまでの会話:\n"
            f"{st.session_state['discussion']}\n\n"
            f"ユーザーの質問: {question}\n\n"
            "初回回答:\n"
        )
        for nm, ans in st.session_state["initial_answers"].items():
            discussion_prompt += f"{nm}: {ans}\n"

        discussion_prompt += (
            "\n上記を踏まえ、3人がさらに話し合いを進めてください。"
            "『名前: 発言』という形式で短い日本語文を出力し、JSONは不要です。"
        )

        res = call_gemini_api(discussion_prompt)
        cleaned = remove_json_artifacts(res)
        if not cleaned.strip():
            cleaned = "（会話なし）"

        # 履歴を追記
        st.session_state["discussion"] += "\n" + cleaned

        st.write("### 会話の内容")
        lines = st.session_state["discussion"].split("\n")
        for line in lines:
            line = line.strip()
            if line:
                display_text_in_box(line)

# ------- 追加発言用 -------
user_follow = st.text_input("さらに話したいことを入力")

if st.button("追加で会話を継続"):
    if not st.session_state["discussion"]:
        st.warning("まずは会話を進めてください。")
    else:
        cont_prompt = (
            f"これまでの会話:\n{st.session_state['discussion']}\n\n"
            f"ユーザーからの追加発言: {user_follow}\n"
            "この情報を踏まえ、3人がさらに会話を続けてください。"
            "名前: 発言 の形式で短い日本語文を出力し、JSON等は不要です。"
        )

        more_res = call_gemini_api(cont_prompt)
        cleaned_more = remove_json_artifacts(more_res)
        if not cleaned_more.strip():
            cleaned_more = "（会話なし）"

        st.session_state["discussion"] += "\n" + cleaned_more

        st.write("### 更新された会話")
        lines = st.session_state["discussion"].split("\n")
        for line in lines:
            line = line.strip()
            if line:
                display_text_in_box(line)

# --- テスト用ボタン ---
if st.button("テストプロンプト"):
    test_prompt = "こんにちは、今日はいい天気ですね？"
    test_res = call_gemini_api(test_prompt)
    st.write("### テスト結果")
    st.write(test_res)
