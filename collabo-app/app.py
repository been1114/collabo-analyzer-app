import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re
import time
import os
import altair as alt

# --- [앱 기본 설정] ---
st.set_page_config(
    page_title="콜라보 후보 분석",
    page_icon="🤝",
    layout="wide",
)

# --- [개선된 디자인] CSS 스타일 주입 ---
st.markdown("""
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" xintegrity="sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
<style>
    /* --- 기본 & 폰트 설정 --- */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
    
    html, body, [class*="st-"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        color: #334155; /* 기본 텍스트 색상 변경 (Slate 700) */
    }
    
    /* --- 전체 앱 레이아웃 & 배경 --- */
    .stApp {
        background-image: linear-gradient(to bottom right, #f8fafc, #e2e8f0); /* 부드러운 그라데이션 배경 */
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1000px; /* 최대 너비 조정 */
        margin: 0 auto;
    }

    /* --- 제목 스타일 --- */
    h1, h2, h3 {
        color: #1e293b; /* 제목 색상 (Slate 800) */
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    h1 { text-align: center; }
    h2 { border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; margin-bottom: 1.5rem; }
    h3 { color: #0f172a; } /* 더 진한 색상 (Slate 900) */

    /* --- 카드 컴포넌트 스타일 --- */
    .card {
        background: #ffffff;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease-in-out;
        margin-bottom: 1.5rem;
        height: 100%;
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.07), 0 4px 6px -4px rgba(0, 0, 0, 0.07);
    }
    
    /* --- 버튼 스타일 (그레이 계열) --- */
    .stButton>button {
        background-color: #64748b; /* 진한 그레이 버튼 (Slate 500) */
        color: #ffffff !important; /* 흰색 텍스트 강제 적용 */
        border: 1px solid #475569; /* 어두운 테두리 (Slate 600) */
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        background-color: #475569; /* 호버 시 더 진한 그레이 (Slate 600) */
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
    }
    .stButton>button:active {
        transform: translateY(0);
        background-color: #334155; /* 클릭 시 가장 진한 그레이 (Slate 700) */
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    /* Streamlit 버튼 내부 p 태그의 폰트 색상을 강제로 지정 */
    .stButton>button p {
        color: #ffffff !important;
    }

    /* "돌아가기" 같은 보조 버튼 스타일 */
    .stButton:has(button:contains("←")) button {
        background: #f1f5f9; /* 밝은 회색 (Slate 100) */
        color: #1e293b !important; /* 더 진한 텍스트 색상으로 변경 (Slate 800) */
        box-shadow: none;
        border: 1px solid #e2e8f0;
    }
    .stButton:has(button:contains("←")) button:hover {
        background: #e2e8f0; /* 조금 더 진한 회색 (Slate 200) */
        box-shadow: none;
        transform: none;
    }
    .stButton:has(button:contains("←")) button:active {
        background: #cbd5e1; /* 클릭 시 더 진한 회색 (Slate 300) */
    }

    /* --- 메트릭 스타일 --- */
    [data-testid="stMetric"] {
        background-color: #f8fafc; /* 카드 내부 메트릭 배경 (Slate 50) */
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #e2e8f0; /* (Slate 200) */
    }
    [data-testid="stMetricValue"] {
        font-size: 2.25rem;
        color: #475569 !important; /* 버튼 색상과 통일감 있는 색상 */
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        font-weight: 500;
        color: #64748b; /* (Slate 500) */
    }
    [data-testid="stMetricDelta"] svg {
        display: none; /* 기본 델타 아이콘 숨기기 */
    }

    /* --- 시작 화면 커스텀 스타일 --- */
    .welcome-subtitle {
        text-align: center; color: #64748b; font-size: 1.1rem; margin-bottom: 2.5rem;
    }
    .candidate-list {
        list-style-type: none;
        padding-left: 10px; /* 왼쪽 여백 추가 */
        margin-top: 1rem;
    }
    .candidate-list li {
        background-color: transparent;
        color: #334155;
        padding: 0;
        border-radius: 0;
        font-weight: 500;
        margin-bottom: 1rem; /* 간격 조정 */
        text-align: left; /* 왼쪽 정렬 */
        border: none;
        font-size: 1.2rem; /* 글자 크기 키움 */
    }

    /* --- 대시보드 화면 커스텀 스타일 --- */
    .dashboard-rank-card {
        padding: 1.5rem;
        padding-top: 2.5rem; /* 아이콘 제거 후 여백 조정 */
        text-align: center;
        border-top: 5px solid;
    }
    .rank-emoji { font-size: 2.5rem; }

    /* --- 상세 리포트 화면 커스텀 스타일 --- */
    .report-title-card {
        text-align: center;
        background: #ffffff; /* 흰색 배경으로 변경 */
        color: #1e293b; /* 어두운 텍스트 색상으로 변경 */
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid #e2e8f0; /* 테두리 추가 */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05); /* 그림자 추가 */
    }
    .report-title-card h2 { color: #1e293b; border: none; margin:0; } /* 텍스트 색상 변경 */

    .insight-card {
        border-left: 4px solid #cbd5e1; /* 기본 보더 색상 (Slate 300) */
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: #f8fafc;
        border-radius: 8px;
    }
    .insight-card h5 { margin-top: 0; font-size: 1rem; color: #475569; }
    .insight-card h5 .fa-solid { margin-right: 0.5rem; }
    .insight-card p { margin-bottom: 0; font-size: 0.95rem; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# 스크립트의 절대 경로를 기준으로 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- [API 및 모델 설정] ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
except Exception as e:
    st.error(f"🚨 API 키 설정 오류: .streamlit/secrets.toml 파일을 확인해주세요. 오류: {e}")
    st.stop()

# --- [고정 변수 및 파일 경로 설정] ---
# 데이터 파일이 있는 'data' 디렉토리가 스크립트와 동일한 위치에 있다고 가정합니다.
# 예시 파일 경로입니다. 실제 파일 구조에 맞게 수정해주세요.
RAW_DATA_PATHS = {
    '가나디': os.path.join(BASE_DIR, 'data', 'raw', 'ganadi_raw.csv'),
    '귀멸의 칼날': os.path.join(BASE_DIR, 'data', 'raw', 'kimetsu_raw.csv'),
    'K팝 데몬 헌터스': os.path.join(BASE_DIR, 'data', 'raw', 'kpop_raw.csv'),
    '산리오': os.path.join(BASE_DIR, 'data', 'raw', 'sanrio_raw.csv')
}
SENTIMENT_DATA_PATHS = {
    '가나디': os.path.join(BASE_DIR, 'data', 'sentiment', 'ganadi_sentiment.csv'),
    '귀멸의 칼날': os.path.join(BASE_DIR, 'data', 'sentiment', 'kimetsu_sentiment.csv'),
    'K팝 데몬 헌터스': os.path.join(BASE_DIR, 'data', 'sentiment', 'kpop_sentiment.csv'),
    '산리오': os.path.join(BASE_DIR, 'data', 'sentiment', 'sanrio_sentiment.csv')
}
CONTENT_COLUMN = '내용'
RETWEET_COLUMN = '리트윗수'
LIKE_COLUMN = '마음수'
VIEW_COLUMN = '조회수'

# --- [분석 함수 (캐시 적용)] ---
@st.cache_data
def load_all_data():
    """모든 후보의 원본 및 감성 분석 데이터를 로드하고 병합합니다."""
    all_data = {}
    for name, path in RAW_DATA_PATHS.items():
        try:
            raw_df = pd.read_csv(path)
            # 조회수 컬럼이 없는 경우를 대비하여 0으로 채움
            if VIEW_COLUMN in raw_df.columns:
                raw_df[VIEW_COLUMN] = pd.to_numeric(raw_df[VIEW_COLUMN], errors='coerce').fillna(0)
            else:
                raw_df[VIEW_COLUMN] = 0
            
            sentiment_df = pd.read_csv(SENTIMENT_DATA_PATHS[name])
            sentiment_df.rename(columns={'score': 'sentiment_score'}, inplace=True)
            
            # 인덱스를 재설정하여 안전하게 병합
            raw_df.reset_index(drop=True, inplace=True)
            sentiment_df.reset_index(drop=True, inplace=True)
            all_data[name] = pd.concat([raw_df, sentiment_df[['sentiment_score']]], axis=1)
        except FileNotFoundError as e:
            st.error(f"🚨 데이터 파일 로드 실패: '{e.filename}' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
            return None
        except Exception as e:
            st.error(f"🚨 '{name}' 데이터 처리 중 오류 발생: {e}")
            return None
    return all_data

def api_call_with_retry(prompt, is_json=False, max_retries=3):
    """지수 백오프를 사용하여 API 호출을 재시도합니다."""
    for attempt in range(max_retries):
        try:
            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json" if is_json else "text/plain"
            )
            response = model.generate_content(prompt, generation_config=generation_config)
            return response.text
        except Exception as e:
            st.warning(f"API 호출 실패 (시도 {attempt + 1}/{max_retries}): {e}")
            time.sleep(2 ** attempt)
    st.error("🚨 모든 재시도 후에도 API 호출에 실패했습니다.")
    return None

@st.cache_data
def analyze_qualitative_feedback(_candidate_name, tweets_tuple):
    """LLM을 사용하여 정성적인 피드백(토픽, 리스크)을 분석합니다."""
    tweets = list(tweets_tuple)
    # 분석할 트윗 샘플 수 조정
    sample_tweets = [str(tweet) for tweet in tweets if pd.notna(tweet)][:70]
    tweet_text = "\n".join(f"- {tweet}" for tweet in sample_tweets)

    prompt = f"""당신은 K-콘텐츠 및 서브컬처 분야의 전문 SNS 데이터 분석가입니다. '{_candidate_name}'에 대한 소셜 미디어 게시글 목록을 분석하여 다음 요청사항을 JSON 형식으로 반환해주세요.

[게시글 목록]
{tweet_text}

[분석 요청]
1.  **핵심 토픽 분석**: 게시글에서 가장 빈번하게 논의되는 핵심 주제 2-3개를 추출해주세요. 각 주제별로 긍정적 반응과 부정적 반응을 구체적인 의견을 바탕으로 각각 한 문장으로 요약해주세요.
2.  **잠재 리스크 식별**: 협업 시 논란이 될 수 있는 사회적 이슈, 팬덤 내 갈등, 부정적 이미지 등 잠재적 리스크를 종합적으로 판단하여 명확하게 명시해주세요. 리스크가 없다면 '없음'으로 표기하세요.

[출력 형식]
반드시 아래의 JSON 형식으로만 응답해주세요. 다른 설명은 절대 포함하지 마세요.
{{
  "topic_analysis": [
    {{"topic": "주제 1", "positive_summary": "긍정적 반응 요약.", "negative_summary": "부정적 반응 요약."}},
    {{"topic": "주제 2", "positive_summary": "긍정적 반응 요약.", "negative_summary": "부정적 반응 요약."}}
  ],
  "potential_risk": "종합적인 잠재 리스크 요약. 없으면 '없음'으로 표기."
}}"""
    response_text = api_call_with_retry(prompt, is_json=True)
    if response_text:
        try:
            # 마크다운 코드 블록(` ```json ... ``` `) 제거
            json_str = re.search(r'\{.*\}', response_text, re.DOTALL).group(0)
            return json.loads(json_str)
        except (AttributeError, json.JSONDecodeError) as e:
            st.error(f"🚨 '{_candidate_name}'의 정성 분석 JSON 파싱 실패: {e}\n응답 내용: {response_text}")
    return None

# 캐시 문제를 해결하기 위해 @st.cache_data 데코레이터를 제거합니다.
# 이제 함수는 호출될 때마다 항상 실행되어 최신 코멘트를 생성합니다.
def generate_marketer_comment(_final_data_str):
    """
    LLM을 사용하여 마케터의 전략적 코멘트를 생성합니다.
    """
    data = json.loads(_final_data_str)
    formatted_topics = ""
    if data.get('topic_analysis'):
        for topic in data['topic_analysis']:
            formatted_topics += f"  - 토픽: {topic.get('topic', 'N/A')}\\n"
            formatted_topics += f"    - 긍정: {topic.get('positive_summary', 'N/A')}\\n"
            formatted_topics += f"    - 부정: {topic.get('negative_summary', 'N/A')}\\n"
    
    prompt = f"""당신은 데이터 기반 의사결정을 내리는 편의점 업계의 수석 마케팅 전략가입니다. '{data['candidate']}' IP에 대한 아래 분석 데이터를 보고, 콜라보레이션 진행에 대한 최종 의사결정 코멘트를 JSON 형식으로 작성해주세요.

[분석 데이터]
- 최종 관심도 지수: {data.get('interest_index', 0):.2f}점
- 참여도 점수 (화제성): {data.get('engagement_score_normalized', 0):.2f}점
- 평균 감성 점수 (호감도): {data.get('sentiment_score_normalized', 0):.2f}점
- 주요 토픽 및 여론:\n{formatted_topics}
- 잠재 리스크: {data.get('potential_risk', '없음')}

[요청사항]
1. 각 항목을 명확하고 실행 중심으로 작성하여, 아래 키를 포함하는 JSON 객체로 답변해주세요.
2. JSON 값에는 실제 분석 내용만 포함하고, 예시나 대괄호(`[]`), 하이픈(`--`) 같은 불필요한 기호는 절대 넣지 마세요.

[JSON 출력 형식]
{{
"total_evaluation": "종합적인 평가와 추천 여부를 한두 문장으로 요약",
"strengths": "데이터 기반 강점 2가지 이상 분석",
"considerations": "의사결정 전 반드시 고려해야 할 사항 분석",
"strategy_suggestion": "구체적인 마케팅 전략 제언"
}}"""
    response_text = api_call_with_retry(prompt, is_json=True)
    if response_text:
        try:
            return json.loads(response_text)
        except (AttributeError, json.JSONDecodeError) as e:
            st.error(f"🚨 마케팅 코멘트 JSON 파싱 실패: {e}\n응답 내용: {response_text}")
    return None

# =======================================================================
# 🎨 [Streamlit UI 및 실행 로직] 🎨
# =======================================================================

# --- 세션 상태 초기화 ---
if 'view' not in st.session_state:
    st.session_state['view'] = 'welcome'
if 'results' not in st.session_state:
    st.session_state['results'] = None

# --- [1/3] 시작 화면 ---
def welcome_page():
    st.title("콜라보 후보 분석")
    st.markdown('<p class="welcome-subtitle">데이터 기반 의사결정으로 최적의 파트너를 찾아보세요</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True, height=300):
            st.subheader("⚙️ 분석 가중치 조정")
            w_engagement = st.slider(
                "가중치 조절", 
                min_value=0.0, max_value=1.0, value=0.5, step=0.1, key='w_engagement_slider',
                label_visibility="collapsed"
            )
            w_sentiment = 1.0 - w_engagement
            
            w_col1, w_col2 = st.columns(2)
            with w_col1:
                st.metric(label="참여도 점수 가중치", value=f"{w_engagement:.1f}")
            with w_col2:
                st.metric(label="평균 감성 점수 가중치", value=f"{w_sentiment:.1f}")

    with col2:
        with st.container(border=True, height=300):
            st.subheader("👥 분석 대상 후보")
            list_html = "<ul class='candidate-list'>"
            for name in RAW_DATA_PATHS.keys():
                list_html += f"<li>{name}</li>"
            list_html += "</ul>"
            st.markdown(list_html, unsafe_allow_html=True)
            
    st.write("")
    if st.button("🚀 분석 시작하기", type="primary", use_container_width=True):
        st.session_state.w_engagement = st.session_state.w_engagement_slider
        st.session_state.w_sentiment = 1.0 - st.session_state.w_engagement_slider

        with st.spinner("🔍 모든 후보 데이터를 분석 중입니다... 잠시만 기다려주세요."):
            all_data = load_all_data()
            if all_data:
                # 1. 원시 점수 계산
                raw_scores_data = []
                for name, df in all_data.items():
                    engagement_raw = df[RETWEET_COLUMN].sum() + df[LIKE_COLUMN].sum() + df[VIEW_COLUMN].sum()
                    sentiment_raw_avg = df['sentiment_score'].mean()
                    raw_scores_data.append({
                        'candidate': name,
                        'engagement_raw': engagement_raw,
                        'sentiment_raw_avg': sentiment_raw_avg
                    })
                
                # 2. 정규화 (Min-Max Scaling)
                df_scores = pd.DataFrame(raw_scores_data)
                df_scores['engagement_score_normalized'] = (df_scores['engagement_raw'] / df_scores['engagement_raw'].max()) * 100
                
                sent_min, sent_max = df_scores['sentiment_raw_avg'].min(), df_scores['sentiment_raw_avg'].max()
                if sent_max > sent_min:
                    df_scores['sentiment_score_normalized'] = ((df_scores['sentiment_raw_avg'] - sent_min) / (sent_max - sent_min)) * 100
                else:
                    df_scores['sentiment_score_normalized'] = 100.0 # 모든 값이 같을 경우

                # 3. 최종 지수 계산
                df_scores['interest_index'] = (
                    df_scores['engagement_score_normalized'] * st.session_state.w_engagement +
                    df_scores['sentiment_score_normalized'] * st.session_state.w_sentiment
                )
                
                results = df_scores.sort_values('interest_index', ascending=False).to_dict('records')
                st.session_state['results'] = results
            else:
                st.session_state['results'] = []

        st.session_state['view'] = 'dashboard'
        st.rerun()

# --- [2/3] 대시보드 화면 ---
def dashboard_page():
    st.title("📊 후보별 종합 점수 대시보드")
    st.markdown(f"**분석 가중치:** 화제성 {st.session_state.w_engagement:.1f} : 호감도 {st.session_state.w_sentiment:.1f}")
    
    if not st.session_state.get('results'):
        st.error("분석된 결과가 없습니다. 시작 화면에서 분석을 먼저 실행해주세요.")
        if st.button("← 시작 화면으로"):
            st.session_state['view'] = 'welcome'
            st.rerun()
        return

    results = st.session_state['results']
    cols = st.columns(len(results))
    border_colors = ["#facc15", "#c0c0c0", "#cd7f32", "#64748b"]

    for i, data in enumerate(results):
        with cols[i]:
            with st.container():
                border_color = border_colors[i] if i < len(border_colors) else border_colors[-1]
                
                st.markdown(f"""
                <div class="card dashboard-rank-card" style="border-top-color: {border_color};">
                    <h3>{data['candidate']}</h3>
                    <hr style="margin: 1rem 0;">
                </div>
                """, unsafe_allow_html=True)
                st.metric("⭐ 최종 관심도 지수", f"{data['interest_index']:.1f}")
                st.metric("🚀 참여도 점수", f"{data['engagement_score_normalized']:.1f}")
                st.metric("😊 평균 감성 점수", f"{data['sentiment_score_normalized']:.1f}")
                
                if st.button("상세 분석 리포트", key=f"detail_{data['candidate']}", use_container_width=True):
                    st.session_state['selected_candidate'] = data['candidate']
                    st.session_state['view'] = 'detail'
                    st.rerun()
    
    st.write("---")

    # 후보 순위표
    st.header("🏆 후보 순위표")
    ranking_df_data = []
    for i, d in enumerate(results):
        ranking_df_data.append({
            "순위": f"{i + 1}위",
            "후보": d['candidate'],
            "최종 관심도 지수": f"{d['interest_index']:.2f}",
            "참여도 점수 (화제성)": f"{d['engagement_score_normalized']:.2f}",
            "평균 감성 점수 (호감도)": f"{d['sentiment_score_normalized']:.2f}"
        })
    ranking_df = pd.DataFrame(ranking_df_data)
    st.dataframe(ranking_df, use_container_width=True, hide_index=True)


    # 순위 시각화 차트
    st.header("📈 후보별 점수 기여도 비교 그래프")
    df_results = pd.DataFrame(results)

    # 누적 막대 그래프를 위한 데이터 가공
    df_results['참여도 점수 기여도'] = df_results['engagement_score_normalized'] * st.session_state.w_engagement
    df_results['평균 감성 점수 기여도'] = df_results['sentiment_score_normalized'] * st.session_state.w_sentiment
    
    df_melted = df_results.melt(
        id_vars=['candidate', 'interest_index'],
        value_vars=['참여도 점수 기여도', '평균 감성 점수 기여도'],
        var_name='점수 종류',
        value_name='기여도'
    )

    chart = alt.Chart(df_melted).mark_bar().encode(
        x=alt.X('기여도:Q', title='최종 관심도 지수', stack='zero', axis=alt.Axis(grid=False)),
        y=alt.Y('candidate:N', title='후보', sort='-x'),
        color=alt.Color('점수 종류:N',
            legend=alt.Legend(title="점수 구성 요소"),
            scale=alt.Scale(
                domain=['참여도 점수 기여도', '평균 감성 점수 기여도'],
                range=['#94a3b8', '#fca5a5'] # Slate-400, Red-300
            )
        ),
        tooltip=[
            alt.Tooltip('candidate', title='후보'),
            alt.Tooltip('점수 종류', title='점수 종류'),
            alt.Tooltip('기여도:Q', title='기여 점수', format='.1f')
        ]
    ).properties(
        height=300
    )
    st.altair_chart(chart, use_container_width=True)


    if st.button("← 가중치 재설정하기"):
        with st.spinner("시작 화면으로 돌아가는 중..."):
            time.sleep(0.5)
            st.session_state['view'] = 'welcome'
            st.rerun()

# --- [3/3] 상세 리포트 화면 ---
def detail_page():
    selected_name = st.session_state.get('selected_candidate')
    if not selected_name:
        st.error("선택된 후보가 없습니다.")
        st.session_state['view'] = 'dashboard'
        st.rerun()

    st.markdown(f"""
    <div class="report-title-card">
        <h2>🔍 {selected_name} 상세 분석 리포트</h2>
    </div>
    """, unsafe_allow_html=True)
    
    detail_data = next((item for item in st.session_state['results'] if item['candidate'] == selected_name), None)
    
    # 상세 데이터가 없는 경우, 에러 메시지를 표시하고 나머지 UI는 표시하지 않습니다.
    if not detail_data:
        st.error("상세 데이터를 불러올 수 없습니다.")
    else:
        # 상세 데이터가 있는 경우에만 리포트 내용을 표시합니다.
        with st.spinner("로딩 중입니다..."):
            all_data = load_all_data()
            if all_data and (candidate_df := all_data.get(selected_name)) is not None:
                tweets_tuple = tuple(candidate_df[CONTENT_COLUMN].dropna().tolist())
                qualitative_result = analyze_qualitative_feedback(selected_name, tweets_tuple)
                
                if qualitative_result:
                    detail_data.update(qualitative_result)
                    final_data_str = json.dumps(detail_data, ensure_ascii=False)
                    comment_dict = generate_marketer_comment(final_data_str)
                else:
                    comment_dict = None
            else:
                st.error("데이터 로딩에 실패하여 심층 분석을 진행할 수 없습니다.")
                comment_dict = None

        # 정량 분석 결과
        st.subheader("🔢 정량 분석 결과")
        col1, col2, col3 = st.columns(3)
        col1.metric("⭐ 최종 관심도 지수", f"{detail_data.get('interest_index', 0):.2f}", help="가중치가 적용된 종합 점수입니다.")
        col2.metric("🚀 참여도 점수", f"{detail_data.get('engagement_score_normalized', 0):.2f}", help="리트윗, 좋아요, 조회수 기반의 화제성 점수입니다.")
        col3.metric("😊 평균 감성 점수", f"{detail_data.get('sentiment_score_normalized', 0):.2f}", help="게시글의 긍/부정 기반의 호감도 점수입니다.")
        
        st.write("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🗣️ 주요 토픽 분석")
            if topics := detail_data.get('topic_analysis'):
                for i, topic in enumerate(topics):
                    st.markdown(f"""
                    <div class="insight-card">
                        <h5><i class="fa-solid fa-comments"></i> <strong>주요 토픽 #{i+1}:</strong> {topic.get('topic', 'N/A')}</h5>
                        <p><i class="fa-solid fa-circle-check" style="color: #22c55e;"></i> <strong>긍정:</strong> {topic.get('positive_summary', '요약 없음')}</p>
                        <p><i class="fa-solid fa-circle-xmark" style="color: #ef4444;"></i> <strong>부정:</strong> {topic.get('negative_summary', '요약 없음')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("분석된 주요 토픽이 없습니다.")

            st.markdown(f"""
            <div class="insight-card" style="border-color: #f97316;">
                <h5><i class="fa-solid fa-triangle-exclamation"></i> 잠재 리스크 분석</h5>
                <p>{detail_data.get('potential_risk', '분석된 리스크 정보가 없습니다.')}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.subheader("💡 전략 코멘트")
            if comment_dict:
                insight_items = {
                    "total_evaluation": {"icon": "fa-magnifying-glass-chart", "title": "총평", "color": "#6366f1"},
                    "strengths": {"icon": "fa-thumbs-up", "title": "핵심 강점", "color": "#22c55e"},
                    "considerations": {"icon": "fa-clipboard-check", "title": "고려사항", "color": "#f59e0b"},
                    "strategy_suggestion": {"icon": "fa-lightbulb", "title": "전략 제언", "color": "#475569"},
                }
                for key, value in insight_items.items():
                    st.markdown(f"""
                    <div class="insight-card" style="border-color: {value['color']};">
                        <h5><i class="fa-solid {value['icon']}"></i> {value['title']}</h5>
                        <p>{comment_dict.get(key, '코멘트 생성에 실패했습니다.')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error("코멘트를 생성하지 못했습니다.")
    
    if st.button("← 대시보드로 돌아가기", key="detail_back"):
        st.session_state['view'] = 'dashboard'
        st.rerun()


# --- 페이지 라우팅 ---
if st.session_state['view'] == 'welcome':
    welcome_page()
elif st.session_state['view'] == 'dashboard':
    dashboard_page()
elif st.session_state['view'] == 'detail':
    detail_page()