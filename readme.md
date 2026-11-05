# 구글 설문지 데이터 정제 및 EDA 시각화 플랫폼

구글 설문지(Google Forms)로 수집된 로우 데이터(`survey_raw.csv`)를 체계적으로 전처리하고, 정제된 데이터를 기반으로 기술통계 분석 및 시각화를 제공하는 Streamlit 멀티페이지 웹 애플리케이션입니다.

---

## 1. 프로젝트 폴더 구조

Streamlit의 멀티페이지 자동 인식을 위해 반드시 아래 구조를 유지해야 합니다. (`pages` 폴더명은 반드시 소문자 복수형이어야 합니다.)

```text
my_survey_app/
├── Home.py                  # 진입점 및 홈 화면
├── pages/
│   ├── 1_데이터_정제.py      # 설문 데이터 전처리 파이프라인
│   └── 2_그래프_분석.py      # 기술통계 및 Streamlit 기본 차트 시각화
├── survey_raw.csv           # 원본 설문 데이터 예시 (선택)
├── requirements.txt         # 의존성 패키지 목록
└── README.md                # 프로젝트 안내 문서