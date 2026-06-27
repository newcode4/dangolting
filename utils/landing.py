"""공개 랜딩 페이지."""
from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from utils.landing_config import APPLICATION_FORM_URL, LANDING_IFRAME_HEIGHT, PARTICIPATION_FEE

ROOT = Path(__file__).resolve().parent.parent
_SHELL_CSS_PATH = ROOT / "assets" / "landing.css"
_PAGE_CSS_PATH = ROOT / "assets" / "landing-page.css"


def _read_css(path: Path) -> str:
    """렌더 시점에 읽어 CSS 변경이 새로고침만으로 반영되게 함."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _landing_html(logo_uri: str, form_url: str, page_css: str, shell_css: str, *, shell_preview: bool = False) -> str:
    logo = html.escape(logo_uri)
    form = html.escape(form_url)
    fee = html.escape(PARTICIPATION_FEE)
    shell_js = json.dumps(shell_css)
    shell_preview_js = "true" if shell_preview else "false"

    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>{page_css}</style>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js"></script>
</head>
<body>
<div class="page-bg" aria-hidden="true"></div>
<div class="dgt-landing-root">
<div class="page">

  <header class="site-header">
    <a class="brand" href="#">
      <img src="{logo}" alt=""/>
      <span>단골팅</span>
    </a>
  </header>

  <section class="hero">
    <div class="hero-glow"></div>
    <div class="hero-stars"></div>
    <div class="hero-inner">
      <span class="eyebrow">혼자 달려온 사람들을 위한 1:1 단골 매칭</span>
      <h1>결이 맞는 한 사람이,<br/>모든 걸 바꿉니다</h1>
      <p class="lead">
        하는 일은 달라도, 우리가 원하는 건 닮아 있습니다.<br/>
        같이 고민할 동료, 솔직한 피드백, 내 일을 깊이 묻는 사람 —<br/>
        <strong style="color:#f1f5f9">서로 주고받을 수 있는 단 한 사람</strong>을 단골팅이 찾아 드립니다.
      </p>
      <div class="hero-icons">
        <span class="chip"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></span>
        <span class="chip"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg></span>
        <span class="chip"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg></span>
      </div>
      <div class="hero-cta">
        <a href="#" data-external="{form}" class="btn btn-primary">
          <span>지금 참여 신청하기</span>
          <span class="arrow">&rarr;</span>
        </a>
        <a href="#faq" class="btn btn-outline">자주 묻는 질문</a>
      </div>
      <p class="price-line">운영진이 못 찾으면 전액 환불 · 지금이 가장 저렴합니다</p>
    </div>
  </section>

  <div class="trust-strip reveal-item">
    <strong>1:1 큐레이션</strong><span class="dot"></span>
    <span>14일 케어</span><span class="dot"></span>
    <span>익명 프로필 소개</span><span class="dot"></span>
    <span>미매칭 전액 환불</span>
  </div>

  <section class="hook-panel section--alt reveal">
    <div class="hook-head reveal-item">
      <span class="hook-kicker">↓ 스크롤하면 숫자가 살아납니다</span>
      <h2>혼자면 <em>100</em> — 결이 맞으면 <em>300</em></h2>
      <p>막연한 인맥이 아니라, <strong>주고받을 한 사람</strong>이 있을 때 궤적이 달라집니다.</p>
    </div>

    <div class="hook-flow reveal-item">
      <div class="hook-step">
        <div class="hook-step-num"><span class="count" data-count="80000" data-suffix="+">0</span></div>
        <div class="hook-step-lbl">평생 스쳐가는 인연</div>
      </div>
      <div class="hook-arrow" aria-hidden="true"><span>→</span></div>
      <div class="hook-step hook-step--mid">
        <div class="hook-step-num"><span class="count" data-count="2" data-prefix="~" data-suffix="명">0</span></div>
        <div class="hook-step-lbl">1년에 새로 만나는<br/>결이 맞는 사람</div>
      </div>
      <div class="hook-arrow" aria-hidden="true"><span>→</span></div>
      <div class="hook-step hook-step--hot">
        <div class="hook-step-num"><span class="count" data-count="3" data-suffix="배">0</span></div>
        <div class="hook-step-lbl">혼자 100일 때<br/>함께면 300</div>
      </div>
    </div>

    <div class="hook-bars reveal-item">
      <div class="hook-bar-row">
        <div class="hook-bar-meta">
          <span class="hook-bar-title">혼자 헤매는 시간</span>
          <span class="hook-bar-val">100%</span>
        </div>
        <div class="hook-bar-track"><div class="hook-bar-fill hook-bar-fill--solo" data-fill="100"></div></div>
      </div>
      <div class="hook-bar-connector"><span class="hook-bar-arrow-icon">↓</span> 단골 한 명이면</div>
      <div class="hook-bar-row hook-bar-row--up">
        <div class="hook-bar-meta">
          <span class="hook-bar-title">함께 달릴 때 속도</span>
          <span class="hook-bar-val hook-bar-val--hot"><span class="count" data-count="300" data-suffix="%">0</span></span>
        </div>
        <div class="hook-bar-track"><div class="hook-bar-fill hook-bar-fill--duo" data-fill="100"></div></div>
      </div>
    </div>

    <a href="#process" class="hook-cta reveal-item">
      <span>어떻게 연결되나요?</span>
      <span class="hook-cta-arrow">→</span>
    </a>
  </section>

  <section class="section section--alt reveal">
    <div class="framing-head reveal-item">
      <h2>우리는 평생 몇 명을 만날까요?<br/>그중 <em>결이 맞는 사람</em>은요?</h2>
      <p>
        스쳐가는 인연은 수만 명. 하지만 <strong>내 결을 아는 사람</strong>은 손에 꼽습니다.<br/>
        그래서 한 명을 <strong>빨리 만날수록</strong> 이득입니다. 혼자 헤맬 길이 절반으로 줄어드니까요.
      </p>
    </div>
    <div class="stat-grid">
      <div class="stat reveal-item">
        <div class="big"><span class="count" data-count="80000" data-suffix="+">0</span></div>
        <div class="cap">평생 스쳐가는 사람<br/><b>그러나 대부분 한 번뿐</b></div>
      </div>
      <div class="stat reveal-item">
        <div class="big"><span class="count" data-count="2" data-prefix="~" data-suffix="명">0</span></div>
        <div class="cap">1년에 새로 만나는<br/><b>진짜 결이 맞는 사람</b></div>
      </div>
      <div class="stat reveal-item">
        <div class="big"><span class="count" data-count="3" data-suffix="배">0</span></div>
        <div class="cap">혼자 100을 할 때<br/><b>맞는 단골과는 300</b></div>
      </div>
    </div>
  </section>

  <section class="section reveal">
    <div class="section-head reveal-item">
      <h2>이런 &lsquo;단골&rsquo;을 만납니다</h2>
      <p>카테고리는 정해져 있어도, 내가 원하는 가치는 무궁무진하니까</p>
    </div>
    <div class="meet-grid">
      <div class="meet-card reveal-item">
        <span class="icon-chip">동</span>
        <div>
          <h3>같은 고민을 나누는 동료</h3>
          <p>비슷한 길을 걷는 사람과, 새벽까지 혼자 끙끙대던 고민을 함께 풉니다.</p>
        </div>
      </div>
      <div class="meet-card reveal-item">
        <span class="icon-chip">피</span>
        <div>
          <h3>솔직한 피드백을 주는 사람</h3>
          <p>좋은 말만 하는 사이가 아니라, 내 일을 진짜로 봐주고 짚어 주는 한 사람.</p>
        </div>
      </div>
      <div class="meet-card reveal-item">
        <span class="icon-chip">인</span>
        <div>
          <h3>내 일을 깊이 묻는 인터뷰어</h3>
          <p>질문을 통해 내 생각이 정리되고, 미처 못 본 기회가 보이게 해주는 사람.</p>
        </div>
      </div>
      <div class="meet-card reveal-item">
        <span class="icon-chip">파</span>
        <div>
          <h3>가치를 주고받는 파트너</h3>
          <p>내가 가진 것과 상대가 필요한 것이 맞물려, 서로를 끌어올리는 관계.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--alt reveal">
    <div class="section-head reveal-item">
      <h2>단골팅이 보는 &lsquo;찐&rsquo;</h2>
      <p>오래 가는 관계를 만드는 3가지 기준</p>
    </div>
    <div class="card-grid-3">
      <div class="value-card reveal-item">
        <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg></div>
        <div class="num">01</div>
        <h3>구체성</h3>
        <p>지금 뭐가 필요한지 또렷한 분을 봅니다. 막연한 인맥이 아니라, 진짜 필요한 연결인지 확인합니다.</p>
      </div>
      <div class="value-card reveal-item">
        <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg></div>
        <div class="num">02</div>
        <h3>주고받을 마음</h3>
        <p>받기만 하는 게 아니라, 줄 것도 있는 분. 서로를 끌어올릴 준비가 된 사람끼리 연결합니다.</p>
      </div>
      <div class="value-card reveal-item">
        <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg></div>
        <div class="num">03</div>
        <h3>지속성 · 진심</h3>
        <p>한 번 보고 끝이 아닙니다. 오래 가는 단골 관계를, 진심으로 임하는 분과 만들어 갑니다.</p>
      </div>
    </div>
  </section>

  <section class="section reveal" id="process">
    <div class="section-head reveal-item">
      <h2>신청 후 진행</h2>
      <p>단계별로 진행되는 단골 매칭 프로세스</p>
    </div>
    <div class="timeline">
      <div class="timeline-step reveal-item">
        <div class="circle">01</div>
        <b>입금 확인</b>
        <span>신청서 작성 후 참가비 입금</span>
      </div>
      <div class="timeline-step reveal-item">
        <div class="circle">02</div>
        <b>매칭 서칭</b>
        <span>운영진이 결 맞는 상대 탐색 · 14일</span>
      </div>
      <div class="timeline-step reveal-item">
        <div class="circle">03</div>
        <b>개별 소개</b>
        <span>익명 프로필로 1:1 소개</span>
      </div>
      <div class="timeline-step reveal-item">
        <div class="circle">04</div>
        <b>1:1 단톡 연결</b>
        <span>수락 시 카톡방 개설</span>
      </div>
    </div>
  </section>

  <section class="section section--alt reveal">
    <div class="section-head reveal-item">
      <h2>왜 단골팅인가?</h2>
      <p>수많은 모임 중, 우리가 다른 4가지</p>
    </div>
    <div class="why-grid">
      <div class="why-item reveal-item">
        <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
        <h3>결 기반<br/>매칭</h3>
        <p>직군 너머, 주고받을<br/>가치로 연결</p>
      </div>
      <div class="why-item reveal-item">
        <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>
        <h3>프라이빗<br/>1:1</h3>
        <p>프로필 공개 없이<br/>1:1로만 제안</p>
      </div>
      <div class="why-item reveal-item">
        <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>
        <h3>안전한<br/>연결</h3>
        <p>바이럴·촬영 없이<br/>매칭 목적만</p>
      </div>
      <div class="why-item reveal-item">
        <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></div>
        <h3>운영진 직접<br/>큐레이션</h3>
        <p>신청서를 직접 읽고<br/>1:1로 조율</p>
      </div>
    </div>
  </section>

  <section class="section reveal">
    <div class="section-head reveal-item">
      <h2>참가자 후기</h2>
      <p>실제 회원들의 리얼 후기</p>
    </div>
    <div class="review-grid">
      <div class="review-card reveal-item">
        <div class="review-meta">2026.06 · 마케팅 디렉터</div>
        <p>&ldquo;첫 미팅부터 실무 이야기로 바로 들어갔어요. 명함만 바꾸던 모임과는 차원이 달랐습니다.&rdquo;</p>
        <div class="stars">★★★★★</div>
      </div>
      <div class="review-card reveal-item">
        <div class="review-meta">2026.06 · 프리랜서 디자이너</div>
        <p>&ldquo;결이 맞는 사람을 연결해 주셔서 시간 낭비 없이 깊은 대화로 이어졌고, 이후 협업까지 됐어요.&rdquo;</p>
        <div class="stars">★★★★★</div>
      </div>
    </div>
    <div class="review-more">
      <a href="#" class="btn btn-outline" data-external="{form}">후기 더보기</a>
    </div>
  </section>

  <section class="section reveal" id="faq">
    <div class="section-head reveal-item">
      <h2>자주 묻는 질문</h2>
      <p>신청 전 궁금한 내용을 확인해보세요</p>
    </div>
    <div class="faq-list">
      <details class="faq reveal-item">
        <summary>외모 · 나이도 보나요?</summary>
        <p>아닙니다. <strong>지금 뭐가 필요한지, 무엇을 주고받을 수 있는지</strong>가 기준입니다. 진지하게 단골을 찾는 분만 받습니다.</p>
      </details>
      <details class="faq reveal-item">
        <summary>매칭이 안 되면 어떻게 되나요?</summary>
        <p>운영진이 <strong>14일 이내</strong> 결 맞는 상대를 찾지 못하거나 조율 과정에서 결렬되면 참가비 <strong>전액 환불</strong>합니다. 다만 소개해 드린 프로필을 누적 <strong>2회 거절</strong>하시면 기회 소진으로 보아 환불되지 않습니다. (자세한 내용은 아래 환불 규정)</p>
      </details>
      <details class="faq reveal-item">
        <summary>신청서는 어떻게 쓰나요?</summary>
        <p><strong>[지금 내 상황] + [받고 싶은 것] + [내가 줄 수 있는 것]</strong>을 솔직하게 적어 주세요. 구체적일수록 더 잘 맞는 사람을 만납니다.</p>
      </details>
      <details class="faq reveal-item">
        <summary>세금계산서 발행되나요?</summary>
        <p>1기는 매칭 로직 검증용 데모 기수입니다. 환불 가능 구조상 <strong>세금계산서 · 현금영수증 발행은 어렵습니다.</strong></p>
      </details>
    </div>
    <div class="rule-links">
      <button type="button" data-modal="refundModal">환불 및 거절 규정</button>
      <button type="button" data-modal="privacyModal">개인정보 수집 및 이용</button>
    </div>
  </section>

  <section class="cta-band reveal">
    <h2 class="reveal-item">이제, 가만히 시간만 보내지 마세요</h2>
    <p class="reveal-item">
      운영진이 끝내 못 찾으면 돌려받고, 만나면 천금 같은 기회입니다. 남는 장사입니다.<br/>
      혼자서는 한계가 있습니다 — 동료든 파트너든, 지금 내 단골을 만드세요.
    </p>
    <a href="#" data-external="{form}" class="btn btn-primary reveal-item">
      <span>지금 참여 신청하기</span>
      <span class="arrow">&rarr;</span>
    </a>
    <p class="price-line" style="margin-top:16px">참가비 {fee} · 운영진 미매칭 시 전액 환불</p>
  </section>

  <footer class="site-footer">
    <div>
      <div class="footer-brand">
        <img src="{logo}" alt=""/>
        <span>단골팅</span>
      </div>
      <p class="footer-copy">&copy; 2026 단골팅. All rights reserved.</p>
    </div>
    <nav class="footer-links">
      <button type="button" data-modal="refundModal">환불 규정</button>
      <button type="button" data-modal="privacyModal">개인정보처리방침</button>
      <button type="button" data-external="{form}">문의하기</button>
    </nav>
  </footer>

  <div class="modal" id="refundModal" aria-hidden="true">
    <div class="modal-backdrop" data-close="refundModal"></div>
    <div class="rule-dialog modal-panel" role="dialog" aria-labelledby="refundTitle">
      <div class="dlg-head">
        <h3 id="refundTitle">환불 및 거절 규정</h3>
        <button type="button" class="dlg-close" data-close="refundModal" aria-label="닫기">&times;</button>
      </div>
      <div class="dlg-body">
        <h4>전액 환불</h4>
        <p>신청일 기준 14일 이내에 조건에 부합하는 상대를 찾지 못하거나, 주최자의 1:1 조율 과정에서 매칭이 최종 결렬될 경우 참가비 {fee} 전액을 조건 없이 즉시 환불해 드립니다. 단, 대표님의 1:1 밀착 조율을 거쳐 최종 3인 매칭 단톡방이 개설된 이후에는 어떤 이유로도 환불이 불가능합니다.</p>
        <h4>거절 · 재매칭</h4>
        <p>대표님이 1:1로 전달해 드리는 상대방의 익명 프로필 카드를 확인하신 후 핏이 맞지 않으면 비밀리에 거절하실 수 있으나, 무분별한 노쇼 방지 및 매칭 풀 관리를 위해 프로필 거절 및 재매칭 기회는 최대 2회로 제한됩니다. 누적 2회 거절 시 서비스는 자동으로 종료되며, 이 경우 개인 변심 및 기회 소진으로 간주하여 참가비가 환불되지 않습니다. 원활한 진행을 위해 중간 가치 조율 과정에 적극적인 협조를 부탁드립니다.</p>
        <div class="acct">
          <b>입금 계좌</b><br/>
          국민은행 942902-00-243479 (예금주: 이주환)<br/>
          참가비 {fee}
        </div>
      </div>
    </div>
  </div>

  <div class="modal" id="privacyModal" aria-hidden="true">
    <div class="modal-backdrop" data-close="privacyModal"></div>
    <div class="rule-dialog modal-panel" role="dialog" aria-labelledby="privacyTitle">
      <div class="dlg-head">
        <h3 id="privacyTitle">개인정보 수집 및 이용 동의</h3>
        <button type="button" class="dlg-close" data-close="privacyModal" aria-label="닫기">&times;</button>
      </div>
      <div class="dlg-body">
        <h4>수집 · 이용 목적</h4>
        <p>참가자 본인 확인 및 연락, 받고 싶은 가치 / 줄 수 있는 가치 데이터 기반의 1:1 매칭 조율, 최종 매칭 성공 시 상대방과의 3인 단톡방 개설, 매칭 안내 및 단골팅 커뮤니티 회원 관리.</p>
        <h4>수집 항목</h4>
        <p>이름(성함), 성별, 주로 활동하는 지역, 연락처(휴대폰 번호), 메인 직군, 연차 및 체급, 내가 줄 수 있는 가치, 내가 받고 싶은 가치.</p>
        <h4>보유 · 이용 기간</h4>
        <p>회원 탈퇴 요청 시까지 보유. 단, 미매칭 후 환불 신청자는 당일 즉시 파기합니다.</p>
        <h4>동의 거부 권리</h4>
        <p>귀하는 본 개인정보 수집 및 이용 동의를 거부할 권리가 있으나, 동의하지 않으실 경우 단골팅의 1:1 매칭 큐레이션 서비스 이용이 불가능합니다.</p>
      </div>
    </div>
  </div>

</div>
</div>
<script>
(function () {{
  var shellPreview = {shell_preview_js};
  var motionReady = false;
  var parentScroller = null;

  function measureContentHeight() {{
    var page = document.querySelector(".page");
    if (page) {{
      return Math.ceil(page.getBoundingClientRect().height + 16);
    }}
    return Math.ceil(document.body.offsetHeight + 16);
  }}

  function expandParentChain(frame, h) {{
    try {{
      var doc = window.parent.document;
      var node = frame ? frame.parentElement : null;
      while (node && node !== doc.body) {{
        node.style.height = h + "px";
        node.style.minHeight = h + "px";
        node.style.maxHeight = "none";
        node.style.overflow = "visible";
        node = node.parentElement;
      }}
      ["stElementContainer", "stVerticalBlock", "stMainBlockContainer", "stMain", "stAppViewContainer"].forEach(function (tid) {{
        var el = doc.querySelector('[data-testid="' + tid + '"]');
        if (!el) return;
        el.style.height = h + "px";
        el.style.minHeight = h + "px";
        el.style.maxHeight = "none";
        el.style.overflow = "visible";
      }});
    }} catch (e) {{}}
  }}

  function syncFrameHeight() {{
    var h = measureContentHeight();
    try {{
      window.parent.postMessage({{ type: "streamlit:setFrameHeight", height: h }}, "*");
      var frame = window.frameElement;
      if (frame) {{
        frame.style.height = h + "px";
        frame.style.maxHeight = "none";
        frame.style.minHeight = "0";
        frame.setAttribute("scrolling", "no");
        frame.style.overflow = "hidden";
        expandParentChain(frame, h);
      }}
    }} catch (e) {{}}
    if (window.ScrollTrigger) ScrollTrigger.refresh();
  }}

  function getParentScroller() {{
    try {{
      var pdoc = window.parent.document;
      if (pdoc.documentElement.scrollHeight > pdoc.documentElement.clientHeight + 2) {{
        return pdoc.scrollingElement || pdoc.documentElement;
      }}
      var el = pdoc.querySelector('section[data-testid="stMain"]');
      if (el && el.scrollHeight > el.clientHeight + 2) return el;
      return pdoc.scrollingElement || pdoc.documentElement;
    }} catch (e) {{
      return document.documentElement;
    }}
  }}

  function setupScrollTriggerProxy() {{
    if (typeof ScrollTrigger === "undefined") return null;
    var pwin = window.parent;
    var scroller = getParentScroller();
    parentScroller = scroller;

    ScrollTrigger.scrollerProxy(scroller, {{
      scrollTop: function (value) {{
        if (arguments.length) {{
          if (scroller === pwin.document.documentElement || scroller === pwin.document.body) {{
            pwin.scrollTo(0, value);
          }} else {{
            scroller.scrollTop = value;
          }}
        }}
        if (scroller === pwin.document.documentElement || scroller === pwin.document.body) {{
          return pwin.scrollY || pwin.document.documentElement.scrollTop || 0;
        }}
        return scroller.scrollTop;
      }},
      getBoundingClientRect: function () {{
        return {{
          top: 0,
          left: 0,
          width: pwin.innerWidth,
          height: pwin.innerHeight
        }};
      }}
    }});

    var onScroll = function () {{ ScrollTrigger.update(); }};
    scroller.addEventListener("scroll", onScroll, {{ passive: true }});
    pwin.addEventListener("scroll", onScroll, {{ passive: true }});
    ScrollTrigger.defaults({{ scroller: scroller }});
    return scroller;
  }}

  function trackEvent(evt) {{
    try {{
      var vid = localStorage.getItem("dgt_vid");
      if (!vid) {{
        vid = "v_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
        localStorage.setItem("dgt_vid", vid);
      }}
      var loc = window.parent.location;
      var base = loc.origin + loc.pathname;
      var q = "evt=" + encodeURIComponent(evt) + "&vid=" + encodeURIComponent(vid);
      var img = new Image();
      img.src = base + (base.indexOf("?") >= 0 ? "&" : "?") + q + "&_=" + Date.now();
    }} catch (e) {{}}
  }}

  function injectShell() {{
    try {{
      var css = {shell_js};
      var doc = window.parent.document;
      var id = "dgt-landing-shell-css";
      var el = doc.getElementById(id);
      if (!el) {{
        el = doc.createElement("style");
        el.id = id;
        doc.head.appendChild(el);
      }}
      el.textContent = css;
      doc.body.classList.add("dgt-landing");
      if (shellPreview) doc.body.classList.add("dgt-landing--preview");
      doc.documentElement.style.height = "auto";
      doc.documentElement.style.overflowY = "auto";
      doc.body.style.height = "auto";
      doc.body.style.overflowY = "auto";
      ["stMainBlockContainer", "stAppViewBlockContainer", "stVerticalBlock", "stElementContainer"].forEach(function (tid) {{
        doc.querySelectorAll('[data-testid="' + tid + '"]').forEach(function (node) {{
          node.style.padding = "0";
          node.style.paddingTop = "0";
          node.style.marginTop = "0";
        }});
      }});
      doc.querySelectorAll(".block-container").forEach(function (node) {{
        node.style.padding = "0";
        node.style.paddingTop = "0";
        node.style.marginTop = "0";
      }});
      syncFrameHeight();
    }} catch (e) {{}}
  }}

  function lockParentScroll(locked) {{
    try {{
      var scroller = parentScroller || getParentScroller();
      if (!scroller || !scroller.style) return;
      scroller.style.overflow = locked ? "hidden" : "";
    }} catch (e) {{}}
  }}

  function openModal(id) {{
    var el = document.getElementById(id);
    if (!el) return;
    el.classList.add("is-open");
    el.setAttribute("aria-hidden", "false");
    lockParentScroll(true);
    refreshMotion();
  }}

  function closeModal(id) {{
    var el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("is-open");
    el.setAttribute("aria-hidden", "true");
    lockParentScroll(false);
    refreshMotion();
  }}

  function openExternal(url) {{
    if (!url) return;
    try {{
      var w = window.parent.open(url, "_blank", "noopener,noreferrer");
      if (!w) window.open(url, "_blank", "noopener,noreferrer");
    }} catch (e) {{
      window.open(url, "_blank", "noopener,noreferrer");
    }}
  }}

  function initMotion() {{
    if (motionReady) return;
    if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") return;
    motionReady = true;
    document.documentElement.classList.add("js-motion-ready");

    var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    gsap.registerPlugin(ScrollTrigger);
    var scroller = setupScrollTriggerProxy() || document.documentElement;

    if (reduced) {{
      gsap.set(".reveal-item, .hero-inner > *, .count", {{ clearProps: "all", opacity: 1, y: 0 }});
      document.querySelectorAll(".count").forEach(function (el) {{
        el.textContent = (el.getAttribute("data-prefix") || "") + (el.getAttribute("data-count") || "") + (el.getAttribute("data-suffix") || "");
      }});
      document.querySelectorAll(".hook-bar-fill").forEach(function (el) {{
        el.style.width = (el.getAttribute("data-fill") || "0") + "%";
      }});
      syncFrameHeight();
      return;
    }}

    function initHookCounters() {{
      document.querySelectorAll(".count").forEach(function (el) {{
        var end = parseFloat(el.getAttribute("data-count") || "0");
        var suffix = el.getAttribute("data-suffix") || "";
        var prefix = el.getAttribute("data-prefix") || "";
        var obj = {{ val: 0 }};
        var tween = gsap.to(obj, {{
          val: end,
          duration: 1.6,
          ease: "power2.out",
          paused: true,
          onUpdate: function () {{
            var v = end >= 1000 ? Math.round(obj.val).toLocaleString("ko-KR") : Math.round(obj.val);
            el.textContent = prefix + v + suffix;
          }}
        }});
        ScrollTrigger.create({{
          scroller: scroller,
          trigger: el.closest(".hook-panel, .stat-grid, .hook-bars") || el,
          start: "top 84%",
          onEnter: function () {{ obj.val = 0; tween.restart(); }},
          onEnterBack: function () {{ obj.val = 0; tween.restart(); }},
          onLeaveBack: function () {{
            gsap.set(obj, {{ val: 0 }});
            el.textContent = prefix + "0" + suffix;
          }}
        }});
      }});
    }}

    function initHookBars() {{
      document.querySelectorAll(".hook-bar-fill").forEach(function (fill) {{
        var pct = fill.getAttribute("data-fill") || "0";
        gsap.fromTo(
          fill,
          {{ width: "0%" }},
          {{
            width: pct + "%",
            ease: "none",
            scrollTrigger: {{
              scroller: scroller,
              trigger: fill.closest(".hook-bars"),
              start: "top 85%",
              end: "top 35%",
              scrub: 0.4
            }}
          }}
        );
      }});
      gsap.utils.toArray(".hook-arrow span").forEach(function (arrow) {{
        gsap.fromTo(
          arrow,
          {{ x: -6, opacity: 0.35 }},
          {{
            x: 6,
            opacity: 1,
            ease: "none",
            scrollTrigger: {{
              scroller: scroller,
              trigger: arrow.closest(".hook-flow"),
              start: "top 80%",
              end: "top 45%",
              scrub: 0.35
            }}
          }}
        );
      }});
    }}

    initHookCounters();
    initHookBars();

    gsap.from(".hero-glow", {{
      scale: 0.88,
      opacity: 0,
      duration: 1.1,
      ease: "power2.out"
    }});

    gsap.from(".hero-inner > *", {{
      y: 32,
      opacity: 0,
      duration: 0.85,
      stagger: 0.08,
      ease: "power3.out",
      delay: 0.08
    }});

    function revealIn(batch) {{
      gsap.to(batch, {{
        opacity: 1,
        y: 0,
        duration: 0.68,
        stagger: {{ each: 0.06, from: "start" }},
        ease: "power3.out",
        overwrite: "auto"
      }});
    }}

    function revealOut(batch) {{
      gsap.to(batch, {{
        opacity: 0,
        y: 28,
        duration: 0.52,
        stagger: {{ each: 0.04, from: "end" }},
        ease: "power2.in",
        overwrite: "auto"
      }});
    }}

    ScrollTrigger.batch(".reveal-item", {{
      scroller: scroller,
      start: "top 88%",
      end: "bottom 12%",
      onEnter: revealIn,
      onLeave: revealOut,
      onEnterBack: revealIn,
      onLeaveBack: revealOut
    }});

    gsap.utils.toArray(".section.reveal, .cta-band.reveal, .hook-panel.reveal").forEach(function (section) {{
      gsap.fromTo(
        section,
        {{ opacity: 0.88, y: 20 }},
        {{
          opacity: 1,
          y: 0,
          ease: "none",
          scrollTrigger: {{
            scroller: scroller,
            trigger: section,
            start: "top 92%",
            end: "top 55%",
            scrub: 0.4
          }}
        }}
      );
    }});

    gsap.fromTo(
      ".hero-inner",
      {{ opacity: 1, y: 0 }},
      {{
        opacity: 0.55,
        y: -36,
        ease: "none",
        scrollTrigger: {{
          scroller: scroller,
          trigger: ".hero",
          start: "top top",
          end: "bottom top",
          scrub: 0.5
        }}
      }}
    );

    gsap.to(".page-bg", {{
      y: 72,
      ease: "none",
      scrollTrigger: {{
        scroller: scroller,
        trigger: document.body,
        start: "top top",
        end: "bottom bottom",
        scrub: 0.45
      }}
    }});

    gsap.to(".hero-glow", {{
      y: 48,
      opacity: 0.35,
      ease: "none",
      scrollTrigger: {{
        scroller: scroller,
        trigger: ".hero",
        start: "top top",
        end: "bottom top",
        scrub: true
      }}
    }});

    syncFrameHeight();
    ScrollTrigger.refresh();
  }}

  document.querySelectorAll("[data-modal]").forEach(function (btn) {{
    btn.addEventListener("click", function (e) {{
      e.preventDefault();
      openModal(btn.getAttribute("data-modal"));
    }});
  }});

  document.querySelectorAll("[data-close]").forEach(function (el) {{
    el.addEventListener("click", function () {{
      closeModal(el.getAttribute("data-close"));
    }});
  }});

  document.querySelectorAll("[data-external]").forEach(function (el) {{
    el.addEventListener("click", function (e) {{
      e.preventDefault();
      trackEvent("apply_click");
      openExternal(el.getAttribute("data-external"));
    }});
  }});

  document.querySelectorAll('a[href="#faq"]').forEach(function (el) {{
    el.addEventListener("click", function () {{
      trackEvent("faq_click");
    }});
  }});

  document.addEventListener("keydown", function (e) {{
    if (e.key !== "Escape") return;
    document.querySelectorAll(".modal.is-open").forEach(function (m) {{
      closeModal(m.id);
    }});
  }});

  injectShell();
  if (!sessionStorage.getItem("dgt_pv")) {{
    sessionStorage.setItem("dgt_pv", "1");
    trackEvent("page_view");
  }}
  function boot() {{
    syncFrameHeight();
    initMotion();
    setTimeout(syncFrameHeight, 120);
    setTimeout(syncFrameHeight, 600);
  }}
  if (document.readyState === "complete") {{
    boot();
  }} else {{
    window.addEventListener("load", boot, {{ once: true }});
  }}
  window.addEventListener("resize", syncFrameHeight);
  if (window.ResizeObserver) {{
    new ResizeObserver(syncFrameHeight).observe(document.body);
  }}
  document.querySelectorAll("details").forEach(function (el) {{
    el.addEventListener("toggle", syncFrameHeight);
  }});
}})();
</script>
</body></html>"""


def render_landing_page(logo_uri: str) -> None:
    """공개 랜딩. 관리자 미리보기(?view=landing + 로그인)일 때만 하단 네비."""
    from utils.admin_route import admin_entry_path, is_landing_preview_route

    shell_css = _read_css(_SHELL_CSS_PATH)
    page_css = _read_css(_PAGE_CSS_PATH)
    preview = is_landing_preview_route() and bool(st.session_state.get("auth_user"))

    components.html(
        _landing_html(logo_uri, APPLICATION_FORM_URL, page_css, shell_css, shell_preview=preview),
        height=LANDING_IFRAME_HEIGHT,
        scrolling=False,
    )

    if not preview:
        return

    st.markdown('<div class="lnd-footer-nav lnd-footer-nav--preview">', unsafe_allow_html=True)
    st.link_button("← 관리자 대시보드", admin_entry_path(), use_container_width=True)
    st.caption("신청자에게 보이는 공개 페이지입니다.")
    st.markdown("</div>", unsafe_allow_html=True)
