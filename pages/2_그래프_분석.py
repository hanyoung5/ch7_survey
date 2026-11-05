# pages/2_그래프_분석.py
# 설문 응답 정제 데이터에 대한 요약 지표 산출 및 시각화 분석 모듈

import pandas as pd
import streamlit as st


class SurveyVisualizer:
    """설문 데이터의 기술통계 계산 및 Streamlit 기본 차트 시각화를 전담하는 클래스"""

    def __init__(self, clean_df: pd.DataFrame, raw_df: pd.DataFrame | None = None):
        self.clean_df = clean_df.copy()
        self.raw_df = raw_df.copy() if raw_df is not None else None

        # 윤리의식 관련 문항 탐색 (Q1 ~ Q5 및 Q6R 또는 Q6)
        self.ethics_cols = [f"Q{i}" for i in range(1, 6) if f"Q{i}" in self.clean_df.columns]
        if "Q6R" in self.clean_df.columns:
            self.ethics_cols.append("Q6R")
        elif "Q6" in self.clean_df.columns:
            self.ethics_cols.append("Q6")

    @staticmethod
    def _find_college_col(df: pd.DataFrame) -> str | None:
        """단과대학 관련 열 이름을 탐색합니다."""
        if "소속단과대학" in df.columns:
            return "소속단과대학"
        for col in df.columns:
            if "대학" in col or "소속" in col:
                return col
        if len(df.columns) > 3:
            return df.columns[3]
        return None

    def calculate_summary_metrics(self) -> dict:
        """유효 응답 수, 평균 AI 사용 시간, AI 윤리의식 평균을 계산합니다."""
        valid_count = len(self.clean_df)

        avg_ai_time = 0.0
        if "AI사용시간" in self.clean_df.columns:
            time_series = pd.to_numeric(self.clean_df["AI사용시간"], errors="coerce").dropna()
            if not time_series.empty:
                avg_ai_time = float(time_series.mean())

        avg_ethics = 0.0
        if self.ethics_cols:
            ethics_df = self.clean_df[self.ethics_cols].apply(pd.to_numeric, errors="coerce")
            mean_val = ethics_df.mean().mean()
            if not pd.isna(mean_val):
                avg_ethics = float(mean_val)

        return {
            "valid_count": valid_count,
            "avg_ai_time": round(avg_ai_time, 2),
            "avg_ethics": round(avg_ethics, 2),
        }

    def get_college_counts(self, df: pd.DataFrame) -> pd.DataFrame:
        """단과대학별 응답자 수를 인덱스 기반 데이터프레임으로 산출합니다."""
        col = self._find_college_col(df)
        if not col or col not in df.columns:
            return pd.DataFrame(columns=["응답자수"])

        series = df[col].fillna("기타").astype(str).value_counts()
        result = series.to_frame(name="응답자수")
        result.index.name = "단과대학"
        return result

    def get_demographics(self, column_name: str) -> pd.DataFrame:
        """인구통계 빈도를 인덱스 기반 데이터프레임으로 산출합니다."""
        if column_name not in self.clean_df.columns:
            return pd.DataFrame(columns=["응답자수"])

        series = self.clean_df[column_name].dropna().astype(str).value_counts()
        result = series.to_frame(name="응답자수")
        result.index.name = column_name
        return result

    def get_question_averages(self) -> pd.DataFrame:
        """문항별 평균 점수를 집계합니다."""
        if not self.ethics_cols:
            return pd.DataFrame(columns=["평균점수"])

        numeric_scores = self.clean_df[self.ethics_cols].apply(pd.to_numeric, errors="coerce")
        means = numeric_scores.mean().round(2).to_frame(name="평균점수")
        means.index.name = "문항"
        return means

    def get_group_statistics(self, group_col: str) -> pd.DataFrame:
        """집단(학년, 단과대학)별 윤리의식 평균과 인원 수를 집계합니다."""
        actual_col = group_col if group_col in self.clean_df.columns else self._find_college_col(self.clean_df)
        if not actual_col or actual_col not in self.clean_df.columns or not self.ethics_cols:
            return pd.DataFrame(columns=["인원수", "평균점수"])

        temp_df = self.clean_df[[actual_col] + self.ethics_cols].copy()
        for c in self.ethics_cols:
            temp_df[c] = pd.to_numeric(temp_df[c], errors="coerce")

        temp_df["윤리의식_평균"] = temp_df[self.ethics_cols].mean(axis=1)

        grouped = (
            temp_df.groupby(actual_col)
            .agg(인원수=("윤리의식_평균", "count"), 평균점수=("윤리의식_평균", "mean"))
        )
        grouped["평균점수"] = grouped["평균점수"].round(2)
        grouped.index.name = group_col
        return grouped

    def get_scatter_data(self) -> pd.DataFrame:
        """AI 사용 시간과 윤리의식 총평균 점수를 결합한 데이터를 반환합니다."""
        if "AI사용시간" not in self.clean_df.columns or not self.ethics_cols:
            return pd.DataFrame()

        temp_df = self.clean_df[["AI사용시간"] + self.ethics_cols].copy()
        temp_df["AI사용시간"] = pd.to_numeric(temp_df["AI사용시간"], errors="coerce")

        for c in self.ethics_cols:
            temp_df[c] = pd.to_numeric(temp_df[c], errors="coerce")

        temp_df["AI윤리의식_평균"] = temp_df[self.ethics_cols].mean(axis=1).round(2)
        clean_scatter = temp_df[["AI사용시간", "AI윤리의식_평균"]].dropna()
        return clean_scatter


