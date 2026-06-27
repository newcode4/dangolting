"""공개 랜딩 페이지."""
from __future__ import annotations

import html
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from utils.landing_config import APPLICATION_FORM_URL, PARTICIPATION_FEE

ROOT = Path(__file__).resolve().parent.parent
_LANDING_CSS = (ROOT / "assets" / "landing.css").read_text(encoding="utf-8")

_LND_PAGE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Pretendard", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
  color: #2c2419;
  background: #f7f4ef;
  line-height: 1.6;
  font-size: 15px;
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; }

.hero { text-align: center; padding: 24px 4px 20px; }
.logo { width: 64px; height: 64px; margin-bottom: 14px; }
.badge {
  display: inline-block;
  font-size: 11px; font-weight: 700; letter-spacing: 0.04em;
  color: #9a6b3f; background: #fff; border: 1px solid #e8dfd3;
  border-radius: 999px; padding: 5px 12px; margin-bottom: 14px;
}
.hero h1 {
  font-size: 22px; font-weight: 800; line-height: 1.45;
  color: #1a1510; letter-spacing: -0.03em; margin-bottom: 12px;
}
.hero .lead {
  font-size: 14px; color: #5c4a38; line-height: 1.65; margin-bottom: 8px;
}
.hero .sub {
  font-size: 13px; color: #8a7968; line-height: 1.55; margin-bottom: 18px;
}
.deco { font-size: 13px; color: #b8895a; margin-bottom: 16px; letter-spacing: 0.12em; }

.btn {
  display: block; width: 100%; text-align: center; text-decoration: none;
  border-radius: 999px; padding: 14px 16px; font-size: 15px; font-weight: 700;
  margin-bottom: 10px;
}
.btn-primary {
  background: linear-gradient(180deg, #b8895a, #9a6b3f);
  color: #fff !important;
  box-shadow: 0 4px 12px rgba(154,107,63,.3);
}
.btn-outline {
  background: #fff; color: #5c4a38 !important;
  border: 1.5px solid #d4c4b0;
}

.section { padding: 28px 0 8px; }
.section h2 {
  font-size: 17px; font-weight: 800; text-align: center;
  color: #1a1510; line-height: 1.45; margin-bottom: 6px;
}
.section .lead {
  text-align: center; font-size: 12px; color: #8a7968; margin-bottom: 16px;
}

.card {
  background: #fff; border: 1px solid #e8dfd3; border-radius: 14px;
  padding: 16px; margin-bottom: 10px;
}
.card p { font-size: 13px; color: #5c4a38; line-height: 1.65; }
.card strong { color: #1a1510; }

.faq summary {
  font-size: 14px; font-weight: 700; cursor: pointer; list-style: none;
}
.faq summary::-webkit-details-marker { display: none; }
.faq p { margin-top: 10px; }

.steps { display: flex; flex-direction: column; gap: 8px; }
.step {
  display: flex; gap: 12px; align-items: flex-start;
  background: #fff; border: 1px solid #e8dfd3; border-radius: 12px; padding: 12px 14px;
}
.step-num {
  flex-shrink: 0; width: 26px; height: 26px; border-radius: 8px;
  background: #f3ebe0; color: #9a6b3f; font-size: 12px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}
.step-body { font-size: 13px; color: #5c4a38; line-height: 1.55; }
.step-body b { display: block; color: #1a1510; font-size: 14px; margin-bottom: 2px; }

.reason { margin-bottom: 22px; }
.reason-num {
  font-size: 11px; font-weight: 800; color: #b8895a;
  letter-spacing: 0.06em; margin-bottom: 4px;
}
.reason h3 {
  font-size: 15px; font-weight: 800; color: #1a1510;
  line-height: 1.45; margin-bottom: 6px;
}
.reason .quote {
  font-size: 13px; color: #8a7968; font-style: italic; margin-bottom: 8px;
}
.reason p { font-size: 13px; color: #5c4a38; line-height: 1.65; }

.review-meta { font-size: 11px; color: #b8895a; font-weight: 600; margin-bottom: 6px; }

.cta-box {
  text-align: center; background: #fff;
  border: 1px solid #e8dfd3; border-radius: 16px;
  padding: 24px 16px; margin: 28px 0 20px;
}
.cta-box h2 { font-size: 17px; margin-bottom: 8px; }
.cta-box p { font-size: 13px; color: #6b5d4f; margin-bottom: 16px; line-height: 1.6; }

.note {
  font-size: 11px; color: #9a8b7a; text-align: center;
  line-height: 1.55; padding: 12px 0 20px;
}
.footer {
  text-align: center; font-size: 11px; color: #9a8b7a;
  padding-top: 14px; border-top: 1px solid #e8dfd3; line-height: 1.7;
}
"""


def _landing_html(logo_uri: str, form_url: str) -> str:
    logo = html.escape(logo_uri)
    form = html.escape(form_url)
    fee = html.escape(PARTICIPATION_FEE)

    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>{_LND_PAGE_CSS}</style></head>
<body>
<div class="dgt-landing-root">

  <section class="hero">
    <img src="{logo}" alt="단골팅" class="logo"/>
    <span class="badge">비즈니스 결정사</span>
    <h1>내 사업의 &lsquo;찐단골&rsquo;을<br/>찾는 단골팅</h1>
    <p class="lead">
      단순히 명함을 바꾸는 네트워킹이 아닙니다.<br/>
      <strong>Have · Want</strong>가 맞고, 서로의 결핍을 채워 줄<br/>
      <strong>1:1 비즈니스 단골</strong>을 연결합니다.
    </p>
    <p class="sub">
      돈만 쓰고 가는 손님이 아니라,<br/>
      내 편이 되어 오래 응원해 줄 파트너를 찾습니다.
    </p>
    <p class="deco">🤝 &nbsp; ✨ &nbsp; 💼</p>
    <a href="{form}" target="_blank" rel="noopener" class="btn btn-primary">지금 참여 신청하기</a>
    <a href="#faq" class="btn btn-outline">자주 묻는 질문</a>
    <p class="note">참가비 {fee} · 신청 후 14일 내 1:1 매칭 케어</p>
  </section>

  <section class="section">
    <h2>단골팅이 보는 &lsquo;결&rsquo;</h2>
    <p class="lead">진정성 있는 신청만 매칭 풀에 올립니다</p>
    <div class="card">
      <p><strong>01 · 구체성</strong><br/>
      &ldquo;피드백 원해요&rdquo;가 아니라, <strong>지금 어떤 상황</strong>이고
      <strong>상대가 어떻게 도와주면 좋을지</strong> 적어 주셔야 합니다.</p>
    </div>
    <div class="card">
      <p><strong>02 · 기브 앤 테이크</strong><br/>
      받고 싶은 깊이만큼, 내가 줄 수 있는 <strong>Have</strong>도
      구체적으로 적혀 있어야 합니다.</p>
    </div>
    <div class="card">
      <p><strong>03 · 가치관 · 깊이</strong><br/>
      직군·지역을 넘어 <strong>비즈니스 철학</strong>과
      <strong>협업 깊이</strong>까지 맞는 사람끼리 연결합니다.</p>
    </div>
  </section>

  <section class="section">
    <h2>신청 후 진행</h2>
    <p class="lead">대표님이 직접 1:1로 케어합니다</p>
    <div class="steps">
      <div class="step">
        <span class="step-num">1</span>
        <div class="step-body"><b>신청 · 입금 확인</b>Have/Want를 구체적으로 작성해 주세요.</div>
      </div>
      <div class="step">
        <span class="step-num">2</span>
        <div class="step-body"><b>매칭 풀 등록 (D-14)</b>14일 안에 결이 맞는 상대를 찾습니다.</div>
      </div>
      <div class="step">
        <span class="step-num">3</span>
        <div class="step-body"><b>익명 프로필 + 매칭 근거</b>왜 이 분인지 이유와 함께 1:1 제안.</div>
      </div>
      <div class="step">
        <span class="step-num">4</span>
        <div class="step-body"><b>3인 단톡 연결</b>수락 시 카톡방 개설 후 매니저 퇴장.</div>
      </div>
    </div>
  </section>

  <section class="section" id="faq">
    <h2>자주 묻는 질문</h2>
    <p class="lead">신청 전 확인해 주세요</p>
    <details class="card faq" open>
      <summary>외모 승인제인가요?</summary>
      <p>아닙니다. <strong>제공가치 · Want · 협업 깊이 · 가치관</strong>이 기준입니다.</p>
    </details>
    <details class="card faq">
      <summary>매칭이 안 되면 환불되나요?</summary>
      <p>신청일 기준 <strong>7일 이내</strong> 조건에 맞는 상대를 찾지 못하면
      참가비 <strong>전액 환불</strong>합니다. (3인 단톡 개설 이후 환불 불가)</p>
    </details>
    <details class="card faq">
      <summary>Have / Want는 어떻게 쓰나요?</summary>
      <p><strong>[현재 상황] + [원하는 행동]</strong> 형태로 적어 주세요.
      &ldquo;로고 필요해요&rdquo;보다 &ldquo;출시 직전 랜딩 UI를
      단골 시선으로 뜯어봐 주실 분&rdquo;이 좋습니다.</p>
    </details>
    <details class="card faq">
      <summary>데모 기수 · 세금계산서</summary>
      <p>1기는 매칭 로직 검증용 데모입니다. 환불 가능 구조상
      <strong>세금계산서·현금영수증 발행은 어렵습니다.</strong></p>
    </details>
  </section>

  <section class="section">
    <h2>참가자 후기</h2>
    <p class="lead">실제 매칭 경험</p>
    <div class="card">
      <div class="review-meta">2026.06 · B2B 영업</div>
      <p>Want·Have를 보고 연결해 주셔서 첫 미팅부터 대화가 바로 됐어요.
      명함만 바꾸는 모임과는 차원이 달랐습니다.</p>
    </div>
    <div class="card">
      <div class="review-meta">2026.06 · 컨설턴트</div>
      <p>가치관·협업 깊이까지 맞춰 주셔서 시간 낭비 없이
      깊은 대화로 이어졌습니다.</p>
    </div>
  </section>

  <section class="section">
    <h2>왜 단골팅인가</h2>
    <p class="lead">수많은 네트워킹 중, 우리가 고집하는 4가지</p>

    <div class="reason">
      <div class="reason-num">01</div>
      <h3>Have · Want 기반 매칭</h3>
      <p class="quote">&ldquo;명함만 바꾸고 끝나는 만남, 이제 그만.&rdquo;</p>
      <p>직군·지역 + 내가 줄 수 있는 것과 상대의 결핍을 맞춥니다.
      대화가 곧 실무로 이어지도록 설계했습니다.</p>
    </div>
    <div class="reason">
      <div class="reason-num">02</div>
      <h3>프라이빗 매칭</h3>
      <p class="quote">&ldquo;당신의 프로필은 구경거리가 아닙니다.&rdquo;</p>
      <p>바이럴 촬영 없음. 참가자 정보는 매칭 목적으로만 사용합니다.</p>
    </div>
    <div class="reason">
      <div class="reason-num">03</div>
      <h3>건강한 연결</h3>
      <p class="quote">&ldquo;가벼운 도파민이 아닌, 진짜 교감.&rdquo;</p>
      <p>게임·억지 프로그램 대신, 서로의 문제와 역량을 나누는 1:1 매칭.</p>
    </div>
    <div class="reason">
      <div class="reason-num">04</div>
      <h3>운영진 직접 큐레이션</h3>
      <p class="quote">&ldquo;알고리즘만 맡기지 않습니다.&rdquo;</p>
      <p>신청서·가치·매칭 이력을 보고, 대화가 통할 사람끼리 연결합니다.
      매칭 근거를 함께 전달합니다.</p>
    </div>
  </section>

  <section class="cta-box">
    <h2>지금, 식지 않는 연결을<br/>시작하세요</h2>
    <p>당신의 다음 단골 파트너가<br/>기다리고 있습니다.</p>
    <a href="{form}" target="_blank" rel="noopener" class="btn btn-primary">지금 참여 신청하기</a>
  </section>

  <footer class="footer">
    <p>단골팅 · 비즈니스 단골 매칭</p>
    <p>© 2026 단골팅</p>
  </footer>
</div>
</body></html>"""


def render_landing_page(logo_uri: str) -> None:
    st.markdown(f'<div class="dgt-landing-root"></div><style>{_LANDING_CSS}</style>', unsafe_allow_html=True)
    components.html(_landing_html(logo_uri, APPLICATION_FORM_URL), height=3400, scrolling=True)

    st.markdown('<div class="lnd-admin-link">', unsafe_allow_html=True)
    if st.button("관리자 로그인 →", key="landing_admin_login", type="secondary"):
        st.session_state["admin_login"] = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
