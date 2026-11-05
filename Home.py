import streamlit as st

# set_page_config는 앱 전체에서 오직 Home.py 최상단에 딱 1번만 실행합니다.
st.set_page_config(
    page_title="설문 데이터 분석 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "clean_df" not in st.session_state:
    st.session_state["clean_df"] = None
if "raw_df" not in st.session_state:
    st.session_state["raw_df"] = None

st.title("📊 구글 설문지 데이터 분석 플랫폼")
st.markdown("---")

st.markdown("""
### 환영합니다!
이 앱은 구글 설문지 응답 데이터를 체계적으로 전처리하고 정제된 결과를 분석하기 위한 도구입니다.

#### 메뉴 안내
왼쪽 사이드바에 보이는 **`1_데이터_정제`**를 클릭하여 정제 작업을 진행하세요.
""")

st.info("👈 왼쪽 사이드바에서 **1_데이터_정제**를 선택해주세요.")