import streamlit as st
import requests
import re
import random

# ========================
#    定数／設定
# ========================
API_KEY = "AIzaSyCyHFSCTYR9T0a5zPn9yg-49eevJXqKP9g"  # gemini-1.5-flash 用 API キー
MODEL_NAME = "gemini-1.5-flash"
# 3人の日本人の名前（固定）
NAMES = ["ゆかり", "しんや", "みのる"]

# ========================
#    関数定義
# ========================

def analyze_question(question: str) -> int:
    """
    質問内容に含まれるキーワードから、感情寄り（例:"困った", "悩み", "苦しい", "辛い"）と
    論理寄り（例:"理由", "原因", "仕組み", "方法"）を判定するためのスコアを算出する。
    感情的なキーワードが多ければ正の値、論理的なキーワードが多ければ負の値を返す。
    """
    score = 0
    keywords_emotional = ["困った", "悩み", "苦しい", "辛い"]
    keywords_logical = ["理由", "原因", "仕組み", "方法"]
    for word in keywords_emotional:
        if re.search(word, question):
            score += 1
    for word in keywords_logical:
        if re.search(word, question):
            score -= 1
    return score

def adjust_parameters(question: str) -> dict:
    """
    質問内容に応じて、各キャラクターのスタイルと詳細文を調整する。
    analyze_question のスコアに応じ、感情寄りか論理寄りかを判断する。
    """
    score = analyze_question(question)
    params = {}
    if score > 0:
        params["ゆかり"] = {"style": "情熱的", "detail": "感情に寄り添う回答"}
        params["しんや"] = {"style": "共感的", "detail": "心情を重視した解説"}
        params["みのる"] = {"style": "柔軟", "detail": "状況に合わせた多面的な視点"}
    else:
        params["ゆかり"] = {"style": "論理的", "detail": "具体的な解説を重視"}
        params["しんや"] = {"style": "分析的", "detail": "データや事実を踏まえた説明"}
        params["みのる"] = {"style": "客観的", "detail": "中立的な視点からの考察"}
    return params

def remove_json_artifacts(text: str) -> str:
    """
    モデルが返す不要なJSON形式（例: 'parts': [{'text': ...}], 'role': 'model'）を取り除く。
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return cleaned.strip()

def call_gemini_api(prompt: str) -> str:
    """
    gemini-1.5-flash モデルを呼び出し、指定されたプロンプトに基づく回答または会話文を取得する。
    失敗時も必ず文字列を返し、'content' が辞書の場合は 'value' キーの内容を取り出す。
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
        return f"エラー: リクエスト送信時に例外が発生しました -> {str(e)}"
    if response.status_code != 200:
        return f"エラー: ステータスコード {response.status_code} -> {response.text}"
    try:
        rjson = response.json()
        candidates = rjson.get("candidates", [])
        if not candidates:
            return "回答が見つかりませんでした。(candidatesが空)"
        candidate0 = candidates[0]
        content_val = candidate0.get("content", "")
        if isinstance(content_val, dict):
            content_str = content_val.get("value", "")
        else:
            content_str = str(content_val)
        content_str = content_str.strip()
        if not content_str:
            return "回答が見つかりませんでした。(contentが空)"
        return remove_json_artifacts(content_str)
    except Exception as e:
        return f"エラー: レスポンス解析に失敗しました -> {str(e)}"

def generate_discussion(question: str, persona_params: dict) -> str:
    """
    ユーザーの質問と各キャラクターの設定をもとに、3人が自然な会話をするプロンプトを生成し、その回答を取得する。
    出力形式は「ゆかり: 発言内容」「しんや: 発言内容」「みのる: 発言内容」とします。
    """
    prompt = f"【ユーザーの質問】\n{question}\n\n"
    for name, params in persona_params.items():
        prompt += f"{name}は【{params['style']}な視点】で、{params['detail']}。\n"
    prompt += (
        "\n上記情報を元に、3人が友達同士のように自然に会話してください。\n"
        "出力形式は以下の通りです。\n"
        "ゆかり: 発言内容\n"
        "しんや: 発言内容\n"
        "みのる: 発言内容\n"
        "余計なJSON形式は入れず、自然な日本語の会話のみを出力してください。"
    )
    return call_gemini_api(prompt)

def generate_summary(discussion: str) -> str:
    """
    生成された3人の会話全体を元に、質問に対するまとめ回答を生成するプロンプトを作成し、結果を取得する。
    """
    prompt = (
        "以下は3人の会話内容です。\n"
        f"{discussion}\n\n"
        "この会話を踏まえて、質問に対するまとめ回答を生成してください。\n"
        "自然な日本語文で出力し、余計なJSON形式は不要です。"
    )
    return call_gemini_api(prompt)

def display_line_style(text: str):
    """
    生成された会話の各行を改行で分割し、LINE風の吹き出し形式で表示する。
    """
    lines = text.split("\n")
    color_map = {
        "ゆかり": "#DCF8C6",
        "しんや": "#E0F7FA",
        "みのる": "#FCE4EC"
    }
    for line in lines:
        line = line.strip()
        if not line:
            continue
        matched = re.match(r"^(.*?):\s*(.*)$", line)
        if matched:
            name = matched.group(1)
            message = matched.group(2)
        else:
            name = ""
            message = line
        bg_color = color_map.get(name, "#F5F5F5")
        bubble_html = f"""
        <div style="
            background-color: {bg_color};
            border:1px solid #ddd;
            border-radius:10px;
            padding:8px;
            margin:5px 0;
            width: fit-content;
        ">
            <strong>{name}</strong><br>
            {message}
        </div>
        """
        st.markdown(bubble_html, unsafe_allow_html=True)

# ========================
#    Streamlit アプリ
# ========================
st.title("ぼくのともだち - 自然な会話")

# ユーザーの質問入力エリア
question = st.text_area("質問を入力してください", placeholder="例: 官民共創施設の名前を考えてください。", height=150)

# セッション状態の初期化
if "discussion" not in st.session_state:
    st.session_state["discussion"] = ""
if "summary" not in st.session_state:
    st.session_state["summary"] = ""

# 3人のキャラクターの設定は adjust_parameters により決定
if st.button("会話を開始"):
    if question.strip():
        persona_params = adjust_parameters(question)
        discussion = generate_discussion(question, persona_params)
        st.session_state["discussion"] = discussion  # 会話履歴として保存
        st.write("### 3人の会話")
        display_line_style(discussion)
    else:
        st.warning("質問を入力してください。")

# まとめ回答生成ボタン
if st.button("会話をまとめる"):
    if st.session_state["discussion"]:
        summary = generate_summary(st.session_state["discussion"])
        st.session_state["summary"] = summary
        st.write("### まとめ回答")
        st.markdown(f"**まとめ:** {summary}")
    else:
        st.warning("まずは会話を開始してください。")
