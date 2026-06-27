"""공개 랜딩 페이지."""
from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from utils.landing_config import APPLICATION_FORM_URL

ROOT = Path(__file__).resolve().parent.parent
_LANDING_CSS = (ROOT / "assets" / "landing.css").read_text(encoding="utf-8")


def render_landing_page(logo_uri: str) -> None:
    form = html.escape(APPLICATION_FORM_URL)
    logo = html.escape(logo_uri)

    st.markdown(f"<style>{_LANDING_CSS}</style>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="dgt-landing">
  <section class="lnd-hero">
    <img src="{logo}" alt="단골팅" class="lnd-logo"/>
    <h1>기회에는 비수기가 없고,<br/>단골에는 계절이 없습니다.</h1>
    <p class="sub">
      직군·지역·제공가치가 맞는 사람끼리 연결하는<br/>
      <strong>비즈니스 단골 매칭, 단골팅</strong>
    </p>
    <p class="lnd-deco">⬇️ ⬇️ ⬇️ 🤝 ✨ 💼 ⬇️ ⬇️ ⬇️</p>
    <a href="{form}" target="_blank" rel="noopener" class="lnd-btn lnd-btn-primary">
      지금 참여 신청하기
    </a>
    <a href="#faq" class="lnd-btn lnd-btn-outline">자주 묻는 질문</a>
  </section>

  <section class="lnd-section" id="faq">
    <h2>자주 묻는 질문</h2>
    <p class="lnd-lead">궁금한 점을 미리 확인해 보세요</p>
    <details class="lnd-faq" open>
      <summary>단골팅은 어떤 매칭인가요?</summary>
      <p>
        명함 교환만 하는 네트워킹이 아닙니다. <strong>내가 줄 수 있는 것(Have)</strong>과
        <strong>상대가 원하는 것(Want)</strong>을 기준으로, 직군·지역·가치관까지 맞는
        1:1 단골 파트너를 연결합니다.
      </p>
    </details>
    <details class="lnd-faq">
      <summary>누구에게 맞나요?</summary>
      <p>
        창업가, 영업·BD, 컨설턴트, 마케터 등 <strong>실무에서 협업·조언·제휴</strong>가
        필요한 분. 가벼운 소개팅이 아니라, 문제 해결에 진심인 분들을 위한 매칭입니다.
      </p>
    </details>
    <details class="lnd-faq">
      <summary>신청 후 어떻게 되나요?</summary>
      <p>
        구글 폼으로 신청 → 입금 확인 후 매칭 풀에 등록됩니다.
        운영진이 프로필을 검토하고, 가치·직군·지역 기준으로 최적의 상대를 추천·연결합니다.
      </p>
    </details>
    <details class="lnd-faq">
      <summary>외모 승인제인가요?</summary>
      <p>
        아닙니다. <strong>제공가치·원하는 것·협업 깊이</strong>가 기준입니다.
        프로필과 신청 내용을 바탕으로 매칭합니다.
      </p>
    </details>
  </section>

  <section class="lnd-section">
    <h2>참가자들의 생생한 후기</h2>
    <p class="lnd-lead">실제 매칭을 경험한 분들의 이야기</p>
    <div class="lnd-review">
      <div class="meta">2026.06 참여 · B2B 영업</div>
      <p>
        단순히 사람만 소개해 주는 게 아니라, 제가 적어 둔 <strong>Want·Have</strong>를
        보고 맞는 분을 연결해 주셔서 첫 미팅부터 대화가 바로 됐어요.
      </p>
    </div>
    <div class="lnd-review">
      <div class="meta">2026.06 참여 · 컨설턴트</div>
      <p>
        직군·연차만 맞추는 게 아니라 <strong>가치관·협업 깊이</strong>까지 고려해 주셔서
        시간 낭비 없이 깊이 있는 대화를 나눌 수 있었습니다.
      </p>
    </div>
  </section>

  <section class="lnd-section">
    <h2>왜 굳이<br/>「단골팅」이어야 할까요?</h2>
    <p class="lnd-lead">수많은 네트워킹 중, 우리가 고집하는 4가지</p>

    <div class="lnd-reason">
      <div class="lnd-reason-num">01</div>
      <h3>Have · Want 기반 매칭</h3>
      <p class="quote">"명함만 바꾸고 끝나는 만남, 이제 그만."</p>
      <p>
        직군·지역에 더해, <strong>내가 줄 수 있는 것</strong>과 <strong>상대가 원하는 것</strong>을
        맞춥니다. 대화가 바로 실무로 이어지도록 설계했습니다.
      </p>
    </div>
    <div class="lnd-reason">
      <div class="lnd-reason-num">02</div>
      <h3>당신의 프로필은<br/>구경거리가 아닙니다</h3>
      <p class="quote">"SNS 바이럴용 촬영, 단골팅엔 없습니다."</p>
      <p>
        참가자 정보는 매칭 목적으로만 사용합니다. 카메라 의식 없이
        <strong>상대와의 대화</strong>에만 집중할 수 있는 환경을 지킵니다.
      </p>
    </div>
    <div class="lnd-reason">
      <div class="lnd-reason-num">03</div>
      <h3>가벼운 도파민이 아닌,<br/>건강한 연결</h3>
      <p class="quote">"게임보다 대화, 수량보다 질."</p>
      <p>
        억지 아이스브레이킹 대신, 서로의 문제와 역량을 나누는
        <strong>깊이 있는 1:1 매칭</strong>을 추구합니다.
      </p>
    </div>
    <div class="lnd-reason">
      <div class="lnd-reason-num">04</div>
      <h3>운영진이 직접 보는 매칭</h3>
      <p class="quote">"알고리즘만 맡기지 않습니다."</p>
      <p>
        신청서·제공가치·매칭 이력을 함께 보며, 기계적으로 채우지 않고
        <strong>대화가 통할 사람</strong>끼리 연결합니다.
      </p>
    </div>
  </section>

  <section class="lnd-cta-box">
    <h2>지금, 식지 않는 연결을<br/>시작하세요</h2>
    <p>
      기회는 계절을 타지 않습니다.<br/>
      당신의 다음 단골 파트너가 기다리고 있어요.
    </p>
    <a href="{form}" target="_blank" rel="noopener" class="lnd-btn lnd-btn-primary">
      지금 참여 신청하기
    </a>
  </section>

  <footer class="lnd-footer">
    <p>
      <a href="#faq">FAQ</a>
    </p>
    <p>단골팅 · 비즈니스 단골 매칭</p>
    <p>© 2026 단골팅. All rights reserved.</p>
  </footer>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="lnd-admin-link">', unsafe_allow_html=True)
    if st.button("관리자 로그인 →", key="landing_admin_login", type="secondary"):
        st.session_state["admin_login"] = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