def render_robust_bar_chart(df: pd.DataFrame, value_col: str) -> None:
    """모든 Streamlit 버전에서 오류 없이 가로 막대 또는 기본 막대 차트를 안전하게 표시합니다."""
    if df.empty:
        st.write("표시할 데이터가 없습니다.")
        return

    # 1. 인덱스를 컬럼으로 변환하여 horizontal 시도
    flat_df = df.reset_index()
    label_col = flat_df.columns[0]

    try:
        # 최신 Streamlit (v1.35 이상) horizontal=True 가로막대 지원
        st.bar_chart(data=flat_df, x=value_col, y=label_col, horizontal=True)
    except Exception:
        # 구버전이거나 매핑 에러 시 인덱스 기반 기본 막대차트로 안전 대체
        st.bar_chart(df[[value_col]])


def render_robust_scatter_chart(df: pd.DataFrame, x_col: str, y_col: str) -> None:
    """Streamlit 내장 산점도를 버전 차이에 구애받지 않고 안전하게 표시합니다."""
    if df.empty:
        st.write("유효한 수치 데이터가 없습니다.")
        return

    try:
        st.scatter_chart(data=df, x=x_col, y=y_col)
    except Exception:
        # 구버전 환경에서 scatter_chart 함수가 없을 경우
        st.line_chart(data=df.set_index(x_col)[[y_col]])


def load_dataset() -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """사이드바 구성 및 데이터 세션/업로드 로드를 처리합니다."""
    with st.sidebar:
        st.header("데이터 관리 및 옵션")

        clean_df = st.session_state.get("clean_df", None)
        raw_df = st.session_state.get("raw_df", None)

        if clean_df is not None:
            st.success(f"정제 데이터 로드 완료 ({len(clean_df):,}건)")
        else:
            st.warning("세션에 정제 데이터가 없습니다.")

        st.subheader("정제 데이터 업로드")
        uploaded_file = st.file_uploader(
            "CSV 파일 선택",
            type=["csv"],
            key="sidebar_csv_uploader",
            help="1_데이터_정제 페이지를 거치지 않고 직접 업로드할 경우 사용합니다."
        )
        if uploaded_file is not None:
            try:
                clean_df = pd.read_csv(uploaded_file)
                st.session_state["clean_df"] = clean_df
                st.success(f"업로드 완료 ({len(clean_df):,}건)")
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

        st.markdown("---")
        st.subheader("안내")
        st.markdown(
            "- 한글 항목은 가로 막대 차트로 표시됩니다.\n"
            "- 정제 전 원본 데이터가 세션에 있으면 전후 비교가 나란히 제공됩니다."
        )

    return clean_df, raw_df


def render_summary_section(visualizer: SurveyVisualizer) -> None:
    """1. 요약 지표 영역"""
    st.subheader("1. 주요 요약 지표")
    metrics = visualizer.calculate_summary_metrics()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="유효 응답", value=f"{metrics['valid_count']:,} 명")
    with col2:
        st.metric(label="평균 AI 사용 시간", value=f"{metrics['avg_ai_time']} 분")
    with col3:
        st.metric(label="AI 윤리의식 평균", value=f"{metrics['avg_ethics']} 점 / 5.0")
    st.markdown("---")


