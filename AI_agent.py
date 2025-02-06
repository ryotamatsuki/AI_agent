import streamlit as st
import requests
import re

# Gemini API のエンドポイントと API キー（Google Cloud コンソールから発行したキー）
API_KEY = "YOUR_GEMINI_API_KEY"

def analyze_question(question):
    """
    質問内容を解析し、感情やキーワードに応じたスコアを返す関数。
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

def adjust_parameters(question):
    """
    質問の内容に応じて、各ペルソナのプロンプトに埋め込むスタイル・詳細文を自動調整する関数。
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

def call_gemini_api(prompt):
    """
    Google Generative Language API の Gemini モデルを呼び出し、
    指定されたプロンプトに基づいた回答を取得する関数。
    
    ※今回のモデルでは、"temperature" や "maxOutputTokens" はサポートされていないため、
      必要最低限の "contents" キーのみを含むペイロードを送信する。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite-preview-02-05:generateContent?key={API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        candidates = response.json().get("candidates", [])
        if candidates:
            return candidates[0].get("content", "回答が見つかりませんでした。")
        else:
            return "回答が見つかりませんでした。"
    else:
        return f"エラー: {response.status_code} {response.text}"

def generate_initial_answers(question, persona_params):
    """
    ユーザーの初回質問に対して、各ペルソナの回答を生成する関数。
    """
    answers = {}
    for persona, params in persona_params.items():
        prompt = (
            f"【{params['style']}な視点】\n"
            f"以下の質問に答えてください。\n"
            f"質問: {question}\n"
            f"詳細: {params['detail']}"
        )
        answer = call_gemini_api(prompt)
        answers[persona] = answer
    return answers

def simulate_persona_discussion(answers):
    """
    各ペルソナの初回回答をもとに、実際の人間の会話のように、  
    ゆっくり丁寧に議論している様子をシミュレーションする関数。
    
    ※以下のプロンプトでは、出力を次の形式で求める：
      - 各行は「ペルソナ1: 発言内容」「ペルソナ2: 発言内容」と短い一文で記述。
      - JSON等の余分な記述は含まず、シンプルな対話形式にする。
      - 会話中に「…」や短い沈黙表現も含むようにする。
    """
    discussion_prompt = (
        "次の各ペルソナの初回回答をもとに、友達同士がゆっくりと話している会話を作ってください。\n"
    )
    for persona, answer in answers.items():
        discussion_prompt += f"{persona}の初回回答: {answer}\n"
    discussion_prompt += (
        "\n出力形式：\n"
        "ペルソナ1: 短い一文\n"
        "ペルソナ2: 短い一文\n"
        "ペルソナ3: 短い一文\n"
        "※各行は一つの発言で、会話全体がシンプルな対話形式になるようにしてください。"
    )
    
    discussion = call_gemini_api(discussion_prompt)
    return discussion

def generate_followup_question(discussion):
    """
    ペルソナ間のディスカッションから、ユーザーへのフォローアップ質問を抽出または生成する関数。
    """
    if "？" in discussion:
        followup = discussion.split("？")[0] + "？"
    else:
        followup = "この件について、さらに詳しく教えていただけますか？"
    return followup

# --- Streamlit UI ---
st.title("ぼくのともだち")

# ユーザーからの初回質問入力
question = st.text_area("最初の質問を入力してください", placeholder="ここに質問を入力", height=150)

if st.button("送信"):
    if question:
        # 内部処理としてパラメーター自動調整
        persona_params = adjust_parameters(question)
        
        # 各ペルソナの初回回答生成
        st.write("### 各ペルソナからの初回回答")
        initial_answers = generate_initial_answers(question, persona_params)
        for persona, answer in initial_answers.items():
            st.markdown(f"**{persona}**: {answer}")

        # ペルソナ間の会話シミュレーション（UDスタイルの対話形式）
        st.write("### ペルソナ間のディスカッション")
        discussion = simulate_persona_discussion(initial_answers)
        st.markdown(discussion)

        # フォローアップ質問生成
        st.write("### フォローアップ質問")
        followup_question = generate_followup_question(discussion)
        st.markdown(f"**システムからの質問:** {followup_question}")

        # ユーザーによるフォローアップ回答の入力
        additional_input = st.text_input("上記のフォローアップ質問に対するあなたの回答を入力してください")
        if additional_input:
            st.write("### 追加回答を反映した会話の更新")
            update_prompt = (
                f"ユーザーからの追加回答: {additional_input}\n"
                f"先ほどのディスカッション: {discussion}\n"
                "この情報を踏まえ、今後の会話の方向性について意見を述べてください。"
            )
            updated_discussion = call_gemini_api(update_prompt)
            st.markdown(updated_discussion)
    else:
        st.warning("質問を入力してください")
