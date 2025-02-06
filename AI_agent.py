import streamlit as st
import requests
import re
import random

API_KEY = "AIzaSyDfyltY3n2p8Ia4qrWJKk8gU8ZBTxsGKWI"  # gemini-1.5-flash 用の有効な API キー

NAMES = ["たかし", "ゆかり", "りな", "けんじ", "あやこ", "みのる", "しんや", "さとみ"]

def call_gemini_api(prompt: str) -> str:
    """
    gemini-1.5-flash モデルを呼び出し、指定されたプロンプトに基づく回答を取得する。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            rjson = response.json()
            candidates = rjson.get("candidates", [])
            if candidates:
                return candidates[0].get("content", "回答が見つかりませんでした。")
            else:
                return "回答が見つかりませんでした。"
        else:
            return f"エラー: {response.status_code} -> {response.text}"
    except Exception as e:
        return f"エラー: {str(e)}"

def remove_json_artifacts(text: str) -> str:
    """
    モデルが JSON 形式を返した場合、その部分を削除する簡易処理。
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    # 単純な例: "'parts': ... , 'role': 'model'" みたいなのを削除
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return cleaned

def short_text(text: str, limit=50) -> str:
    """
    50文字程度に切り詰める（初回回答を短くまとめたい場合）。
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    t = text.strip().replace("\n", " ")
    return t if len(t) <= limit else t[:limit] + "…"

def generate_individual_answer(question: str, style: str, detail: str, limit=50) -> str:
    """
    1名分の回答を生成。style, detailを含む説明をプロンプトに埋め込み、短くまとめる。
    """
    prompt = (
        f"【{style}な視点】\n"
        f"以下の質問に答えてください。\n"
        f"質問: {question}\n"
        f"詳細: {detail}\n"
        "回答は50文字程度で、余計な推論を含めず、JSON表記は不要です。"
    )
    raw_answer = call_gemini_api(prompt)
    cleaned = remove_json_artifacts(raw_answer)
    return short_text(cleaned, limit)

def create_names_for_personas():
    """
    日本人名をランダムに3つ選んで返す。
    重複回避したい場合は random.sample を使う。
    """
    return random.sample(NAMES, 3)

def generate_parameters(question: str) -> list:
    """
    質問内容に応じて「情熱的」「論理的」などを割り当てる例。
    ここではシンプルに3人分を固定かランダムで割り当てる。
    """
    # シンプルに3種類のスタイルを定義
    # 実際には analyze_question(question) などで感情度合いを判断してもよい
    styles = [
        {"style": "情熱的", "detail": "感情に寄り添う回答"},
        {"style": "論理的", "detail": "具体的な解説を重視"},
        {"style": "柔軟", "detail": "状況に合わせた多面的な視点"}
    ]
    return styles

def display_text_in_box(text: str):
    """
    1つの文章を枠で囲んで表示。
    """
    st.markdown(
        f"""<div style="border:1px solid #ddd; border-radius:5px; padding:8px; margin-bottom:8px;">
        {text}
        </div>""",
        unsafe_allow_html=True
    )

def simulate_discussion(user_question: str, answers: dict, existing_discussion: str = "") -> str:
    """
    3人の回答と、過去の会話(existing_discussion)を踏まえ、さらに会話を続ける。
    user_question はユーザーの質問を再度示す。

    existing_discussion: これまでの会話の内容
    """
    prompt = (
        f"ユーザーの質問: {user_question}\n"
        "以下は3人が話し合った会話の内容です。\n"
        f"{existing_discussion}\n\n"
        "また、それぞれの最初の回答は以下の通りです:\n"
    )
    for name, ans in answers.items():
        prompt += f"{name}の初回回答: {ans}\n"
    prompt += (
        "\n続きの会話を日本語で進めてください。雑談ではなく、ユーザーの質問に焦点を当てつつ、"
        "アイデアや追加質問を出してください。"
        "出力形式は以下:\n"
        "名前: 発言（短く）\n"
        "名前: 発言\n"
        "※JSONや'parts'などは不要です。"
    )
    raw_result = call_gemini_api(prompt)
    cleaned = remove_json_artifacts(raw_result)
    return cleaned

# Streamlit アプリ開始
st.title("ぼくのともだち - 日本人の名前で会話する")

# Session State 初期化
if "names" not in st.session_state:
    st.session_state["names"] = []
if "initial_answers" not in st.session_state:
    st.session_state["initial_answers"] = {}
if "discussion_history" not in st.session_state:
    st.session_state["discussion_history"] = ""

question = st.text_area(
    "最初の質問を入力してください", 
    placeholder="ここに質問を入力"
)

if st.button("初回回答をもらう"):
    if question.strip():
        # 1) 日本人の名前を3つ選ぶ
        st.session_state["names"] = create_names_for_personas()  # 例: ["たかし", "ゆかり", "りな"]
        st.write("今回の登場人物:")
        st.write(", ".join(st.session_state["names"]))

        # 2) それぞれのパラメータを用意
        param_list = generate_parameters(question)  # [{"style":..., "detail":...}, ...]
        # len(param_list) = 3 を想定

        # 3) 3人分の初回回答を生成
        answers_dict = {}
        for i, name in enumerate(st.session_state["names"]):
            style_data = param_list[i] if i < len(param_list) else {"style":"標準","detail":"特になし"}
            ans = generate_individual_answer(
                question, style_data["style"], style_data["detail"], limit=50
            )
            answers_dict[name] = ans
        st.session_state["initial_answers"] = answers_dict

        st.write("### 初回回答")
        for name, ans in answers_dict.items():
            st.markdown(f"**{name}**: {ans}")

        st.session_state["discussion_history"] = ""  # 初期化
    else:
        st.warning("質問を入力してください")

if st.button("会話を進める"):
    if not st.session_state["names"]:
        st.warning("まずは初回回答を得てください。")
    else:
        # ペルソナ(名前)の回答が既にあるか
        if not st.session_state["initial_answers"]:
            st.warning("初回回答がありません。")
        else:
            # 会話のシミュレーション
            new_discussion = simulate_discussion(question, st.session_state["initial_answers"], st.session_state["discussion_history"])
            # 新しく得られた会話を履歴に追加
            st.session_state["discussion_history"] += "\n" + new_discussion

            st.write("### ペルソナ間のディスカッション(日本人名)")
            lines = st.session_state["discussion_history"].split("\n")
            for line in lines:
                line = line.strip()
                if line:
                    display_text_in_box(line)

# フォローアップのやりとり
user_follow = st.text_input("ペルソナたちとの会話に対して追加で話したいことを入力")

if st.button("追加回答を踏まえて会話を継続"):
    if not st.session_state["discussion_history"]:
        st.warning("まずは会話を進めてください。")
    else:
        # ユーザーのフォローアップを含めてさらに会話
        next_prompt = (
            f"前回までの会話:\n{st.session_state['discussion_history']}\n\n"
            f"ユーザーからの追加発言: {user_follow}\n"
            "これを踏まえ、さらに3人が会話を進めてください。\n"
            "名前: 発言 という形式で短い文を日本語で回答し、JSONやpartsなどは不要です。"
        )
        result = call_gemini_api(next_prompt)
        cleaned_result = remove_json_artifacts(result)
        st.session_state["discussion_history"] += "\n" + cleaned_result

        st.write("### 更新された会話")
        lines = st.session_state["discussion_history"].split("\n")
        for line in lines:
            line = line.strip()
            if line:
                display_text_in_box(line)
