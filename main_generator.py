# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# APIキーを環境変数から読み込む
API_KEY = os.getenv("GOOGLE_API_KEY") 
if not API_KEY:
    raise ValueError("環境変数 GOOGLE_API_KEY が設定されていません。")

client = genai.Client(
    api_key=API_KEY,
    http_options={'headers': {'User-Agent': 'MyDestinyEngine/1.0'}}
)

def load_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_fortune_telling(meishiki_json, exam_spec, output_spec):
    """Gemini APIを呼び出して鑑定文を生成する"""
    
    # システムプロンプトを構築
    system_instruction = f"""
    あなたは四柱推命の専門家であり、卓越した鑑定士です。
    以下の【鑑定仕様書】の論理法則を厳守し、【出力仕様書】のトーン＆マナーに従って鑑定書を作成してください。
    
    【鑑定仕様書】
    {exam_spec}
    
    【出力仕様書】
    {output_spec}
    """

    user_input = f"""
    以下の命式データに基づき、鑑定書を生成してください。
    
    --- 命式データ ---
    {json.dumps(meishiki_json, ensure_ascii=False, indent=2)}
    """

    # 新しいSDKの形式で呼び出し
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=user_input,
        config={
            "system_instruction": system_instruction,
            "temperature": 0.7,
        }
    )
    
    return response.text

def main():
    try:
        meishiki_data = load_json("output/meishiki_data.json")
        exam_spec = load_text("config/prompt_examination_specification(VOL.13).txt")
        output_spec = load_text("config/prompt_output_specification.txt")
    except FileNotFoundError as e:
        print(f"ファイル読み込みエラー: {e}")
        return

    print("AI鑑定を実行中...")
    result_text = generate_fortune_telling(meishiki_data, exam_spec, output_spec)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"output/鑑定結果_{timestamp}.md"
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(result_text)
    
    print(f"鑑定が完了しました: {output_filename}")

if __name__ == "__main__":
    main()