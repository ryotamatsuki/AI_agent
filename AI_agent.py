import streamlit as st
import requests
import re

API_KEY = "AIzaSyBTNVkzjKD3sUNVUMlp_tcXWQMO-FpfrSo"  # gemini-1.5-flash 用 API キー

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
    score = analyze_question(question)
    persona_params = {}
    if score > 0:
        persona_params["ペルソナ1"] = {"style": "情熱的", "detail": "感情に寄り添う回答"}
        persona_params["ペルソナ2"] = {"style": "共感的", "detail": "心情を重視した解説"}
        persona_params["ペルソナ3"] = {"style": "柔軟", "detail": "状況に合わせた多面的な視点"}
    else:
        persona_params["ペルソナ1"] = {"style": "論理的", "detail": "具体的な解説を重視"}
        persona_params["ペルソナ2"] = {"style": "分析的", "detail": "データや事実を踏まえた説明"}
        persona_params["ペルソナ3"] = {"style": "客観的", "detail": "中立的な視点からの考察"}
    return persona_params

def call_gemini_api(prompt: str) -> str:
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
                return candidates[0].get("content", "回答が見つかりませんでした。")
            else:
                return "回答が見つかりませんでした。"
        else:
            return f"エラー: ステータスコード {response.status_code} -> {response.text}"
    except Exception as e:
        return f"エラー: レスポンス解析に失敗しました -> {str(e)}"

def truncate_text(text, limit=50) -> str:
    if not isinstance(text, str):
        text = ""
    t = text.strip().replace("\n", " ")
    return t if len(t) <= limit else t[:limit] + "…"

def generate_initial_answers(question: str, persona_params: dict) -> dict:
    answers = {}
    for persona, params in persona_params.items():
        prompt = (
            f"【{params['style']}な視点】\n"
            f"以下の質問に答えてください。\n"
            f"質問: {question}\n"
            f"詳細: {params['detail']}\n"
            "回答は50文字程度で、余計な推論を含めないように。"
        )
        raw_answer = call_gemini_api(prompt)
        short_answer = truncate_text(raw_answer, 50)
        answers[persona] = short_answer
    return answers

def simulate_persona_discussion(answers: dict) -> str:
    discussion_prompt = "次の各ペルソナの初回回答をもとに、友達同士がゆっくりと話している自然な会話を作ってください。\n"
    for persona, ans in answers.items():
        discussion_prompt += f"{persona}の初回回答: {ans}\n"
    discussion_prompt += (
        "\n出力形式：\n"
        "ペルソナ1: 発言内容（50文字程度）\n"
        "ペルソナ2: 発言内容（50文字程度）\n"
        "ペルソナ3: 発言内容（50文字程度）\n"
        "各行は一つの発言で、余計な記述はなくシンプルにしてください。"
    )
    return call_gemini_api(discussion_prompt)

def generate_followup_question(discussion: str) -> str:
    if "？" in discussion:
        return discussion.split("？")[0] + "？"
    else:
        return "この件について、さらに詳しく教えていただけますか？"

def display_discussion_in_boxes(discussion: str):
    # discussion が文字列であることを保証（None なら空文字）
    if not isinstance(discussion, str):
        discussion = "" if discussion is None else str(discussion)

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

# ===== Streamlit UI =====
st.title("ぼくのともだち")

question = st.text_area("最初の質問を入力してください", placeholder="ここに質問を入力", height=150)

if st.button("送信"):
    if question:
        persona_params = adjust_parameters(question)
        
        st.write("### 各ペルソナからの初回回答")
        initial_answers = generate_initial_answers(question, persona_params)
        for persona, answer in initial_answers.items():
            st.markdown(f"**{persona}**: {answer}")

        st.write("### ペルソナ間のディスカッション")
        discussion = simulate_persona_discussion(initial_answers)
        display_discussion_in_boxes(discussion)

        st.write("### フォローアップ質問")
        followup_question = generate_followup_question(discussion)
        st.markdown(f"**システムからの質問:** {followup_question}")

        additional_input = st.text_input("上記のフォローアップ質問に対するあなたの回答を入力してください")
        if additional_input:
            st.write("### 追加回答を反映した会話の更新")
            update_prompt = (
                f"ユーザーからの追加回答: {additional_input}\n"
                f"先ほどのディスカッション: {discussion}\n"
                "この情報を踏まえ、今後の会話の方向性について意見を述べてください。"
            )
            updated_discussion = call_gemini_api(update_prompt)
            display_discussion_in_boxes(updated_discussion)
    else:
        st.warning("質問を入力してください")
