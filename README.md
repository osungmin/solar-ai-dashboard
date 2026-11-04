# 우리 지역 태양광 AI 예측 대시보드

2025년 전남에서 학습한 Random Forest 모델을 전남·대전에 적용한 교육용 앱입니다.

## 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

지도에서 전남·대전 점을 선택하거나 선택 메뉴로 전환할 수 있습니다.
예측 방식 A(발전량 직접)와 B(CF 기반)를 전환하고 10~12월 실제값을 공개할 수 있습니다.

## GitHub 및 배포
`app.py`, `requirements.txt`, `data/`만 GitHub 저장소에 올려도 실행 가능합니다.
[Streamlit Community Cloud](https://share.streamlit.io/)에서 저장소를 연결하고 `app.py`를 지정하세요.
원본 KMA/KPX/EPSIS CSV와 모델 학습 스크립트는 배포에 필요하지 않습니다.

## 해석 주의
- 1~9월은 전남 모델 학습기간, 10~12월은 미학습 검증기간입니다.
- 검증기간의 기상 입력은 **실제 관측값**입니다. 따라서 예측 곡선은 미래 예보가 아닌 사후 추정(hindcast)입니다.
- 앱의 1~9월은 관측 발전량만 표시합니다.
- 지역별 CF는 KPX 거래량과 EPSIS 정회원 설비용량의 집계 범위가 맞는지 추가 검증이 필요합니다.
- 데이터는 실제 공개자료에서 생성한 2025년 시계열이며, 지도 점은 대표 위치입니다.
