import streamlit as st
import requests
import re

# ========================
#   設定エリア
# ========================
API_KEY = "AIzaSyCyHFSCTYR9T0a5zPn9yg-49eevJXqKP9g"  # gemini-1.5-flash 用 API キー

# モデル名
MODEL_NAME = "gemini-1.5-flash"

# 3人の日本人名
NAMES = ["ゆかり", "しんや", "みのる"]

# ========================
#   関数定義
# ========================

def remove_json_artifacts(text: str) -> str:
    """
    モデルが JSON 形式や 'parts': [{'text': ...}], 'role': 'model' などの情報を返した場合、
    正規表現で取り除く簡易処理。
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    # 'parts': [{'text': ... }] などを除去
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return cleaned.strip()

def call_gemini_api(prompt: str) -> str:
    """
    gemini-1.5-flash モデルを呼び出し、指定されたプロンプトに対する回答を取得する。
    content が dict の場合は 'value' キーなどを取り出す。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        return f"エラー: リクエスト送信失敗 -> {str(e)}"

    if response.status_code != 200:
        return f"エラー: {response.status_code} -> {response.text}"

    try:
        rjson = response.json()
        candidates = rjson.get("candidates", [])
        if not candidates:
            return "回答が見つかりません。(candidatesが空)"

        # 最初の候補を取得
        candidate0 = candidates[0]
        content_val = candidate0.get("content", "")
        # 'content' が辞書の場合への対処
        if isinstance(content_val, dict):
            # もし 'value' 等があれば取得
            content_str = content_val.get("value", "")
        else:
            content_str = str(content_val)

        content_str = content_str.strip()
        if not content_str:
            return "回答が見つかりません。(contentが空)"

        # 不要な JSON 表記を除去
        return remove_json_artifacts(content_str)

    except Exception as e:
        return f"エラー: JSON解析失敗 -> {str(e)}"

def generate_answer(name: str, question: str) -> str:
    """
    個別に、指定した名前が質問に回答する形で呼び出す。
    """
    prompt = (
        f"{name}が以下の質問について回答してください。\n"
        f"質問: {question}\n"
        "文字数制限はありません。余計な JSON は不要です。"
    )
    return call_gemini_api(prompt)

def generate_discussion(names_answers: dict) -> str:
    """
    3人の初回回答をもとに、自然な会話を生成する。
    """
    prompt = "以下は3人の初回回答です。\n"
    for nm, ans in names_answers.items():
        prompt += f"{nm}: {ans}\n"

    prompt += (
        "\nこの3人が友達同士のように、ユーザーの話題について話し合ってください。"
        "「名前: 発言」の形式で、LINE風の短いやりとりを日本語で出力してください。\n"
        "余計な JSON は入れず、自然な文章のみをお願いします。"
    )
    return call_gemini_api(prompt)

def display_line_style(discussion: str):
    """
    discussion を改行で分割し、「名前: 内容」をパースして LINE風吹き出しを表示する。
    """
    lines = discussion.split("\n")

    # 吹き出しカラーを名前ごとに分ける（好みで変更可）
    color_map = {
        "ゆかり": "#DCF8C6",  # 薄い緑
        "しんや": "#E0F7FA",  # 薄い水色
        "みのる": "#FCE4EC",  # 薄いピンク
    }

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 「名前: 内容」の形式をパース
        # 例： "ゆかり: なるほど、いいね。"
        matched = re.match(r"^(.*?)\s*:\s*(.*)$", line)
        if matched:
            name = matched.group(1)
            message = matched.group(2)
        else:
            # もし上記形式でないなら、そのまま表示
            name = ""
            message = line

        # 吹き出しの背景色を名前別に設定 (無かったらグレーに)
        bg_color = color_map.get(name, "#F5F5F5")

        # HTML で吹き出し風の見た目に
        bubble_html = f"""
        <div style="
            background-color: {bg_color}; 
            display: inline-block; 
            border-radius: 10px; 
            padding: 8px; 
            margin: 5px 0;
        ">
            <strong style="color: #000;">{name}</strong><br>
            {message}
        </div>
        """
        st.markdown(bubble_html, unsafe_allow_html=True)

# ========================
#   Streamlit アプリ
# ========================
st.title("ぼくのともだち - 日本人名＆LINE風表示")

if "names" not in st.session_state:
    # 3名を固定 (ユーザーが変更したい場合はここを動的にしてもOK)
    st.session_state["names"] = NAMES

if "initial_answers" not in st.session_state:
    st.session_state["initial_answers"] = {}

if "discussion" not in st.session_state:
    st.session_state["discussion"] = ""

# 1. 質問を入力
question = st.text_area("最初の質問を入力してください", placeholder="例: 官民共創施設の名前を考えてください。")

# 2. 初回回答取得ボタン
if st.button("初回回答を取得"):
    if not question.strip():
        st.warning("質問を入力してください。")
    else:
        # 3人それぞれの回答を取得
        answers_dict = {}
        for nm in st.session_state["names"]:
            ans = generate_answer(nm, question)
            answers_dict[nm] = ans
        
        st.session_state["initial_answers"] = answers_dict
        st.session_state["discussion"] = ""  # 会話履歴初期化

        st.write("### 初回回答")
        for nm, ans in answers_dict.items():
            # LINE風で表示
            st.markdown(f"**{nm}**: {ans}")

# 3. 会話を進めるボタン
if st.button("会話を進める"):
    if not st.session_state["initial_answers"]:
        st.warning("先に『初回回答を取得』を押してください。")
    else:
        # これまでの会話 + 新たなディスカッション
        new_discussion = generate_discussion(st.session_state["initial_answers"])
        # 連結して履歴に追加
        st.session_state["discussion"] += "\n" + new_discussion

        st.write("### 3人の会話 (LINE風)")
        display_line_style(st.session_state["discussion"])

# 4. ユーザー追加入力
user_follow = st.text_input("彼らの会話に追加で伝えたいこと")

if st.button("追加回答を踏まえて会話を継続"):
    if not st.session_state["discussion"]:
        st.warning("まずは『会話を進める』を押して、会話を開始してください。")
    else:
        # 追加発言を踏まえて再度モデルへ
        prompt_cont = (
            f"これまでの会話:\n{st.session_state['discussion']}\n\n"
            f"ユーザーからの追加発言: {user_follow}\n"
            "この情報を踏まえ、3人がさらに会話を続けます。\n"
            "名前: 内容 の形式で、LINEのように自然なやりとりをお願いします。"
        )
        cont_result = call_gemini_api(prompt_cont)
        st.session_state["discussion"] += "\n" + cont_result

        st.write("### 更新された会話")
        display_line_style(st.session_state["discussion"])
