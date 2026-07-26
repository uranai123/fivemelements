# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components  # 💡 モバイル・SEO最適化用
import json
import os
import pandas as pd
import altair as alt
from datetime import datetime, time, date, timedelta
import extra_streamlit_components as stx
from google import genai
from dotenv import load_dotenv
import base64
from pathlib import Path

# 既存の計算エンジン・マスターから関数をインポート
from generate_meishiki5 import get_meishiki_data

# 環境変数の読み込みとGeminiクライアントの初期化
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

# 1. ページ全体の基本設定
st.set_page_config(
    page_title="四柱推命 深層鑑定・五行解析ポータル | Five Elements Lab",
    page_icon="🔮",
    layout="wide"
)

# 2. 【SEO & モバイル操作性改善】全項目ピンチズーム無制限化スクリプト
seo_and_zoom_script = """
<script>
(function() {
    function forceEnableZoom() {
        // 自画面・親画面・最上位画面のすべてをターゲットにする
        const docs = [document];
        try { if (window.parent && window.parent.document) docs.push(window.parent.document); } catch(e){}
        try { if (window.top && window.top.document) docs.push(window.top.document); } catch(e){}

        docs.forEach(doc => {
            if (!doc) return;

            // 1. 既存のズーム制限メタタグを全削除し、ピンチ許可タグを挿入
            let viewports = doc.querySelectorAll('meta[name="viewport"]');
            viewports.forEach(v => v.remove());

            let meta = doc.createElement('meta');
            meta.name = 'viewport';
            meta.content = 'width=device-width, initial-scale=1.0, minimum-scale=0.2, maximum-scale=5.0, user-scalable=yes';
            doc.head.appendChild(meta);

            // 2. アプリ全体のタッチ操作制限（touch-action）をCSSで強制解除
            if (!doc.getElementById('zoom-force-style')) {
                let style = doc.createElement('style');
                style.id = 'zoom-force-style';
                style.innerHTML = `
                    *, html, body, .stApp, #root, .main, .block-container {
                        touch-action: auto !important;
                        -webkit-text-size-adjust: 100% !important;
                    }
                `;
                doc.head.appendChild(style);
            }
        });
    }

    // 初回実行に加え、Streamlitの再描画で上書きされないよう1秒ごとに自動更新
    forceEnableZoom();
    setInterval(forceEnableZoom, 1000);
})();
</script>
"""
components.html(seo_and_zoom_script, height=0, width=0)

# --- ⚙️ ユーティリティ・補助関数の定義 ---

