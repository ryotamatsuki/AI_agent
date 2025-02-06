import streamlit as st
import requests
import re

API_KEY = "AIzaSyDfyltY3n2p8Ia4qrWJKk8gU8ZBTxsGKWI"  # gemini-1.5-flash 用の有効な API キーを指定

def analyze_question(question: str) -> int:
    """
    質問内容に含まれるキーワードから、
    感情寄り or 論理寄りをざっくり判定するためのスコアを算出。
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
    質問内容に応じて、各ペルソナの「style」と「detail」を自動設定する。
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
    通信・解析エラー時も必ず文字列を返す（None にはしない）。
    ※ デバッグログを追加し、レスポンスをコンソールに出力。
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
        print("[DEBUG] Network error:", str(e))
        return f"エラー: リクエスト送信時に例外が発生しました -> {str(e)}"

    print("[DEBUG] Status code:", response.status_code)
    print("[DEBUG] Response text:", response.text)

    # レスポンス解析
    try:
        if response.status_code == 200:
            rjson = response.json()
            candidates = rjson.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", "回答が見つかりませんでした。")
                print("[DEBUG] Parsed content:", content)
                return content
            else:
                return "回答が見つかりませんでした。"
        else:
            return f"エラー: ステータスコード {response.status_code} -> {response.text}"
    except Exception as e:
        print("[DEBUG] JSON decode error:", str(e))
        return f"エラー: レスポンス解析に失敗しました -> {str(e)}"

def truncate_text(text, limit=50) -> str:
    """
    テキストを指定文字数（limit）に収める。text が文字列でない or None の場合は空文字列扱い。
    """
    if not isinstance(text, str) or not text:
        return "（回答なし）"  # 万一空の場合は「（回答なし）」と表示
    t = text.strip().replace("\n", " ")
    return t if len(t) <= limit else t[:limit] + "…"

def remove_json_artifacts(text: str) -> str:
    """
    モデルが JSON 形式 (例: {'parts': [{'text': ...}], 'role': 'model'}) を
    返してきた場合、それらを正規表現で取り除く。
    """
    # 'parts': [{'text': '...'}], 'role': 'model' などを雑に除去
    # 単純な例として "'parts': [{'text': ...}]" を取り除く
    # 必要に応じて細かいカスタマイズが可能
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return cleaned

def generate_initial_answers(question: str, persona_params: dict) -> dict:
    """
    ユーザーの初回質問に対して、各ペルソナが 50文字程度の短い回答を返す。
    """
    answers = {}
    for persona, params in persona_params.items():
        prompt = (
            f"【{params['style']}な視点】\n"
            f"以下の質問に答えてください。\n"
            f"質問: {question}\n"
            f"詳細: {params['detail']}\n"
            "回答は50文字程度で、余計な推論を含めず、JSON形式も返さないでください。"
        )
        raw_answer = call_gemini_api(prompt)
        # もしモデルが JSON ぽい文字列を返した場合に取り除く
        cleaned_answer = remove_json_artifacts(raw_answer)
        short_answer = truncate_text(cleaned_answer, 50)
        answers[persona] = short_answer
        print(f"[DEBUG] {persona} raw_answer:", raw_answer)
        print(f"[DEBUG] {persona} cleaned_answer:", cleaned_answer)
        print(f"[DEBUG] {persona} short_answer:", short_answer)
    return answers

def simulate_persona_discussion(answers: dict, user_question: str) -> str:
    """
    各ペルソナの初回回答とユーザーの質問を踏まえ、
    「雑談になりすぎず、ユーザーの疑問に焦点を当てる」会話を生成する。
    """
    discussion_prompt = (
        "ユーザーの質問があります:\n"
        f"【質問】{user_question}\n\n"
        "以下に各ペルソナの初回回答を示します。JSON等ではなく、会話形式をお願いします。\n"
    )
    for persona, ans in answers.items():
        discussion_prompt += f"{persona}の初回回答: {ans}\n"

    discussion_prompt += (
        "\n上記の質問と初回回答を基に、3人がユーザーの疑問について話し合ってください。"
        "雑談ではなく、ユーザーの話題に寄り添い、具体的なアイデアや追加質問を提示してください。\n"
        "出力形式:\n"
        "ペルソナ1: （短い発言。JSONやpartsなど不要）\n"
        "ペルソナ2: （短い発言）\n"
        "ペルソナ3: （短い発言）\n"
        "※50文字程度で。"
    )

    print("[DEBUG] discussion_prompt:", discussion_prompt)
    discussion = call_gemini_api(discussion_prompt)
    # JSONぽい表記があれば削除
    cleaned = remove_json_artifacts(discussion)
    print("[DEBUG] discussion result:", cleaned)
    return cleaned

def generate_followup_question(discussion: str) -> str:
    """
    ペルソナ間のディスカッションからユーザーへのフォローアップ質問を抽出。
    """
    if "？" in discussion:
        return discussion.split("？")[0] + "？"
    else:
        return "この件について、さらに詳しく教えていただけますか？"

def display_discussion_in_boxes(discussion: str):
    """
    会話結果を各行ごとに枠で囲み、見やすく表示する。
    """
    if not isinstance(discussion, str):
        discussion = str(discussion) if discussion is not None else ""
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

# =============== Streamlit アプリケーション ===============
st.title("ぼくのともだち")

question = st.text_area(
    "最初の質問を入力してください", 
    placeholder="ここに質問を入力", 
    height=150
)

if st.button("送信"):
    if question.strip():
        # 1. ペルソナのパラメータ調整
        persona_params = adjust_parameters(question)
        print("[DEBUG] persona_params:", persona_params)

        # 2. 各ペルソナの初回回答生成
        st.write("### 各ペルソナからの初回回答")
        initial_answers = generate_initial_answers(question, persona_params)
        for persona, ans in initial_answers.items():
            st.markdown(f"**{persona}**: {ans}")

        # 3. ペルソナ間のディスカッション
        st.write("### ペルソナ間のディスカッション")
        discussion = simulate_persona_discussion(initial_answers, question)
        display_discussion_in_boxes(discussion)

        # 4. フォローアップ質問生成
        st.write("### フォローアップ質問")
        followup_question = generate_followup_question(discussion)
        st.markdown(f"**システムからの質問:** {followup_question}")

        # 5. ユーザーの追加回答
        additional_input = st.text_input("上記のフォローアップ質問に対するあなたの回答を入力してください")
        if additional_input.strip():
            st.write("### 追加回答を反映した会話の更新")
            update_prompt = (
                f"ユーザーからの追加回答: {additional_input}\n"
                f"先ほどのディスカッション: {discussion}\n"
                "この情報を踏まえ、今後の会話の方向性について意見を述べてください。\n"
                "※出力は会話形式で、JSON表記や'parts'などは不要です。"
            )
            updated_discussion = call_gemini_api(update_prompt)
            cleaned_update = remove_json_artifacts(updated_discussion)
            display_discussion_in_boxes(cleaned_update)
    else:
        st.warning("質問を入力してください")
