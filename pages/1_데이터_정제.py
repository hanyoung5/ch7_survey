import re
import pandas as pd
import streamlit as st

# 사이드바가 항상 열린 상태로 시작되도록 설정
st.set_page_config(
    page_title="데이터 정제",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -------------------------------------------------------------
# 헬퍼 함수 정의
# -------------------------------------------------------------
def standardize_grade(val):
    """학년 표기를 숫자(1, 2, 3, 4 등)로 통일"""
    if pd.isna(val):
        return val
    s = str(val).strip()
    korean_map = {"일": 1, "이": 2, "삼": 3, "사": 4, "오": 5, "육": 6}
    for k, num in korean_map.items():
        if k in s:
            return num
    found = re.findall(r"\d+", s)
    return int(found[0]) if found else s


def standardize_college(val):
    """단과대학 분류 규칙 적용"""
    if pd.isna(val):
        return "기타"
    s = str(val).strip()
    if "인문" in s:
        return "인문대학"
    elif "사과" in s or "사회" in s:
        return "사회과학대학"
    elif "경통" in s or "경제" in s:
        return "경제통상대학"
    elif "경영" in s:
        return "경영대학"
    elif "사범" in s:
        return "사범대학"
    return "기타"


def parse_time_to_minutes(val):
    """'1시간 30분', '90분', '2시간' 등 자연어 표현을 분 단위 정수로 변환"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    try:
        return float(s)
    except ValueError:
        pass

    hours, minutes = 0, 0
    h_match = re.search(r"(\d+)\s*시간", s)
    m_match = re.search(r"(\d+)\s*분", s)

    if h_match:
        hours = int(h_match.group(1))
    if m_match:
        minutes = int(m_match.group(1))

    if not h_match and not m_match:
        found = re.findall(r"\d+", s)
        return int(found[0]) if found else None

    return hours * 60 + minutes


# -------------------------------------------------------------
# 사이드바 컨트롤 구성
# -------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 정제 옵션 설정")

    ai_time_range = st.slider(
        "AI 사용 시간 허용범위 (분 단위)",
        min_value=0,
        max_value=720,
        value=(0, 300),
        step=10,
        help="선택한 분 범위에 속하지 않는 데이터는 이상치로 판단하여 제거합니다."
    )

    missing_option = st.radio(
        "결측치(빈칸) 처리 방식",
        options=["그대로 두기", "행 삭제"],
        help="'행 삭제' 선택 시 하나라도 빈칸이 있는 행을 완전히 제거합니다."
    )

# -------------------------------------------------------------
# 메인 화면
# -------------------------------------------------------------
st.title("🧹 설문 데이터 정제 (Data Cleansing)")

uploaded_file = st.file_uploader(
    "구글 설문지 CSV 파일(survey_raw.csv)을 업로드하세요",
    type=["csv"]
)

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)
    st.session_state["raw_df"] = raw_df

    # 원본 데이터 현황 표시
    st.subheader("📋 전체 원본 데이터")
    st.info(f"설문 응답자 수: **{len(raw_df):,}명** | 전체 열 개수: **{len(raw_df.columns)}개**")
    st.dataframe(raw_df, use_container_width=True)

    # ---------------------------------------------------------
    # 정제 파이프라인 (원본 보존 후 복사본 처리)
    # ---------------------------------------------------------
    clean_df = raw_df.copy()
    step_logs = []

    # 1. 열 제목 표준화
    standard_cols = ["타임스탬프", "성별", "학년", "소속단과대학", "AI사용시간",
                     "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "서술형"]
    if len(clean_df.columns) == len(standard_cols):
        clean_df.columns = standard_cols
    else:
        rename_dict = {orig: standard_cols[i] for i, orig in enumerate(clean_df.columns[:len(standard_cols)])}
        clean_df = clean_df.rename(columns=rename_dict)
    step_logs.append({"단계": "1. 열 제목 축소", "내용": "타임스탬프, 성별, 학년, 소속단과대학, AI사용시간, Q1~Q6, 서술형으로 변경"})

    # 2. 중복 제거 (타임스탬프 제외 모든 열 기준)
    before_dup = len(clean_df)
    cols_except_ts = [col for col in clean_df.columns if col != "타임스탬프"]
    clean_df = clean_df.drop_duplicates(subset=cols_except_ts, keep="first")
    dup_removed = before_dup - len(clean_df)
    step_logs.append({"단계": "2. 중복 행 제거", "내용": f"타임스탬프 제외 동일 응답 {dup_removed}건 제거"})

    # 3. 학년 표기 통일
    if "학년" in clean_df.columns:
        clean_df["학년"] = clean_df["학년"].apply(standardize_grade)
        step_logs.append({"단계": "3. 학년 표준화", "내용": "숫자 형식(1, 2, 3...)으로 통일"})

    # 4. 단과대학 분류
    if "소속단과대학" in clean_df.columns:
        clean_df["소속단과대학"] = clean_df["소속단과대학"].apply(standardize_college)
        step_logs.append({"단계": "4. 단과대학 분류", "내용": "인문/사회과학/경제통상/경영/사범대학 및 기타로 분류"})

    # 5. 이상치 처리 (AI사용시간)
    if "AI사용시간" in clean_df.columns:
        clean_df["AI사용시간"] = clean_df["AI사용시간"].apply(parse_time_to_minutes)
        before_outlier = len(clean_df)
        min_time, max_time = ai_time_range
        clean_df = clean_df[
            clean_df["AI사용시간"].isna() |
            ((clean_df["AI사용시간"] >= min_time) & (clean_df["AI사용시간"] <= max_time))
            ]
        outliers_removed = before_outlier - len(clean_df)
        step_logs.append({"단계": "5. 이상치 필터링", "내용": f"AI사용시간 {min_time}분~{max_time}분 범위 외 {outliers_removed}건 제거"})

    # 6. 결측치 처리
    missing_counts = clean_df.isna().sum().to_dict()
    missing_summary = ", ".join([f"{k}: {v}건" for k, v in missing_counts.items() if v > 0]) or "결측치 없음"

    if missing_option == "행 삭제":
        before_na = len(clean_df)
        clean_df = clean_df.dropna()
        na_removed = before_na - len(clean_df)
        step_logs.append({"단계": "6. 결측치 처리", "내용": f"행 삭제 적용 ({na_removed}건 제거, 빈칸 현황: {missing_summary})"})
    else:
        step_logs.append({"단계": "6. 결측치 처리", "내용": f"그대로 두기 유지 (빈칸 현황: {missing_summary})"})

    # 7. 점수 계산 (Q6R = 6 - Q6)
    if "Q6" in clean_df.columns:
        clean_df["Q6"] = pd.to_numeric(clean_df["Q6"], errors="coerce")
        clean_df["Q6R"] = 6 - clean_df["Q6"]
        step_logs.append({"단계": "7. 역코딩 점수 계산", "내용": "Q6R = 6 - Q6 계산 열 추가"})

    # 세션 상태 저장
    st.session_state["clean_df"] = clean_df

    # ---------------------------------------------------------
    # 정제 결과 지표 카드 및 표 출력
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📊 정제 결과 요약")

    card1, card2, card3, card4 = st.columns(4)
    with card1:
        st.metric("원본 응답 수", f"{len(raw_df):,}명")
    with card2:
        st.metric("최종 정제 데이터 수", f"{len(clean_df):,}명", delta=f"{len(clean_df) - len(raw_df)}명")
    with card3:
        st.metric("중복 제거 건수", f"{dup_removed}건")
    with card4:
        st.metric("허용 AI 시간 범위", f"{ai_time_range[0]}~{ai_time_range[1]}분")

    # 정제 기록 표
    with st.expander("📝 단계별 정제 수행 내역 보기", expanded=True):
        st.table(pd.DataFrame(step_logs))

    # 정제된 데이터 테이블
    st.subheader("✨ 정제 완료 데이터 (Cleaned Data)")
    st.dataframe(clean_df, use_container_width=True)

    # CSV 다운로드
    csv_bytes = clean_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 정제된 데이터 CSV 내려받기",
        data=csv_bytes,
        file_name="survey_cleaned.csv",
        mime="text/csv",
        type="primary"
    )

else:
    st.warning("분석을 시작하려면 먼저 구글 설문 CSV 파일을 업로드해 주세요.")