def render_comparison_section(visualizer: SurveyVisualizer) -> None:
    """2. 정제 전후 단과대학별 응답자 수 가로 막대 비교"""
    st.subheader("2. 정제 전후 단과대학별 응답자 수 비교")

    clean_counts = visualizer.get_college_counts(visualizer.clean_df)

    if visualizer.raw_df is None:
        st.info("정제 전 원본 데이터가 세션에 없습니다. 정제 후 단과대학별 응답자 수만 표시합니다.")
        render_robust_bar_chart(clean_counts, value_col="응답자수")
        st.markdown("---")
        return

    raw_counts = visualizer.get_college_counts(visualizer.raw_df)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**정제 전 단과대학별 응답자 수**")
        render_robust_bar_chart(raw_counts, value_col="응답자수")

    with col2:
        st.markdown("**정제 후 단과대학별 응답자 수**")
        render_robust_bar_chart(clean_counts, value_col="응답자수")

    st.markdown("---")


def render_tabs_section(visualizer: SurveyVisualizer) -> None:
    """3. 세부 4개 탭 영역"""
    st.subheader("3. 세부 데이터 분석")
    tab1, tab2, tab3, tab4 = st.tabs(["응답자 구성", "문항별 평균", "집단 비교", "사용 시간과 점수"])

    # 탭 1: 응답자 구성
    with tab1:
        st.markdown("#### 응답자 구성 현황")
        col_grade, col_gender = st.columns(2)
        with col_grade:
            st.markdown("**학년별 응답자 수**")
            grade_df = visualizer.get_demographics("학년")
            render_robust_bar_chart(grade_df, value_col="응답자수")
        with col_gender:
            st.markdown("**성별 응답자 수**")
            gender_df = visualizer.get_demographics("성별")
            render_robust_bar_chart(gender_df, value_col="응답자수")

    # 탭 2: 문항별 평균
    with tab2:
        st.markdown("#### 설문 문항별 평균 점수")
        q_means = visualizer.get_question_averages()
        render_robust_bar_chart(q_means, value_col="평균점수")
        st.dataframe(q_means.reset_index(), use_container_width=True)

    # 탭 3: 집단 비교
    with tab3:
        st.markdown("#### 집단별 평균 및 인원 수 비교")

        st.markdown("**1) 학년별 통계**")
        grade_stats = visualizer.get_group_statistics("학년")
        if not grade_stats.empty:
            render_robust_bar_chart(grade_stats[["평균점수"]], value_col="평균점수")
            st.dataframe(
                grade_stats.reset_index().rename(columns={"인원수": "인원 수 (명)", "평균점수": "평균 점수"}),
                use_container_width=True,
            )
        else:
            st.write("학년 집계 데이터가 없습니다.")

        st.markdown("**2) 단과대학별 통계**")
        college_stats = visualizer.get_group_statistics("소속단과대학")
        if not college_stats.empty:
            render_robust_bar_chart(college_stats[["평균점수"]], value_col="평균점수")
            st.dataframe(
                college_stats.reset_index().rename(columns={"인원수": "인원 수 (명)", "평균점수": "평균 점수"}),
                use_container_width=True,
            )
        else:
            st.write("단과대학 집계 데이터가 없습니다.")

    # 탭 4: 사용 시간과 점수
    with tab4:
        st.markdown("#### AI 사용 시간과 AI 윤리의식 점수 관계")
        scatter_df = visualizer.get_scatter_data()
        if not scatter_df.empty:
            render_robust_scatter_chart(scatter_df, x_col="AI사용시간", y_col="AI윤리의식_평균")
            st.dataframe(scatter_df, use_container_width=True)
        else:
            st.write("사용 시간 또는 점수 데이터가 존재하지 않습니다.")


def main() -> None:
    """메인 실행 진입점"""
    st.title("설문 데이터 시각화 및 그래프 분석")

    clean_df, raw_df = load_dataset()

    if clean_df is None:
        st.info("정제된 데이터가 없습니다. 왼쪽 사이드바에서 CSV 파일을 업로드하거나, 1_데이터_정제 페이지에서 정제를 먼저 완료하세요.")
        return

    visualizer = SurveyVisualizer(clean_df=clean_df, raw_df=raw_df)

    render_summary_section(visualizer)
    render_comparison_section(visualizer)
    render_tabs_section(visualizer)


if __name__ == "__main__":
    main()