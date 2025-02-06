import streamlit as st
import requests
import re

# ========================
#    定数／設定
# ========================
API_KEY = "AIzaSyCyHFSCTYR9T0a5zPn9yg-49eevJXqKP9g"  # gemini-1.5-flash 用 API キー

# ========================
#    関数定義
# ========================

def analyze_question(question: str) -> int:
    """
    質問内容を解析し、感情やキーワードに応じたスコアを返す。
    キーワード '困った' や '悩み' などが含まれていればスコアを高めにする。
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
    質問内容に応じて、各ペルソナのプロンプトに埋め込むスタイルと詳細文を自動調整する。
    """
    score = analyze_question(question)
    persona_params = {}

    if score > 0:
        # 感情寄りの回答を重視
        persona_params["ペルソナ1"] = {"style": "情熱的", "detail": "感情に寄り添う回答"}
        persona_params["ペルソナ2"] = {"style": "共感的", "detail": "心情を重視した解説"}
        persona_params["ペルソナ3"] = {"style": "柔軟", "detail": "状況に合わせた多面的な視点"}
    else:
        # 論理寄りの回答を重視
        persona_params["ペルソナ1"] = {"style": "論理的", "detail": "具体的な解説を重視"}
        persona_params["ペルソナ2"] = {"style": "分析的", "detail": "データや事実を踏まえた説明"}
        persona_params["ペルソナ3"] = {"style": "客観的", "detail": "中立的な視点からの考察"}

    return persona_params

def call_gemini_api(prompt: str) -> str:
    """
    gemini-1.5-flash モデルを呼び出し、指定されたプロンプトに基づく回答を取得する。
    エラー発生時も必ず文字列を返す（None にはならない）。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}

    # ネットワーク送信
    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        return f"エラー: リクエスト送信時に例外が発生しました -> {str(e)}"

    # レスポンス解析
    try:
        if response.status_code == 200:
            rjson = response.json()
            candidates = rjson.get("candidates", [])
            if candidates:
                # "content" がない場合はフォールバック
                return candidates[0].get("content", "回答が見つかりませんでした。")
            else:
                return "回答が見つかりませんでした。"
        else:
            return f"エラー: ステータスコード {response.status_code} -> {response.text}"
    except Exception as e:
        return f"エラー: レスポンス解析に失敗しました -> {str(e)}"

def generate_initial_answers(question: str, persona_params: dict) -> dict:
    """
    ユーザーの初回質問に対して、各ペルソナの回答を生成する。
    文字数制限はなくし、長い回答も許容する。
    """
    answers = {}
    for persona, params in persona_params.items():
        prompt = (
            f"【{params['style']}な視点】\n"
            f"以下の質問に答えてください。\n"
            f"質問: {question}\n"
            f"詳細: {params['detail']}\n"
            "回答に文字数制限はありません。余計な推論は控えめで、質問に集中してください。"
        )
        raw_answer = call_gemini_api(prompt)
        answers[persona] = raw_answer  # そのまま全体を格納
    return answers

def simulate_persona_discussion(answers: dict) -> str:
    """
    各ペルソナの初回回答をもとに、友達同士がゆっくりと話している自然な会話を生成する。
    文字数制限を撤廃し、自由に会話させる。
    """
    discussion_prompt = (
        "以下の各ペルソナの初回回答を踏まえて、自然な会話を作ってください。\n"
    )
    for persona, ans in answers.items():
        discussion_prompt += f"{persona}の初回回答: {ans}\n"
    discussion_prompt += (
        "\n出力形式：\n"
        "ペルソナ1: 発言内容（自由）\n"
        "ペルソナ2: 発言内容（自由）\n"
        "ペルソナ3: 発言内容（自由）\n"
        "※各行は一度の発言で、JSONや余計な記述は不要とします。"
    )
    return call_gemini_api(discussion_prompt)

def generate_followup_question(discussion: str) -> str:
    """
    ペルソナ間のディスカッションから、ユーザーへのフォローアップ質問を抽出または生成する。
    """
    if "？" in discussion:
        return discussion.split("？")[0] + "？"
    else:
        return "この件について、さらに詳しく教えていただけますか？"

def display_discussion_in_boxes(discussion: str):
    """
    生成された会話の各発言を改行で分割し、各発言を枠で囲んで表示する。
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
st.title("ぼくのともだち (50文字制限解除版)")

# ユーザーからの初回質問入力
question = st.text_area("最初の質問を入力してください", placeholder="ここに質問を入力", height=150)

if st.button("送信"):
    if question:
        # 自動パラメーター調整
        persona_params = adjust_parameters(question)

        # 各ペルソナの初回回答生成（制限なし）
        st.write("### 各ペルソナからの初回回答")
        initial_answers = generate_initial_answers(question, persona_params)
        for persona, answer in initial_answers.items():
            st.markdown(f"**{persona}**: {answer}")

        # ペルソナ間のディスカッション（文字数制限なし）
        st.write("### ペルソナ間のディスカッション")
        discussion = simulate_persona_discussion(initial_answers)
        display_discussion_in_boxes(discussion)

        # フォローアップ質問生成
        st.write("### フォローアップ質問")
        followup_question = generate_followup_question(discussion)
        st.markdown(f"**システムからの質問:** {followup_question}")

        # ユーザーの追加回答を入力
        additional_input = st.text_input("上記のフォローアップ質問に対するあなたの回答を入力してください")
        if additional_input:
            st.write("### 追加回答を反映した会話の更新")
            update_prompt = (
                f"ユーザーからの追加回答: {additional_input}\n"
                f"先ほどのディスカッション: {discussion}\n"
                "この情報を踏まえ、今後の会話の方向性について意見を述べてください。\n"
                "制限はなく自由に回答してください。"
            )
            updated_discussion = call_gemini_api(update_prompt)
            display_discussion_in_boxes(updated_discussion)
    else:
        st.warning("質問を入力してください")
