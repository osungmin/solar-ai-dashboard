"""태양광 발전량 예측 지도: 2025년 전남·대전 교육용 대시보드."""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="우리 지역 태양광 AI", page_icon="☀️", layout="wide")
ROOT = Path(__file__).resolve().parent
REGIONS = {"전남": {"code": "JN", "lat": 34.82, "lon": 126.46},
           "대전": {"code": "DJ", "lat": 36.35, "lon": 127.38}}
CUTOFF = pd.Timestamp("2025-10-01")

@st.cache_data
def load_data(code):
    return pd.read_csv(ROOT / "data" / f"{code}.csv", parse_dates=["datetime"])

if "region" not in st.session_state:
    st.session_state.region = "전남"

st.title("우리 지역 태양광 발전량, AI로 맞혀볼까?")
st.caption("KPX 발전량 · EPSIS 설비용량 · KMA 관측 기상자료 | 2025년 전남 학습 → 대전 적용")

left, right = st.columns([1, 2.4], gap="large")
with left:
    st.subheader("지역 선택")
    st.selectbox("지역", list(REGIONS), key="region")
    # 클릭 가능한 지도 점. 선택 이벤트가 지원되지 않는 환경에서도 위 선택상자로 조작 가능.
    import plotly.express as px
    pts = pd.DataFrame([{"지역": k, "lat": v["lat"], "lon": v["lon"]} for k,v in REGIONS.items()])
    fig_map = px.scatter_map(pts, lat="lat", lon="lon", hover_name="지역",
                             text="지역", zoom=5.5, height=320,
                             center={"lat": 35.65, "lon": 127.0})
    fig_map.update_traces(marker={"size": 19, "color": "#E9A23B"}, textposition="top center")
    fig_map.update_layout(map_style="open-street-map", margin=dict(l=0,r=0,t=0,b=0),
                          showlegend=False)
    event = st.plotly_chart(fig_map, use_container_width=True, key="region_map",
                            on_select="rerun", selection_mode="points")
    selected_points = event.selection.points if event is not None else []
    if selected_points:
        idx = selected_points[0].get("point_index")
        if idx is not None and 0 <= idx < len(pts):
            clicked = pts.iloc[idx]["지역"]
            if clicked != st.session_state.region:
                st.session_state.region = clicked
                st.rerun()
    st.info("지도 점을 클릭하거나 위 메뉴에서 지역을 선택하세요.")
    st.caption("지도 점은 지역 대표 위치이며 발전소 위치가 아닙니다.")

with right:
    region = st.session_state.region
    df = load_data(REGIONS[region]["code"])
    st.subheader(f"{region} 태양광 발전량")
    model = st.radio("예측 방식", ["A · 발전량 직접 예측", "B · CF 기반 예측"],
                     index=1, horizontal=True)
    pred_col = "pred_A" if model.startswith("A") else "pred_B"
    scale = st.radio("시간 단위", ["일별", "시간별", "월별"], horizontal=True)
    reveal = st.toggle("10~12월 실제값 공개 (정답 확인)", value=False)
    st.caption("1~9월: 전남 모델 학습기간 | 10~12월: 미학습 검증기간")
    st.caption("10~12월의 모델 추정치는 실제 관측 기상자료를 입력한 사후 추정 결과입니다.")

    series = df.set_index("datetime")
    freq = {"시간별": "h", "일별": "D", "월별": "MS"}[scale]
    # 시간별 MWh를 기간별 총 발전량 MWh로 합산.
    actual = series["amount_MWh"].resample(freq).sum(min_count=1)
    predicted = series[pred_col].resample(freq).sum(min_count=1)
    hist = actual.loc[actual.index < CUTOFF]
    forecast = predicted.loc[predicted.index >= CUTOFF]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist, name="실제 발전량 (1~9월)",
                             mode="lines", line=dict(color="#2563eb", width=1.5)))
    fig.add_trace(go.Scatter(x=forecast.index, y=forecast,
                             name="모델 추정 (10~12월)", mode="lines",
                             line=dict(color="#ea580c", width=1.6, dash="dash")))
    if reveal:
        held = actual.loc[actual.index >= CUTOFF]
        fig.add_trace(go.Scatter(x=held.index, y=held, name="검증기간 실제값",
                                 mode="lines", line=dict(color="#0f766e", width=1.4)))
    fig.add_vline(x=CUTOFF.timestamp() * 1000, line_dash="dot", line_color="gray")
    fig.update_layout(height=420, margin=dict(l=5,r=5,t=20,b=5),
                      xaxis_title="2025년", yaxis_title="발전량 (MWh / 선택 기간)",
                      legend=dict(orientation="h", y=1.15), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    q4 = df.loc[df.datetime >= CUTOFF].copy()
    if reveal:
        from sklearn.metrics import mean_absolute_error, r2_score
        valid = q4[pred_col].notna()
        mae = mean_absolute_error(q4.loc[valid, "amount_MWh"], q4.loc[valid, pred_col])
        r2 = r2_score(q4.loc[valid, "amount_MWh"], q4.loc[valid, pred_col])
        a, b = st.columns(2)
        a.metric("10~12월 시간별 MAE", f"{mae:,.2f} MWh")
        b.metric("10~12월 시간별 R²", f"{r2:,.3f}")
        st.caption("평가지표는 시간별 자료 기준이며, 일별·월별 그래프 선택과 무관합니다.")
    else:
        st.info("정답 공개 스위치를 켜면 10~12월 실제 발전량과 모델 성능을 확인할 수 있습니다.")

st.divider()
st.subheader("왜 전남 모델을 대전에 그대로 적용하면 안 될까?")
st.write("발전량 직접 예측 모델은 전남의 큰 설비 규모를 학습합니다. "
         "대전은 설비 규모가 달라 직접 전이가 어려울 수 있습니다. "
         "CF(설비이용률)를 예측한 뒤 해당 지역 설비용량을 곱하면 규모 차이를 반영할 수 있습니다.")
st.latex(r"\mathrm{CF} = \frac{\mathrm{1시간\ 발전량\ (MWh)}}{\mathrm{설비용량\ (MW)}\times 1\mathrm{h}}")
st.warning("교육용 모델입니다. 관측 기상자료를 사용한 사후 추정이며 미래 예보가 아닙니다. "
           "KPX 거래량과 EPSIS 정회원 설비용량의 집계 범위 일치 여부도 별도 검증이 필요합니다.")
st.caption("자료: 한국전력거래소(KPX), 전력통계정보시스템(EPSIS), 기상청 ASOS. "
           "2025년 전남 1~9월 Random Forest 학습, 전남·대전 10~12월 평가.")
