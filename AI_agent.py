import streamlit as st
import requests
import re
import random

# ==========================
#   設定エリア
# ==========================
API_KEY = "AIzaSyDfyltY3n2p8Ia4qrWJKk8gU8ZBTxsGKWI"  # gemini-2.0-flash-001 用の有効な API キー
MODEL_NAME = "gemini-2.0-flash-001"  # 新しいモデル

# 会話に登場する日本人名の候補
NAMES = ["ゆかり", "しんや", "みのる", "たかし", "けんじ", "あやこ", "りな"]

# ==========================
#   関数定義
# ==========================

def call_gemini_api(prompt: str) -> str:
    """
    Google Generative Language API (gemini-2.0-flash-001) にプロンプトを送信。
    失敗や空回答でも必ず文字列を返す。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}

    print("[DEBUG] Prompt sent to model:\n", prompt)

    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print("[DEBUG] Network error:", str(e))
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
        content = candidates[0].get("content", "").strip()
        if not content:
            return "回答が見つかりませんでした。(contentが空)"
        return content
    except Exception as e:
        print("[DEBUG] JSON parse error:", str(e))
        return f"エラー: JSON解析失敗 -> {str(e)}"

def remove_json_artifacts(text: str) -> str:
    """
    モデルが JSON 形式や 'parts': [{'text': ...}] を返した場合に取り除く。
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return cleaned

def short_text(text: str, limit=50) -> str:
    """
    50文字程度に切り詰める。
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    t = text.strip().replace("\n", " ")
    return t if len(t) <= limit else t[:limit] + "…"

def display_text_in_box(text: str):
    """
    会話や回答を枠で囲んで表示。HTMLでシンプルなボックスにする。
    """
    st.markdown(
        f"""<div style="border:1px solid #ddd; border-radius:5px; padding:8px; margin-bottom:8px;">
        {text}
        </div>""",
        unsafe_allow_html=True
    )

def create_random_names() -> list:
    """
    日本人名リストからランダムに3名を選んで返す。
    """
    return random.sample(NAMES, 3)

# =============== Streamlit アプリ ===============
st.title("ぼくのともだち（gemini-2.0-flash-001）")

# セッションステート初期化
if "names" not in st.session_state:
    st.session_state["names"] = []
if "initial_answers" not in st.session_state:
    st.session_state["initial_answers"] = {}
if "discussion" not in st.session_state:
    st.session_state["discussion"] = ""

# ユーザーが最初に入力する質問
question = st.text_area("最初の質問を入力してください", placeholder="ここに質問を入力")

# ------- ボタン1: 初回回答を取得 -------
if st.button("初回回答を取得"):
    if not question.strip():
        st.warning("質問を入力してください。")
    else:
        # 3人の日本人名をランダムに選ぶ
        st.session_state["names"] = create_random_names()
        st.write("今回の登場人物:", ", ".join(st.session_state["names"]))

        # 各人の回答を生成
        answers_dict = {}
        for name in st.session_state["names"]:
            # シンプルなプロンプトで回答を得る
            prompt = (
                f"{name}が以下の質問に短め（50文字程度）で回答してください。\n"
                f"質問: {question}\n"
                "雑談ではなく、ユーザーの悩みに答えるようにしてください。"
            )
            raw_answer = call_gemini_api(prompt)
            cleaned = remove_json_artifacts(raw_answer)
            short_ans = short_text(cleaned)
            if not short_ans.strip():
                short_ans = "（回答なし）"
            answers_dict[name] = short_ans
        
        st.session_state["initial_answers"] = answers_dict
        st.write("### 初回回答")
        for name, ans in answers_dict.items():
            st.markdown(f"**{name}**: {ans}")
        
        # 会話履歴を初期化
        st.session_state["discussion"] = ""

# ------- ボタン2: 会話を進める -------
if st.button("会話を進める"):
    if not st.session_state["initial_answers"]:
        st.warning("先に『初回回答を取得』してください。")
    else:
        # これまでの会話履歴 + 今回の質問 + 初回回答 をもとに会話を続行
        prompt_discussion = (
            "これまでの会話:\n"
            f"{st.session_state['discussion']}\n\n"
            f"ユーザーの質問: {question}\n\n"
            "登場人物の初回回答:\n"
        )
        for name, ans in st.session_state["initial_answers"].items():
            prompt_discussion += f"{name}: {ans}\n"
        
        prompt_discussion += (
            "\n上記を踏まえ、3人でさらに話し合ってください。"
            "名前: 一言 の形式で短く、日本語で返してください。"
            "JSONや'parts'などは不要です。"
        )

        result = call_gemini_api(prompt_discussion)
        cleaned_result = remove_json_artifacts(result)
        if not cleaned_result.strip():
            cleaned_result = "（会話なし）"

        # 履歴に追記
        st.session_state["discussion"] += "\n" + cleaned_result

        st.write("### 会話の内容")
        lines = st.session_state["discussion"].split("\n")
        for line in lines:
            line = line.strip()
            if line:
                display_text_in_box(line)

# ------- ユーザー追加入力 -------
user_follow = st.text_input("上記の会話に追加で伝えたいことがあれば入力してください")

if st.button("追加で会話を継続"):
    if not st.session_state["discussion"]:
        st.warning("まずは会話を進めてください。")
    else:
        prompt_follow = (
            "今までの会話:\n"
            f"{st.session_state['discussion']}\n\n"
            f"ユーザーが追加で伝えたい内容: {user_follow}\n"
            "この情報を踏まえ、再度3人で話を続けてください。"
            "名前: 発言 の形式で短い日本語文を出力し、JSONなどは不要です。"
        )

        follow_result = call_gemini_api(prompt_follow)
        cleaned_follow = remove_json_artifacts(follow_result)
        if not cleaned_follow.strip():
            cleaned_follow = "（会話なし）"

        st.session_state["discussion"] += "\n" + cleaned_follow

        st.write("### 更新された会話")
        lines = st.session_state["discussion"].split("\n")
        for line in lines:
            line = line.strip()
            if line:
                display_text_in_box(line)

# ------- テスト用 シンプルプロンプト -------
st.write("---")
if st.button("テストプロンプト実行"):
    test_prompt = "こんにちは！今日は調子はいかがですか？"
    test_res = call_gemini_api(test_prompt)
    st.write("### テスト結果")
    st.write(test_res)
