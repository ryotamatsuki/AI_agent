import streamlit as st
import requests
import re
import random

API_KEY = "AIzaSyDfyltY3n2p8Ia4qrWJKk8gU8ZBTxsGKWI"
MODEL_NAME = "gemini-2.0-flash-001"

NAMES = ["ゆかり", "しんや", "みのる", "たかし", "けんじ", "あやこ", "りな"]

def call_gemini_api(prompt: str) -> str:
    """
    gemini-2.0-flash-001 モデルで回答を取得。
    'content' が辞書の場合は 'value' を取り出し、文字列化。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}

    print("[DEBUG] Prompt:\n", prompt)
    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        return f"エラー: ネットワーク接続失敗 -> {str(e)}"

    print("[DEBUG] Status code:", response.status_code)
    print("[DEBUG] Response text:", response.text)

    if response.status_code != 200:
        return f"エラー: ステータス {response.status_code} -> {response.text}"

    try:
        rjson = response.json()
        candidates = rjson.get("candidates", [])
        if not candidates:
            return "回答が見つかりません。(candidatesが空)"

        candidate0 = candidates[0]
        content_val = candidate0.get("content", "")
        if isinstance(content_val, dict):
            content_str = content_val.get("value", "")
        else:
            content_str = str(content_val)
        content_str = content_str.strip()
        if not content_str:
            return "回答が見つかりません。(contentが空)"
        return content_str
    except Exception as e:
        return f"エラー: JSON解析失敗 -> {str(e)}"

def remove_json_artifacts(text: str) -> str:
    if not isinstance(text, str):
        text = str(text) if text else ""
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    return re.sub(pattern, "", text, flags=re.DOTALL)

def create_random_names():
    return random.sample(NAMES, 3)

def display_in_box(text: str):
    st.markdown(
        f"""<div style="border:1px solid #ddd; border-radius:5px; padding:8px; margin-bottom:8px;">
        {text}
        </div>""",
        unsafe_allow_html=True
    )

st.title("ぼくのともだち - Gemini 2.0 Flash (制限なし)")

if "names" not in st.session_state:
    st.session_state["names"] = []
if "answers" not in st.session_state:
    st.session_state["answers"] = {}
if "history" not in st.session_state:
    st.session_state["history"] = ""

question = st.text_area("最初の質問を入力してください", placeholder="ここに質問を入力")

# 初回回答
if st.button("初回回答を取得"):
    if not question.strip():
        st.warning("質問を入力してください。")
    else:
        st.session_state["names"] = create_random_names()
        st.write("今回の登場人物:", ", ".join(st.session_state["names"]))

        answers = {}
        for name in st.session_state["names"]:
            prompt = (
                f"{name}が以下の質問に回答してください:\n"
                f"質問: {question}\n"
                "長さ制限はありません。ユーザーの疑問にしっかり答えてください。"
            )
            raw = call_gemini_api(prompt)
            cleaned = remove_json_artifacts(raw).strip()
            if not cleaned:
                cleaned = "（回答なし）"
            answers[name] = cleaned

        st.session_state["answers"] = answers
        st.write("### 初回回答")
        for nm, ans in answers.items():
            st.markdown(f"**{nm}**: {ans}")
        
        st.session_state["history"] = ""

# 会話を進める
if st.button("会話を進める"):
    if not st.session_state["answers"]:
        st.warning("まず初回回答を取得してください。")
    else:
        discussion_prompt = (
            "これまでの会話:\n"
            f"{st.session_state['history']}\n\n"
            f"ユーザーの質問: {question}\n\n"
            "初回回答:\n"
        )
        for nm, ans in st.session_state["answers"].items():
            discussion_prompt += f"{nm}: {ans}\n"

        discussion_prompt += (
            "\n上記を踏まえ、3人がさらに話し合ってください。\n"
            "名前: 発言\n"
            "という形式で日本語で出力してください。JSONは不要です。"
        )

        res = call_gemini_api(discussion_prompt)
        cleaned = remove_json_artifacts(res).strip()
        if not cleaned:
            cleaned = "（会話なし）"

        st.session_state["history"] += "\n" + cleaned
        st.write("### 会話の内容")
        lines = st.session_state["history"].split("\n")
        for line in lines:
            line = line.strip()
            if line:
                display_in_box(line)

# 追加のやりとり
user_follow = st.text_input("さらに話したいことがあれば入力")

if st.button("追加で会話を継続"):
    if not st.session_state["history"]:
        st.warning("まず会話を進めてください。")
    else:
        follow_prompt = (
            f"今までの会話:\n{st.session_state['history']}\n\n"
            f"ユーザーの追加発言: {user_follow}\n"
            "これを踏まえ、3人がさらに話し合いを続けてください。\n"
            "名前: 発言 の形式で回答し、JSON表記は不要です。"
        )
        follow_res = call_gemini_api(follow_prompt)
        cleaned_f = remove_json_artifacts(follow_res).strip()
        if not cleaned_f:
            cleaned_f = "（会話なし）"

        st.session_state["history"] += "\n" + cleaned_f
        st.write("### 更新された会話")
        lines = st.session_state["history"].split("\n")
        for line in lines:
            line = line.strip()
            if line:
                display_in_box(line)

# テスト用
st.write("---")
if st.button("テストプロンプト"):
    test_prompt = "こんにちは。今日は何をしましたか？"
    result = call_gemini_api(test_prompt)
    st.write("### テスト結果")
    st.write(result)