@st.cache_data
def load_column_md(filename):
    """content/column/ フォルダ内の Markdown ファイルを安全に読み込む関数（キャッシュ付き）"""
    filepath = os.path.join("content", "column", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        readable_path = filepath.replace("\\", "/")
        return f"⚠️ 記事ファイル `/{readable_path}` が見つかりませんでした。ファイル名やフォルダの配置を確認してください。"

@st.cache_data
def load_knowledge_md(filename):
    """content/knowledge/ 配下のmdファイルを安全に読み込む関数（キャッシュ付き）"""
    filepath = os.path.join("content", "knowledge", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        readable_path = filepath.replace("\\", "/")
        return f"⚠️ 用語の解説ファイル `/{readable_path}` が見つかりません。ファイル配置を確認してください。"

def load_spec_text(filepath):
    """仕様書テキストの読み込み"""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def generate_fortune_telling_ai(meishiki_json, exam_spec, output_spec):
    """Gemini APIを呼び出して鑑定書を生成する（自動混雑回避・最適化版）"""
    if not client:
        return "【エラー】環境変数 GOOGLE_API_KEY が設定されていないため、AI鑑定を実行できません。"
        
    system_instruction = f"""
あなたは四柱推命の専門家であり、卓越した鑑定士です。
以下の【鑑定仕様書】の論理法則を厳守し、【出力仕様書】のトーン＆マナーに従って鑑定書を作成してください。
五行バランスおよび身強・身弱のデータが与えられている場合は、その客観的数値をベースに深層心理や運勢を紐解いてください。
もし時柱のデータが「不明」や空欄になっている場合は、生まれた時刻がわからない状態（三柱推命）として、日柱・月柱・年柱を中心にプロフェッショナルな鑑定を行ってください。

【鑑定仕様書】{exam_spec}

【出力仕様書】{output_spec}
"""
    user_input = f"以下の命式および分析データに基づき、鑑定書を生成してください。\n--- 命式データ ---\n{json.dumps(meishiki_json, ensure_ascii=False, indent=2)}"
    
    model_priority = [
        "gemini-3.5-flash",
        "gemini-2.0-flash",
        "gemini-3.1-flash-lite"
    ]
    
    for model_name in model_priority:
        try:
            full_model_path = f"models/{model_name}"
            
            response = client.models.generate_content(
                model=full_model_path,
                contents=user_input,
                config={
                    "system_instruction": system_instruction, 
                    "temperature": 0.3
                }
            )
            return response.text
            
        except Exception as e:
            print(f"【システム通知】{model_name} が混雑またはエラーのため、次のモデルに切り替えます。詳細: {e}")
            continue
            
    return "申し訳ありません。現在鑑定サーバーが大変混雑しております。しばらく経ってから再度お試しください。"

# --- 🌟 流年（1年ごとの運気）算出用の定義と関数 🌟 ---
STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEM_INFO = {
    "甲": {"elem": 0, "polarity": 1}, "乙": {"elem": 0, "polarity": -1},
    "丙": {"elem": 1, "polarity": 1}, "丁": {"elem": 1, "polarity": -1},
    "戊": {"elem": 2, "polarity": 1}, "己": {"elem": 2, "polarity": -1},
    "庚": {"elem": 3, "polarity": 1}, "辛": {"elem": 3, "polarity": -1},
    "壬": {"elem": 4, "polarity": 1}, "癸": {"elem": 4, "polarity": -1},
}

JUNIUN_MAP = {
    "甲": {"亥": "長生", "子": "沐浴", "丑": "冠帯", "寅": "建禄", "卯": "帝旺", "辰": "衰", "巳": "病", "午": "死", "未": "墓", "申": "絶", "酉": "胎", "戌": "養"},
    "乙": {"午": "長生", "巳": "沐浴", "辰": "冠帯", "卯": "建禄", "寅": "帝旺", "丑": "衰", "子": "病", "亥": "死", "戌": "墓", "酉": "絶", "申": "胎", "未": "養"},
    "丙": {"寅": "長生", "卯": "沐浴", "辰": "冠帯", "巳": "建禄", "午": "帝旺", "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "絶", "子": "胎", "丑": "養"},
    "丁": {"酉": "長生", "申": "沐浴", "未": "冠帯", "午": "建禄", "巳": "帝旺", "辰": "衰", "卯": "病", "寅": "死", "丑": "墓", "子": "絶", "亥": "胎", "戌": "養"},
    "戊": {"寅": "長生", "卯": "沐浴", "辰": "冠帯", "巳": "建禄", "午": "帝旺", "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "絶", "子": "胎", "丑": "養"},
    "己": {"酉": "長生", "申": "沐浴", "未": "冠帯", "午": "建禄", "巳": "帝旺", "辰": "衰", "卯": "病", "寅": "死", "丑": "墓", "子": "絶", "亥": "胎", "戌": "養"},
    "庚": {"巳": "長生", "午": "沐浴", "未": "冠帯", "申": "建禄", "酉": "帝旺", "戌": "衰", "亥": "病", "子": "死", "丑": "墓", "寅": "絶", "卯": "胎", "辰": "養"},
    "辛": {"子": "長生", "亥": "沐浴", "戌": "冠帯", "酉": "建禄", "申": "帝旺", "未": "衰", "午": "病", "巳": "死", "辰": "墓", "卯": "絶", "寅": "胎", "丑": "養"},
    "壬": {"申": "長生", "酉": "沐浴", "戌": "冠帯", "亥": "建禄", "子": "帝旺", "丑": "衰", "寅": "病", "卯": "死", "辰": "墓", "巳": "絶", "午": "胎", "未": "養"},
    "癸": {"卯": "長生", "寅": "沐浴", "丑": "冠帯", "子": "建禄", "亥": "帝旺", "戌": "衰", "酉": "病", "申": "死", "未": "墓", "午": "絶", "巳": "胎", "辰": "養"}
}

def get_yearly_ganzi(year):
    stem_idx = (year - 4) % 10
    branch_idx = (year - 4) % 12
    return STEMS[stem_idx], BRANCHES[branch_idx]

def get_hensei(day_stem, year_stem):
    ds_info = STEM_INFO.get(day_stem)
    ys_info = STEM_INFO.get(year_stem)
    if not ds_info or not ys_info:
        return "－"
    ds_elem, ds_pol = ds_info["elem"], ds_info["polarity"]
    ys_elem, ys_pol = ys_info["elem"], ys_info["polarity"]
    same_polarity = (ds_pol == ys_pol)
    rel = (ys_elem - ds_elem) % 5
    if rel == 0: return "比肩" if same_polarity else "劫財"
    elif rel == 1: return "食神" if same_polarity else "傷官"
    elif rel == 2: return "偏財" if same_polarity else "正財"
    elif rel == 3: return "偏官" if same_polarity else "正官"
    elif rel == 4: return "偏印" if same_polarity else "印綬"
    return "－"

def get_juniun(day_stem, year_branch):
    stem_map = JUNIUN_MAP.get(day_stem)
    if not stem_map: return "－"
    return stem_map.get(year_branch, "－")

# --- 状態管理（Session State）の初期化 ---
if "meishiki_result" not in st.session_state:
    st.session_state.meishiki_result = None
if "ai_appraisal" not in st.session_state:
    st.session_state.ai_appraisal = None
if "is_time_unknown" not in st.session_state:
    st.session_state.is_time_unknown = False

# ヘッダーセクション（HTML/CSS・レスポンシブ最適化済）
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Kaisei+Decol:wght@700&family=Noto+Serif+JP:wght@600;900&family=Yuji+Syuku&display=swap" rel="stylesheet">
    <style>
    .shichu-title-container {
        background: linear-gradient(135deg, #090D16 0%, #151E2E 100%);
        padding: 55px 20px 30px 20px;
        border-radius: 12px;
        border: 1px solid #2A3B56;
        border-bottom: 4px solid #F59E0B;
        text-align: center;
        margin-bottom: 25px;
        position: relative;
        overflow: hidden;
        box-shadow: inset 0 0 25px rgba(0, 0, 0, 0.9);
    }
    .shichu-kanzhi-banner {
        position: absolute;
        top: 0; left: 0; width: 100%;
        background: rgba(8, 12, 21, 0.95);
        border-bottom: 1px solid rgba(245, 158, 11, 0.5);
        padding: 8px 0;
        font-family: 'Noto Serif JP', serif;
        font-size: 14px; font-weight: 900; color: #FBBF24;
        letter-spacing: 0.5em; text-indent: 0.5em;
        white-space: nowrap; text-shadow: 0 0 8px rgba(251, 191, 36, 0.6);
    }
    .shichu-main-title {
        font-family: 'Yuji Syuku', 'Kaisei Decol', 'HG行書体', serif !important;
        font-size: 38px; font-weight: 700; color: #FFFFFF; letter-spacing: 4px;
        margin: 20px 0 10px 0;
        text-shadow: -1.5px -1.5px 0 #000, 1.5px -1.5px 0 #000, -1.5px 1.5px 0 #000, 1.5px 1.5px 0 #000, 0px 6px 15px rgba(0,0,0,0.95);
        position: relative; z-index: 2;
    }
    .shichu-sub-title {
        font-family: 'Noto Serif JP', serif !important;
        font-size: 13.5px; color: #FBBF24; letter-spacing: 4px;
        margin: 0 0 8px 0; font-weight: 700;
        position: relative; z-index: 2; text-shadow: 0px 2px 5px rgba(0,0,0,0.9);
    }
    .shichu-lab-text {
        font-family:'Cormorant Garamond',serif;
        font-size:14px; color:#C9CCD4; letter-spacing:1.2px;
        margin-top:10px; font-weight: 500; text-transform:none;
        transform: translateX(70px);
    }

    @media (max-width: 768px) {
        .shichu-title-container {
            padding: 45px 10px 20px 10px;
        }
        .shichu-kanzhi-banner {
            font-size: 10px;
            letter-spacing: 0.2em;
        }
        .shichu-main-title {
            font-size: 26px !important;
            letter-spacing: 2px !important;
        }
        .shichu-sub-title {
            font-size: 11.5px !important;
            letter-spacing: 1.5px !important;
        }
        .shichu-lab-text {
            transform: none !important;
            text-align: center;
            margin-top: 6px;
        }
    }
    </style>
    <div class="shichu-title-container">
        <div class="shichu-kanzhi-banner">甲・乙・丙・丁・戊・己・庚・辛・壬・癸・子・丑・寅・卯・辰・巳・午・未・申・酉・戌・亥</div>
        <h1 class="shichu-main-title">☯️ 四柱推命 深層鑑定</h1>
        <p class="shichu-sub-title">― 五行バランス解析に基づく運命診断 ―</p>
        <p class="shichu-lab-text">Five Elements Lab</p>
    </div>
    """,
    unsafe_allow_html=True
)

tab_fortune, tab_column, tab_dictionary, tab_about = st.tabs(["✨ 鑑定する", "📚 四柱推命コラム", "📖 知識辞典", "🏛️ 当ラボについて"])

# ==========================================
# 1. 鑑定する タブ
# ==========================================
with tab_fortune:
    st.header("命式鑑定")
    st.write("生年月日・出生時刻を選択し、「命式を算出する」ボタンを押してください。")
    
    with st.container(border=True):
        st.subheader("📋 鑑定用プロフィールの入力")
        
        col_date, col_time, col_gender = st.columns(3)
        with col_date:
            input_date = st.date_input("生年月日", value=date(1973, 5, 28), min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
        with col_time:
            is_unknown_time = st.checkbox("出生時刻が不明", value=False)
            if is_unknown_time:
                input_time = "不明"
            else:
                st.markdown("<p style='font-size: 14px; margin-bottom: 8px;'>出生時刻（24時間表記）</p>", unsafe_allow_html=True)
                c_hour, c_min = st.columns(2)
                with c_hour:
                    selected_hour = st.selectbox(
                        "時", 
                        options=list(range(24)), 
                        index=1, 
                        format_func=lambda h: f"{h:02d}時",
                        label_visibility="collapsed"
                    )
                with c_min:
                    selected_min = st.selectbox(
                        "分", 
                        options=list(range(60)), 
                        index=7, 
                        format_func=lambda m: f"{m:02d}分",
                        label_visibility="collapsed"
                    )
                input_time = time(selected_hour, selected_min)
        with col_gender:
            input_gender = st.selectbox("性別", options=["男", "女"], index=1)
            
        submit_button = st.button("🔮 命式を算出する", type="primary", use_container_width=True)

    if submit_button:
        if input_time == "不明":
            target_datetime = datetime.combine(input_date, time(12, 0))
            st.session_state.is_time_unknown = True
        else:
            target_datetime = datetime.combine(input_date, input_time)
            st.session_state.is_time_unknown = False

        with st.spinner("計算エンジン駆動中... 命式を算出しています..."):
            try:
                st.session_state.meishiki_result = get_meishiki_data(target_datetime, gender=input_gender)
                st.session_state.ai_appraisal = None
                st.success("🎉 命式の算出が完了しました！")
            except Exception as e:
                st.error(f"計算エラーが発生しました: {e}")

    if st.session_state.meishiki_result:
        meishiki_data = st.session_state.meishiki_result
        st.markdown("---")
        
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.subheader("📊 命式")
            pillars = meishiki_data.get("pillars", [])
            
            header_cols = st.columns(5)
            header_cols[0].markdown("**項目**")
            header_cols[1].markdown("**時柱**")
            header_cols[2].markdown("**日柱**")
            header_cols[3].markdown("**月柱**")
            header_cols[4].markdown("**年柱**")
            
            row_labels = [
                ("天干 (通変星)", "stem", "stem_hensei"),
                ("地支 (蔵干)", "branch", "zokan"),
                ("蔵干通変星", "zokan_hensei", None),
                ("十二運星", "juniun", None)
            ]
            
            for label, key1, key2 in row_labels:
                cols = st.columns(5)
                cols[0].write(f"**{label}**")
                for idx, p_name in enumerate(["時", "日", "月", "年"]):
                    p_data = next((p for p in pillars if p["name"] == p_name), None)
                    if p_data:
                        if p_name == "時" and st.session_state.is_time_unknown:
                            cols[idx+1].info("不明")
                        elif p_data.get(key1) in ["－", "", None]:
                            cols[idx+1].info("－")
                        else:
                            cell_text = f"{p_data[key1]} ({p_data[key2]})" if key2 and p_data.get(key2) else f"{p_data[key1]}"
                            cols[idx+1].info(cell_text)
                    else:
                        cols[idx+1].write("－")
            
            st.write("")
            st.markdown(f"**空亡（天中殺）:** `{meishiki_data.get('kuubo')}`")
            
            # 大運タイムライン
            st.markdown("---")
            st.subheader("⏳ 大運タイムライン（10年ごとの運気）")
            daun_list = meishiki_data.get("daun", [])
            
            if daun_list and "error" not in daun_list[0]:
                def format_age_num(age_val):
                    num_str = str(age_val).strip()
                    if len(num_str) == 1:
                        zenkaku_map = {"0":"０", "1":"１", "2":"２", "3":"３", "4":"４", "5":"５", "6":"６", "7":"７", "8":"８", "9":"９"}
                        return zenkaku_map.get(num_str, num_str)
                    return num_str

                age_html_list = []
                for i, d in enumerate(daun_list):
                    start_age = int(str(d.get('start_age')).split('歳')[0])
                    if i < len(daun_list) - 1:
                        next_start = int(str(daun_list[i+1].get('start_age')).split('歳')[0])
                        end_age = next_start - 1
                    else:
                        end_age = start_age + 9
                    
                    s_formatted = format_age_num(start_age)
                    e_formatted = format_age_num(end_age)
                    age_html_list.append(f"{s_formatted}<br>～<br>{e_formatted}")

                kanzhis_raw = [str(d.get("ganzhi", "－－")).split()[0][:2] for d in daun_list]
                kanzhis_html = []
                for kz in kanzhis_raw:
                    if len(kz) >= 2:
                       kanzhis_html.append(f"<span style='font-size: 16px; font-weight: bold;'>{kz[0]}</span><br><span style='font-size: 16px; font-weight: bold;'>{kz[1]}</span>")
                    else:
                        kanzhis_html.append(f"{kz}<br>&nbsp;")

                henseis = [d.get("tenkan_hensei", "－").strip("() ") for d in daun_list]
                juniuns = [d.get("juniun", "－").strip() for d in daun_list]
                
                html_table = f"""
                <div style="overflow-x: auto; width: 100%; border: 1px solid #334155; border-radius: 8px;">
                    <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; text-align: center; font-size: 14px; line-height: 1.4; background-color: #1E293B;">
                        <tr style="background-color: #0F172A; border-bottom: 2px solid #334155;">
                            <td style="padding: 10px 8px; font-weight: bold; color: #94A3B8; min-width: 70px; text-align: left; background-color: #111827;">年齢</td>
                            {"".join([f"<td style='padding: 8px 4px; font-weight: bold; color: #38BDF8; vertical-align: middle; font-size: 14px;'>{age}</td>" for age in age_html_list])}
                        </tr>
                        <tr style="border-bottom: 1px solid #334155;">
                            <td style="padding: 10px 8px; font-weight: bold; color: #94A3B8; text-align: left; background-color: #111827;">干支</td>
                            {"".join([f"<td style='padding: 8px 4px; color: #F8FAFC; font-weight: bold;'>{kz}</td>" for kz in kanzhis_html])}
                        </tr>
                        <tr style="border-bottom: 1px solid #334155;">
                            <td style="padding: 10px 8px; font-weight: bold; color: #94A3B8; text-align: left; background-color: #111827;">通変星</td>
                            {"".join([f"<td style='padding: 8px 4px; color: #E2E8F0; font-size: 13px; white-space: nowrap;'>{hs}</td>" for hs in henseis])}
                        </tr>
                        <tr>
                            <td style="padding: 10px 8px; font-weight: bold; color: #94A3B8; text-align: left; background-color: #111827;">十二運</td>
                            {"".join([f"<td style='padding: 8px 4px; color: #94A3B8; font-size: 13px; white-space: nowrap;'>{ju}</td>" for ju in juniuns])}
                        </tr>
                    </table>
                </div>
                """
                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.warning("大運データが取得できないか、エラーが発生しています。")

            # 流年タイムライン
            st.write("")
            st.markdown("---")
            st.subheader("📅 流年タイムライン（1年ごとの運気）")
            
            day_stem = None
            if pillars:
                day_pillar = next((p for p in pillars if p["name"] == "日"), None)
                if day_pillar and "stem" in day_pillar:
                    day_stem = day_pillar["stem"].strip()[0]
            
            if day_stem and day_stem in JUNIUN_MAP:
                current_year = datetime.now().year
                years_range = list(range(current_year - 3, current_year + 7))
                
                years_cells, age_cells, kanzhi_cells, hensei_cells, juniun_cells = [], [], [], [], []
                for y in years_range:
                    is_curr = (y == current_year)
                    if is_curr:
                        years_cells.append(f"<td style='padding: 8px 4px; font-weight: bold; vertical-align: middle; font-size: 14px; color: #F59E0B; background-color: #2D3748;'>{y % 100}年</td>")
                        age_cells.append(f"<td style='padding: 8px 4px; font-weight: bold; color: #F59E0B; background-color: #2D3748;'>{y - input_date.year}歳</td>")
                    else:
                        years_cells.append(f"<td style='padding: 8px 4px; font-weight: bold; vertical-align: middle; font-size: 14px; color: #38BDF8;'>{y % 100}年</td>")
                        age_cells.append(f"<td style='padding: 8px 4px; color: #94A3B8;'>{y - input_date.year}歳</td>")
                    
                    stem, branch = get_yearly_ganzi(y)
                    if is_curr:
                        kanzhi_cells.append(f"<td style='padding: 8px 4px; background-color: #2D3748;'><span style='font-size: 16px; font-weight: bold; color: #F59E0B;'>{stem}</span><br><span style='font-size: 16px; font-weight: bold; color: #F59E0B;'>{branch}</span></td>")
                    else:
                        kanzhi_cells.append(f"<td style='padding: 8px 4px; background-color: #1E293B;'><span style='font-size: 16px; font-weight: bold; color: #F8FAFC;'>{stem}</span><br><span style='font-size: 16px; font-weight: bold; color: #94A3B8;'>{branch}</span></td>")
                    
                    y_stem, y_branch = get_yearly_ganzi(y)
                    hensei_val = get_hensei(day_stem, y_stem)
                    juniun_val = get_juniun(day_stem, y_branch)
                    
                    if is_curr:
                        hensei_cells.append(f"<td style='padding: 8px 4px; color: #F59E0B; font-weight: bold; font-size: 13px; white-space: nowrap; background-color: #2D3748;'>{hensei_val}</td>")
                        juniun_cells.append(f"<td style='padding: 8px 4px; color: #F59E0B; font-weight: bold; font-size: 13px; white-space: nowrap; background-color: #2D3748;'>{juniun_val}</td>")
                    else:
                        hensei_cells.append(f"<td style='padding: 8px 4px; color: #E2E8F0; font-size: 13px; white-space: nowrap;'>{hensei_val}</td>")
                        juniun_cells.append(f"<td style='padding: 8px 4px; color: #94A3B8; font-size: 13px; white-space: nowrap;'>{juniun_val}</td>")
                
                ryunen_table = f"""
                <div style="overflow-x: auto; width: 100%; border: 1px solid #334155; border-radius: 8px;">
                    <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; text-align: center; font-size: 14px; line-height: 1.4; background-color: #1E293B;">
                        <tr style="background-color: #0F172A; border-bottom: 2px solid #334155;">
                            <td style="padding: 10px 8px; font-weight: bold; color: #94A3B8; min-width: 70px; text-align: left; background-color: #111827;">西暦(略)</td>
                            {"".join(years_cells)}
                        </tr>
                        <tr style="border-bottom: 1px solid #334155;">
                            <td style="padding: 10px 8px; font-weight: bold; color: #94A3B8; text-align: left; background-color: #111827;">年齢</td>
                            {"".join(age_cells)}
                        </tr>
                        <tr style="border-bottom: 1px solid #334155;">
                            <td style="padding: 10px 8px; font-weight: bold; color: #94A3B8; text-align: left; background-color: #111827;">干支</td>
                            {"".join(kanzhi_cells)}
                        </tr>
                        <tr style="border-bottom: 1px solid #334155;">
                            <td style="padding: 10px 8px; font-weight: bold; color: #94A3B8; text-align: left; background-color: #111827;">通変星</td>
                            {"".join(hensei_cells)}
                        </tr>
                        <tr>
                            <td style="padding: 10px 8px; font-weight: bold; color: #94A3B8; text-align: left; background-color: #111827;">十二運</td>
                            {"".join(juniun_cells)}
                        </tr>
                    </table>
                </div>
                """
                st.markdown(ryunen_table, unsafe_allow_html=True)
            else:
                st.warning("日干の抽出に失敗したため流年タイムラインを表示できません。")

        with col_right:
            st.subheader("☯️ 五行・身強身弱分析")
            analysis = meishiki_data.get("analysis", {})
            
            if analysis:
                st.metric(label="命式・身弱身強判定", value=f"【 {analysis.get('judgment')} 】")
                if st.session_state.is_time_unknown:
                    st.caption("⚠️ 時刻不明（三柱）のため、時柱の五行エネルギーは除外して計算されています。")
                st.markdown(f"**日干の五行:** `{analysis.get('day_stem_element')}`")
                
                total_score = analysis.get("jitou_score", 0) + analysis.get("itau_score", 0)
                progress_val = analysis.get("jitou_score", 0) / total_score if total_score > 0 else 0.5
                st.progress(progress_val, text=f"自党（比劫·印星）: {analysis.get('jitou_score')} スコア")
                st.caption(f"異党（食傷·財·官）: {analysis.get('itau_score')} スコア")
                
                df_gogyo = pd.DataFrame([
                    {"五行": elem, "スコア": analysis.get("gogyo_balance", {}).get(elem, 0.0)}
                    for elem in ["木", "火", "土", "金", "水"]
                ])
                
                chart = alt.Chart(df_gogyo).mark_bar().encode(
                    x=alt.X("五行:N", sort=["木", "火", "土", "金", "水"], axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("スコア:Q"),
                    color=alt.Color("五行:N", scale=alt.Scale(
                        domain=["土", "水", "火", "金", "木"],
                        range=["#F1C40F", "#2C3E50", "#E74C3C", "#BDC3C7", "#76D7C4"]
                    ), legend=None)
                ).properties(width="container", height=300)
                st.altair_chart(chart, use_container_width=True)
                
            st.markdown("---")
            st.subheader("🤖 運診診断の実行")

            # 🍪 クッキーによる利用制限システム
            if "cookie_manager" not in st.session_state:
                st.session_state.cookie_manager = stx.CookieManager()
            
            cookie_manager = st.session_state.cookie_stats_manager if "cookie_stats_manager" in st.session_state else st.session_state.cookie_manager

            cookie_data = cookie_manager.get(cookie="fortune_usage_stats")

            usage_count = 0
            reset_at_str = ""
            can_appraise = True

            if cookie_data:
                try:
                    data = json.loads(cookie_data)
                    reset_at = datetime.fromisoformat(data["reset_at"])
                    
                    if datetime.now() > reset_at:
                        cookie_manager.delete("fortune_usage_stats")
                        usage_count = 0
                    else:
                        usage_count = data["count"]
                        reset_at_str = reset_at.strftime("%Y/%m/%d %H:%M:%S")
                        if usage_count >= 3:
                            can_appraise = False
                except Exception:
                    pass

            if not can_appraise:
                st.warning(
                    f"🚫 本日の無料鑑定枠（3回）をすべて消費しました。次の枠は **{reset_at_str}** 以降に復活します。"
                )
            else:
                st.info(f"🔮 本日の残り鑑定可能回数: **{3 - usage_count}回** / 3回")
            
            ai_button = st.button(
                "🔮 仕様書に基づく鑑定書を生成する", 
                type="secondary", 
                use_container_width=True, 
                disabled=(not API_KEY) or (not can_appraise)
            )
            
            st.markdown(
                """
                <div style="background-color: #111827; border: 1px solid #334155; border-radius: 6px; padding: 12px 15px; margin-top: 10px;">
                    <p style="color: #94A3B8; font-size: 11.5px; line-height: 1.5; margin: 0;">
                        🔒 <strong>プライバシー保護について</strong><br>
                        本鑑定システムに入力された生年月日および出生データは、解析処理のみに使用されます。入力データが解析エンジンの学習や二次利用に供されることは一切ございません。どうぞ安心して、ご自身の命式と対話してください。
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if ai_button and can_appraise:
                loading_placeholder = st.empty()
                
                loading_placeholder.markdown(
                    """
                    <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); 
                                border: 1px solid #3B82F6; border-left: 6px solid #3B82F6; 
                                padding: 20px; border-radius: 8px; margin: 15px 0;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                                animation: pulse_blinker 2.0s linear infinite;">
                        <h4 style="color: #38BDF8; margin: 0; font-size: 16px; font-weight: bold;">🔮 深層鑑定士が執筆中...</h4>
                        <p style="color: #94A3B8; margin: 10px 0 0 0; font-size: 13.5px; line-height: 1.6;">
                            現在、Geminiが命式ロジックと仕様書を照合し、あなただけのディープな鑑定書を生成しています。<br><br>
                            ⚡ <strong>完了まで約20〜30秒かかります。</strong>画面が暗くなっていますが、正常に計算中ですのでこのまま閉じずにお待ちください。
                        </p>
                    </div>
                    <style>
                    @keyframes pulse_blinker {
                        0% { opacity: 0.7; }
                        50% { opacity: 1; border-color: #F59E0B; }
                        100% { opacity: 0.7; }
                    }
                    </style>
                    """, 
                    unsafe_allow_html=True
                )

                import time
                time.sleep(0.2)

                try:
                    payload = dict(meishiki_data)
                    if st.session_state.is_time_unknown:
                        payload["time_status"] = "UNKNOWN (Three Pillars Mode)"
                    
                    exam_spec = load_spec_text("config/prompt_examination_specification(VOL.13).txt")
                    output_spec = load_spec_text("config/prompt_output_specification.txt")
                    
                    ai_result = generate_fortune_telling_ai(payload, exam_spec, output_spec)
                    
                    if ai_result.startswith("申し訳ありません"):
                        loading_placeholder.empty() 
                        st.error(ai_result)
                    else:
                        new_count = usage_count + 1
                        new_reset_at = datetime.now() + timedelta(days=1) if new_count == 1 else (reset_at if cookie_data else datetime.now() + timedelta(days=1))

                        new_cookie_data = {
                            "count": new_count,
                            "reset_at": new_reset_at.isoformat()
                        }

                        cookie_manager.set(
                            cookie="fortune_usage_stats",
                            val=json.dumps(new_cookie_data),
                            expires_at=datetime.now() + timedelta(days=365)
                        )

                        st.session_state.ai_appraisal = ai_result
                        st.toast(f"鑑定書が完成しました！（残り {3 - new_count} 回）", icon="🎉")
                        st.rerun()
                        
                except Exception as ai_err:
                    loading_placeholder.empty()
                    st.error("⚠️ AIサーバー混雑のため、少し時間を置いて再度お試しください。")

        if st.session_state.ai_appraisal:
            st.markdown("---")
            st.subheader("📜 深層鑑定書 (VOL.13 統合仕様版)")
            with st.container(border=True):
                st.markdown(st.session_state.ai_appraisal)

# ==========================================
# 2. 四柱推命コラム タブ
# ==========================================
with tab_column:
    st.header("📚 深層分析コラム・サバイバル術")
    st.write("四柱推命の思想を現代のライフ戦略や心理学に落とし込み、メタ認知を鍛えるための特製コラムです。")

    COL_CATEGORIES = [
        {"id": "すべて", "emoji": "🗂️", "title": "すべてのコラム", "desc": "現在公開中のすべての知的サバイバルコラムを一覧表示します。"},
        {"id": "🧠 深層心理・自己分析", "emoji": "🧠", "title": "深層心理・自己分析", "desc": "ユング心理学的アプローチで、自らのペルソナと影（シャドウ）を統合する。"},
        {"id": "🏢 対人・組織戦略（処世術）", "emoji": "🏢", "title": "対人・組織戦略", "desc": "職場に蔓延る『奴隷道徳』をスルーし、星の性質で手綱を握るマキャベリ的処世術。"},
        {"id": "⏳ 運気の波・タイミングの科学", "emoji": "⏳", "title": "運気の波・タイミング", "desc": "『絶』や『空亡』の更地化を恐れず、次の10年のインスピレーションを待つ動的戦略。"},
        {"id": "☯️ 陰陽五行の思想と構造", "emoji": "☯️", "title": "陰陽五行の宇宙論", "desc": "密教の曼荼羅と同じく、歪み（偏り）こそが強烈な個性となる五行システム論。"},
        {"id": "👤 先賢・偉人の命式分析", "emoji": "👤", "title": "先賢・偉人のメタ認知", "desc": "ニーチェなど歴史上の超人たちの命式を覗き見し、その葛藤と共時性を解剖する。"}
    ]

    COLUMN_MAP = {
        "🧠 深層心理・自己分析": [],
        "🏢 対人・組織戦略（処世術）": ["〜フォローなき凋落の数理と、過熱する自尊心のハルシネーション〜.md", "～システムエラーを起こしたNPCの末路～.md"],
        "⏳ 運気の波・タイミングの科学": ["～絶・死の過ごし方～.md"],
        "☯️ 陰陽五行の思想と構造": ["～夢の曼荼羅と、命式が放つ「魂コード」の色彩～.md"],
        "👤 先賢・偉人の命式分析": [],
    }

    if "selected_column_cat" not in st.session_state:
        st.session_state.selected_column_cat = "すべて"

    st.markdown("### 🗂️ コラムテーマを選択する")
    
    cols = st.columns(3)
    for idx, cat in enumerate(COL_CATEGORIES):
        is_selected = (st.session_state.selected_column_cat == cat["id"])
        
        with cols[idx % 3]:
            border_color = "#1E88E5" if is_selected else "#E6E8ED"
            bg_color = "#F0F7FF" if is_selected else "#FFFFFF"
            text_color = "#1E88E5" if is_selected else "#2D3748"
            
            st.markdown(f"""
            <div style="border: 2px solid {border_color}; border-radius: 8px; padding: 12px; 
                        background-color: {bg_color}; min-height: 140px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 20px; margin-bottom: 4px;">{cat["emoji"]}</div>
                <div style="font-weight: bold; font-size: 13px; color: {text_color};">{cat["title"]}</div>
                <div style="font-size: 11px; color: #718096; margin-top: 4px; line-height: 1.3;">{cat["desc"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("読む ➔" if not is_selected else "選択中", key=f"col_btn_{idx}", type="primary" if is_selected else "secondary", use_container_width=True):
                st.session_state.selected_column_cat = cat["id"]
                st.rerun()

    st.markdown("---")

    selected_cat = st.session_state.selected_column_cat
    st.subheader(f"📖 {selected_cat} の記事一覧")

    if selected_cat == "すべて":
        display_map = COLUMN_MAP
    else:
        display_map = {selected_cat: COLUMN_MAP.get(selected_cat, [])}

    found_any = False
    for cat_name, files in display_map.items():
        if files:
            found_any = True
            if selected_cat == "すべて":
                st.markdown(f"#### {cat_name}")
            
            for filename in files:
                title = filename.replace('.md', '').replace('-', ' ').replace('_', ' ').title()
                
                with st.expander(f"📄 {title}", expanded=False):
                    st.markdown(load_column_md(filename))
                
        elif selected_cat != "すべて":
            st.info(f"「{cat_name}」にはまだ記事がありません。執筆までお待ちください。")

    if not found_any and selected_cat == "すべて":
        st.write("まだ記事が登録されていません。")

# ==========================================
# 3. 知識辞典 タブ
# ==========================================
with tab_dictionary:
    st.header("📖 四柱推命 知識辞典")
    st.write("命式やタイムラインに登場する専門用語の意味や、鑑定結果を読み解くコツを解説します。")
    
    DICTIONARY_DATA = {
        "四柱推命の基本": {
            "四柱推命（しちゅうすいめい）": "shichu_suimei.md",
            "四柱推命の歴史": "history.md",
            "陰陽五行（いんようごぎょう）": "inyo_gogyo.md",
            "五行の関係 ～相生・相剋・比和～": "gogyo_relations.md",
            "大運（だいうん）": "taiun.md",
            "流年（りゅうねん）/ 歳運": "ryunen.md"
        },
        "命式の構造と強弱": {
            "命式（めいしき）": "meishiki.md",
            "日干（にっかん）": "nikkan.md",
            "蔵干（ぞうかん）": "zokan.md",
            "日干と命式全体のバランス": "balance.md",
            "月支元命（げっしげんめい）": "gesshi_genmei.md",
            "身強（みきょう）・身弱（みじゃく）": "mikyo_mijaku.md",
            "月令を得ている（げつれい）": "getsurei.md",
            "格局（かっきょく）": "kakyoku.md",
            "空亡（くうぼう）/ 天中殺": "kubo.md"
        },
        "十干・十二支と十二運星": {
            "天干・地支（てんかん・ちし）": "tenkan_chishi.md",
            "六十干支（ろくじっかんし）": "rokuju_kanshi.md",
            "十二運星（じゅうにうんせい）": "juuni_unsei.md",
            "胎・養・長生・沐浴・冠帯・建禄・帝旺・衰・病・死・墓・絶": "juuni_unsei_all.md"
        },
        "通変星（行動・才能のキャラクター）": {
            "比肩（ひけん）": "hiken.md",
            "劫財（ごうざい）": "gozai.md",
            "食神（しょくじん）": "shokujin.md",
            "傷官（しょうかん）": "shokan.md",
            "偏財（へんざい）": "henzai.md",
            "正財（せいざい）": "seizai.md",
            "偏官（へんかん）": "henkan.md",
            "正官（せいかん）": "seikan.md",
            "偏印（へんいん）": "henin.md",
            "印綬（いんじゅ）": "inju.md"
        }
    }

    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("用紙をリアルタイム検索", placeholder="例：身強、空亡、帝旺、偏財...", key="dict_search")
    with col_filter:
        categories = ["すべて表示"] + list(DICTIONARY_DATA.keys())
        selected_category = st.selectbox("カテゴリで絞り込み", options=categories, key="dict_filter")

    st.write("")

    found_any = False
    for cat_name, terms in DICTIONARY_DATA.items():
        if selected_category != "すべて表示" and cat_name != selected_category:
            continue
            
        filtered_terms = {}
        for term, filename in terms.items():
            desc_content = load_knowledge_md(filename)
            
            if not search_query:
                filtered_terms[term] = desc_content
            else:
                q = search_query.lower()
                if (q in term.lower() or 
                    q in desc_content.lower() or 
                    q in cat_name.lower()):
                    filtered_terms[term] = desc_content

        if filtered_terms:
            found_any = True
            st.markdown(f"### 📂 {cat_name}")
            for term, desc in filtered_terms.items():
                with st.expander(f"📙 **{term}**", expanded=False):
                    st.markdown(desc)
            st.write("")

    if not found_any:
        st.info("🔍 入力されたキーワードに一致する用語が見つかりませんでした。別の言葉で試してみてください。")

# ==========================================
# 4. 当ラボについて タブ
# ==========================================
with tab_about:
    logo_path = Path("assets/logo.png")
    logo_b64 = ""
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    logo_img_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 100%; max-width: 180px; border-radius: 50%; box-shadow: 0 4px 20px rgba(245, 158, 11, 0.2); border: 1px solid #F59E0B40;">' if logo_b64 else ''

    about_html = f"""<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 12px; padding: 32px; margin-top: 10px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);">
<div style="display: flex; gap: 32px; align-items: center; flex-wrap: wrap;">
<div style="flex: 0 0 180px; text-align: center; margin: 0 auto;">
{logo_img_html}
</div>
<div style="flex: 1; min-width: 280px;">
<div style="font-family: 'Georgia', serif; font-size: 12px; font-weight: 600; letter-spacing: 2.5px; color: #F59E0B; text-transform: uppercase; margin-bottom: 6px;">Laboratory Profile</div>
<h2 style="font-size: 28px; font-weight: 700; color: #F8FAFC; margin: 0 0 8px 0; letter-spacing: 0.5px;">Five Elements.Lab</h2>
<div style="font-size: 18px; color: #CBD5E1; font-weight: 500; margin-bottom: 16px;">
三上 壬之助 <span style="font-size: 14px; color: #94A3B8; font-weight: normal; margin-left: 6px;">(Mikami Jinnosuke)</span>
</div>
<div style="color: #CBD5E1; font-size: 14.5px; line-height: 1.85; font-weight: 300;">
伝統的な五行論および四柱推命（子平学）の原典・古典をベースに、運命構造の解読と探求を行う命理研究家。<br>
『滴天髄』『子平真詮』をはじめとする原典解釈に基づき、感性に頼らない論理的かつ本質的な鑑定・構造分析を提供する。
</div>
</div>
</div>
<hr style="border: none; border-top: 1px solid #334155; margin: 28px 0 24px 0;">
<div>
<div style="font-size: 12px; font-weight: 600; color: #F59E0B; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 14px;">📜 主要拠り所（四大古典）</div>
<div style="display: flex; gap: 10px; flex-wrap: wrap;">
<span style="background-color: #0F172A; border: 1px solid #F59E0B50; color: #E2E8F0; padding: 8px 16px; border-radius: 6px; font-size: 13.5px; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">『滴天髄』</span>
<span style="background-color: #0F172A; border: 1px solid #F59E0B50; color: #E2E8F0; padding: 8px 16px; border-radius: 6px; font-size: 13.5px; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">『窮通宝鑑』</span>
<span style="background-color: #0F172A; border: 1px solid #F59E0B50; color: #E2E8F0; padding: 8px 16px; border-radius: 6px; font-size: 13.5px; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">『子平真詮』</span>
<span style="background-color: #0F172A; border: 1px solid #F59E0B50; color: #E2E8F0; padding: 8px 16px; border-radius: 6px; font-size: 13.5px; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">『淵海子平』</span>
</div>
</div>
</div>"""
    st.markdown(about_html, unsafe_allow_html=True)