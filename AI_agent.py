import streamlit as st
import requests
import re

# ========================
#    定数／設定
# ========================
API_KEY = "AIzaSyCyHFSCTYR9T0a5zPn9yg-49eevJXqKP9g"  # gemini-1.5-flash 用 API キー
MODEL_NAME = "gemini-1.5-flash"

# 質問を分析してキャラクター設定を変える用 (任意の関数)
def analyze_question(question: str) -> int:
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
    質問内容に応じて、3名の視点（style, detail）を自動調整する。
    """
    score = analyze_question(question)
    persona_params = {}
    if score > 0:
        # 感情寄りの回答を重視
        persona_params["ゆかり"] = {"style": "情熱的", "detail": "感情に寄り添う回答"}
        persona_params["しんや"] = {"style": "共感的", "detail": "心情を重視した解説"}
        persona_params["みのる"] = {"style": "柔軟", "detail": "状況に合わせた多面的な視点"}
    else:
        # 論理寄りの回答を重視
        persona_params["ゆかり"] = {"style": "論理的", "detail": "具体的な解説を重視"}
        persona_params["しんや"] = {"style": "分析的", "detail": "データや事実を踏まえた説明"}
        persona_params["みのる"] = {"style": "客観的", "detail": "中立的な視点からの考察"}
    return persona_params

def call_gemini_api(prompt: str) -> str:
    """
    gemini-1.5-flash モデルを呼び出し、指定されたプロンプトに基づく会話テキストを取得。
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
            return "回答が見つかりません。(candidatesが空)"

        content_val = candidates[0].get("content", "")
        # 辞書かもしれないので対処
        if isinstance(content_val, dict):
            content_str = content_val.get("value", "")
        else:
            content_str = str(content_val)
        content_str = content_str.strip()
        if not content_str:
            return "回答が見つかりません。(contentが空)"
        return remove_json_artifacts(content_str)
    except Exception as e:
        return f"エラー: レスポンス解析に失敗しました -> {str(e)}"

def remove_json_artifacts(text: str) -> str:
    """
    'parts': [{'text': ...}] や 'role': 'model' などを簡易的に除去
    """
    if not isinstance(text, str):
        text = str(text) if text else ""
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return cleaned.strip()

def generate_discussion(question: str, persona_params: dict) -> str:
    """
    いきなり3人が質問についてディスカッションするプロンプトを生成。
    """
    # 3名のスタイルを活かして、自由に会話してもらう
    prompt = "以下の情報を元に、3人がユーザーの質問について自然な会話をしてください。\n"
    prompt += f"ユーザーの質問: {question}\n\n"

    for name, params in persona_params.items():
        prompt += (
            f"{name}は【{params['style']}な視点】で、{params['detail']}。\n"
        )

    prompt += (
        "\n出力形式は以下:\n"
        "ゆかり: 会話内容\n"
        "しんや: 会話内容\n"
        "みのる: 会話内容\n"
        "余計なJSONや'parts'などは不要。自由に話し合ってください。"
    )
    return call_gemini_api(prompt)

def display_discussion_in_boxes(discussion: str):
    """
    会話結果を各行ごとに枠で囲んで表示する。
    """
    lines = discussion.split("\n")
    for line in lines:
        line = line.strip()
        if line:
            st.markdown(
                f"""<div style="border:1px solid #ddd; border-radius:5px; padding:8px; margin-bottom:8px;">
                {line}
                </div>""",
                unsafe_allow_html=True
            )

# ========================
#    Streamlit アプリ
# ========================
st.title("ぼくのともだち - いきなりディスカッション版")

# 質問を入力
question = st.text_area("3人が一緒に考える質問を入力してください。", placeholder="例: 官民共創施設の名前を考えてください。")

# 送信ボタン → ディスカッション直接生成
if st.button("ディスカッション"):
    if question.strip():
        # 質問を解析してパラメーター調整
        persona_params = adjust_parameters(question)

        # いきなり3人のディスカッション生成
        discussion = generate_discussion(question, persona_params)

        st.write("### 3人のディスカッション")
        display_discussion_in_boxes(discussion)
    else:
        st.warning("質問を入力してください。")
