import io
import os
import base64
from PIL import Image
import streamlit as st
from openai import OpenAI

api_key = st.secrets.openAI["api_key"]
# api_key = os.getenv("OPENAI_API_KEY")
# if not api_key:
#     raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=api_key)

st.set_page_config(page_title="1. 물체와 물질_제품 제작소", page_icon="🎨")
st.title("🎨 직접 제작한 '제품 설명'과 '스케치'로 실사화 모습을 만들어 보아요!")
contents1 = '''
📢 주의! 기회는 단... 3번뿐!! 신중히 버튼을 눌러주세요.🤓
'''

st.write(contents1)



# --- 기본(숨김) 프롬프트: 코드에만 보관 ---
BASE_PROMPT = (
    "다음 그림과 이어지는 제품 설명을 토대로, 제품의 실사화 제품 사진을 생성해줘."
    "글씨는 무시하고 절대 그림에 포함되서는 안돼."
)

uploaded = st.file_uploader("이미지 업로드 (JPG/PNG/WebP, ≤ 50MB)", type=["png", "jpg", "jpeg", "webp"])

if uploaded:
    st.subheader("원본 미리보기")
    st.image(uploaded, use_container_width=True)

directives = st.text_area("제품 설명을 넣어주세요.", placeholder="예) 우리 제품은 연필과 지우개를 합친 제품이야. 해당 제품에 대해서 실사화를 예쁘게 부탁해.", height=100)
go = st.button("🖼️ 제품 만들기!")

def pil_to_bytes(img: Image.Image, fmt="PNG") -> io.BytesIO:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf

def build_prompt(base: str, extra: str | None) -> str:
    if extra and extra.strip():
        return f"{base}\n\n추가 지시문: {extra.strip()}"
    return base

# --- 세션 상태에 결과 저장소 초기화 ---
if "results" not in st.session_state:
    st.session_state["results"] = []

if go:
    if not uploaded:
        st.warning("이미지를 업로드하세요.")
        st.stop()

    try:
        base_img = Image.open(uploaded).convert("RGBA")
        base_png = pil_to_bytes(base_img, "PNG")
        image_tuple = ("image.png", base_png)

        prompt = build_prompt(BASE_PROMPT, directives)

        with st.spinner("이미지를 생성 중입니다…"):
            resp = client.images.edit(
                model="gpt-image-1",
                prompt=prompt,
                image=image_tuple,
                size="1024x1024",
                n=1
            )

        for data in resp.data:
            b = base64.b64decode(data.b64_json)
            # ★ 세션 상태에 누적 저장
            st.session_state["results"].append(b)

    except Exception as e:
        st.error(f"이미지 편집 중 오류: {e}")

# --- 결과 전체 표시 (세션에 쌓인 모든 이미지) ---
if st.session_state["results"]:
    st.subheader("결과 모아보기")
    for i, b in enumerate(st.session_state["results"], start=1):
        st.image(b, caption=f"Result #{i}", use_container_width=True)
        st.download_button(
            f"⬇️ 제품 #{i} 저장!",
            data=b,
            file_name=f"result_{i}.png",
            mime="image/png",
        )
