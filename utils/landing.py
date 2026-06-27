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

  <section class="hero hero--fullscreen">
    <div class="hero-glow"></div>
    <div class="hero-stars"></div>
    <div class="hero-inner">
      <span class="eyebrow">비즈니스 시너지 파트너 매칭 · 1기 한정 · 5만 원</span>
      <h1>내 사업을 같이 키울 수 있는<br/>파트너 <em>한 명</em>이면 됩니다</h1>
      <p class="lead">
        모임에 수십 번 나가도 진짜 파트너는 잘 생기지 않습니다.<br/>
        운영진이 직접 나서서, 내 비즈니스에 맞는 사람을 찾아 연결합니다.
      </p>
      <div class="hero-cta">
        <a href="#" data-external="{form}" class="btn btn-primary">
          <span>지금 내 사람 찾기</span>
          <span class="arrow">&rarr;</span>
        </a>
        <a href="#offer" data-scroll-to="offer" class="btn btn-outline">5만 원에 뭘 받나요?</a>
      </div>
      <p class="price-line">운영진이 못 찾으면 한 푼도 안 냅니다 · 1기 가격은 지금이 마지막</p>
    </div>
    <button class="hero-scroll-hint" data-scroll-to="hook-section" aria-label="아래로 스크롤">
      <span class="hero-scroll-label">아래로</span>
      <span class="hero-scroll-arrow">↓</span>
    </button>
  </section>

  <div class="trust-strip reveal-item" id="hook-section">
    <strong>비즈니스 시너지 중심 매칭</strong><span class="dot"></span>
    <span>운영진이 1:1로 직접 탐색</span><span class="dot"></span>
    <span>익명 프로필 보고 내가 결정</span><span class="dot"></span>
    <span>최대 2회 소개 제공 · 소개 없으면 전액 환불</span>
  </div>

  <section class="hook-panel section--alt reveal">
    <div class="hook-head reveal-item">
      <span class="hook-kicker">잠깐, 이 숫자를 보세요 ↓</span>
      <h2>아는 사람은 많아도, 비즈니스로 <em>서로 이득</em>이 되는 사람은 드뭅니다</h2>
      <p>인맥은 넓은데 막상 도움이 되는 사람은 손에 꼽죠. <strong>비즈니스 시너지가 나는 파트너 한 명</strong>이 생기면 성장 속도가 완전히 달라집니다.</p>
    </div>

    <div class="hook-flow reveal-item">
      <div class="hook-step">
        <div class="hook-step-num"><span class="count" data-count="1000" data-suffix="+">0</span></div>
        <div class="hook-step-lbl">평생 알게 되는 비즈니스 지인 수</div>
      </div>
      <div class="hook-arrow" aria-hidden="true"><span>→</span></div>
      <div class="hook-step hook-step--mid">
        <div class="hook-step-num"><span class="count" data-count="2" data-prefix="~" data-suffix="명">0</span></div>
        <div class="hook-step-lbl">1년에 새로 생기는 진짜 비즈니스 파트너</div>
      </div>
      <div class="hook-arrow" aria-hidden="true"><span>→</span></div>
      <div class="hook-step hook-step--hot">
        <div class="hook-step-num"><span class="count" data-count="3" data-suffix="배">0</span></div>
        <div class="hook-step-lbl">비즈니스 파트너가 생기면 달라지는 성장 속도</div>
      </div>
    </div>

    <div class="growth-chart reveal-item">
      <div class="chart-wrap">
        <div class="chart-y-label">성장 속도 →</div>
        <div class="chart-svg-container">
          <svg class="growth-svg" viewBox="0 0 480 180" preserveAspectRatio="none" aria-hidden="true">
            <defs>
              <linearGradient id="duoAreaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.28"/>
                <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/>
              </linearGradient>
              <filter id="dotBlue" x="-80%" y="-80%" width="260%" height="260%">
                <feGaussianBlur stdDeviation="4" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>
            <line x1="0" y1="40" x2="480" y2="40" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
            <line x1="0" y1="90" x2="480" y2="90" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
            <line x1="0" y1="140" x2="480" y2="140" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
            <line x1="180" y1="10" x2="180" y2="172" stroke="rgba(96,165,250,0.25)" stroke-width="1.5" stroke-dasharray="5 4"/>
            <path class="chart-area-duo" d="M 0,165 C 70,163 130,158 180,148 C 265,108 380,20 480,3 L480,172 L0,172 Z" fill="url(#duoAreaGrad)" opacity="0"/>
            <path class="chart-path-solo" d="M 0,165 C 160,163 310,158 480,138" fill="none" stroke="#475569" stroke-width="2.5" stroke-linecap="round"/>
            <path class="chart-path-duo" d="M 0,165 C 70,163 130,158 180,148 C 265,108 380,20 480,3" fill="none" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>
            <circle class="chart-dot-solo" cx="480" cy="138" r="5" fill="#64748b" opacity="0"/>
            <circle class="chart-dot-duo" cx="480" cy="3" r="6" fill="#60a5fa" opacity="0" filter="url(#dotBlue)"/>
            <text x="185" y="142" font-size="10.5" fill="rgba(96,165,250,0.75)" font-family="Pretendard,Apple SD Gothic Neo,sans-serif" font-weight="700">↗ 단골 연결</text>
          </svg>
          <div class="chart-end-labels">
            <span class="chart-end-duo">단골팅</span>
            <span class="chart-end-solo">혼자</span>
          </div>
        </div>
        <div class="chart-x-labels">
          <span>지금</span>
          <span>6개월 후</span>
        </div>
      </div>
      <div class="chart-legend">
        <span class="leg-item leg-solo"><span class="leg-line"></span>혼자 할 때</span>
        <span class="leg-item leg-duo"><span class="leg-line"></span>단골 한 명 생긴 후</span>
      </div>
    </div>

    <a href="#offer" data-scroll-to="offer" class="hook-cta reveal-item" style="margin-top:32px">
      <span>그래서, 5만 원에 뭘 받나요?</span>
      <span class="hook-cta-arrow">→</span>
    </a>
  </section>

  <section class="founder-section reveal">
    <div class="founder-card reveal-item">
      <div class="founder-quote-mark" aria-hidden="true">&ldquo;</div>
      <div class="founder-body">
        <p class="founder-story">
          저도 오프라인 모임을 수십 번 나갔습니다.<br/>
          목적은 하나였어요. <em>&ldquo;나랑 비즈니스로 시너지가 나는 사람을 만날 수 있을까?&rdquo;</em>
        </p>
        <p class="founder-story">
          하지만 대부분은 명함만 바꾸고 끝났습니다.<br/>
          가끔 괜찮아 보이는 분을 만나도 — 서로 뭘 원하는지 확인하고, 의견 조율하고,<br/>
          실제로 도움이 되는지 검증하는 과정이 너무 피곤했어요.
        </p>
        <p class="founder-story founder-story--highlight">
          그런데 저는 그 과정이 <strong>재밌었습니다.</strong><br/>
          사람을 읽고, 비즈니스 맥락을 파악하고, 누가 누구에게 어떤 가치를 줄 수 있는지 찾는 게 — 저한테는 놀이예요.
        </p>
        <p class="founder-story">
          &ldquo;남들이 힘들어하는 걸 내가 즐긴다면 — 내가 하면 되잖아.&rdquo;<br/>
          그래서 단골팅을 만들었습니다.
        </p>
        <p class="founder-story">
          저는 실제로 단골을 만드는 걸 좋아하고, 비즈니스 관계에서 사람을 보는 눈이 쌓여 있습니다.<br/>
          당신의 상황과 필요를 파악해, 실질적으로 이득이 되는 파트너를 제가 직접 찾겠습니다.
        </p>
        <div class="founder-sig">
          <div class="founder-sig-name">이주환</div>
          <div class="founder-sig-title">단골팅 CEO · 비즈니스 단골 수집가</div>
        </div>
      </div>
    </div>
  </section>

  <section class="section reveal">
    <div class="section-head reveal-item">
      <h2>어떤 비즈니스 파트너를 만나나요?</h2>
      <p>직업이 같을 필요 없습니다. <strong>서로에게 실질적 가치를 줄 수 있으면</strong> 됩니다</p>
    </div>
    <div class="meet-grid">
      <div class="meet-card reveal-item">
        <span class="icon-chip">협</span>
        <div>
          <h3>실질적으로 협업할 파트너</h3>
          <p>내가 잘하는 것 + 상대가 잘하는 것이 맞물려, 둘 다 더 큰 결과물을 만드는 사이.</p>
        </div>
      </div>
      <div class="meet-card reveal-item">
        <span class="icon-chip">피</span>
        <div>
          <h3>비즈니스 피드백 파트너</h3>
          <p>"좋아요" 대신 "이건 왜 이렇게 했어요?"를 물어봐 줄, 성장에 직접 도움이 되는 관점.</p>
        </div>
      </div>
      <div class="meet-card reveal-item">
        <span class="icon-chip">멘</span>
        <div>
          <h3>먼저 가 본 멘토 혹은 멘티</h3>
          <p>내가 막힌 길을 이미 지나온 사람. 또는 내 경험을 필요로 하는 사람. 둘 다 이득입니다.</p>
        </div>
      </div>
      <div class="meet-card reveal-item">
        <span class="icon-chip">레</span>
        <div>
          <h3>서로 고객을 소개하는 레퍼럴</h3>
          <p>내 고객이 상대에게 필요하고, 상대 고객이 나에게 필요한 — 비즈니스 이익이 일치하는 관계.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="target-section reveal">
    <div class="section-head reveal-item">
      <h2>이런 분께 맞습니다</h2>
      <p>비즈니스 목적이 분명한 분만 신청해 주세요</p>
    </div>
    <div class="target-grid reveal-item">
      <div class="target-chip">
        <span class="target-icon">💼</span>
        <span>프리랜서 · 1인 사업자</span>
      </div>
      <div class="target-chip">
        <span class="target-icon">🚀</span>
        <span>스타트업 창업자 · 사이드프로젝트 운영자</span>
      </div>
      <div class="target-chip">
        <span class="target-icon">📈</span>
        <span>직장인이지만 부업·외부 협업 원하는 분</span>
      </div>
      <div class="target-chip">
        <span class="target-icon">🎯</span>
        <span>특정 업종에서 레퍼럴 파트너가 필요한 분</span>
      </div>
      <div class="target-chip target-chip--no">
        <span class="target-icon">✗</span>
        <span>단순 친목·소개팅·일상적 친구 찾기</span>
      </div>
    </div>
  </section>

  <section class="section section--alt reveal">
    <div class="section-head reveal-item">
      <h2>아무나 연결하지 않습니다</h2>
      <p>비즈니스 시너지가 나야 하니까 — 운영진이 세 가지를 먼저 봅니다</p>
    </div>
    <div class="card-grid-3">
      <div class="value-card reveal-item">
        <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg></div>
        <div class="num">01</div>
        <h3>비즈니스로 줄 수 있는 게 있는 사람</h3>
        <p>"인맥 넓히고 싶어요"는 거릅니다. 상대에게 실질적 가치를 줄 수 있는 분만 연결합니다.</p>
      </div>
      <div class="value-card reveal-item">
        <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg></div>
        <div class="num">02</div>
        <h3>지금 뭐가 필요한지 또렷한 사람</h3>
        <p>막연히 "좋은 사람"이 아니라, 어떤 협업·피드백·레퍼럴이 필요한지 구체적으로 아는 분.</p>
      </div>
      <div class="value-card reveal-item">
        <div class="icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg></div>
        <div class="num">03</div>
        <h3>단골처럼 오래 볼 사람</h3>
        <p>한 번 거래로 끝나는 관계가 아니라, 서로의 성장이 장기적으로 이어지는 단골 관계를 원하는 분.</p>
      </div>
    </div>
  </section>

  <section class="section reveal" id="process">
    <div class="section-head reveal-item">
      <h2>신청하면, 이렇게 진행됩니다</h2>
      <p>복잡한 거 없습니다. 신청서만 쓰면 나머지는 운영진이 합니다</p>
    </div>
    <div class="timeline">
      <div class="timeline-step reveal-item">
        <div class="circle">01</div>
        <div class="step-content"><b class="step-label">신청서 작성</b><span class="step-sub">5분이면 충분, 솔직하게만</span></div>
      </div>
      <div class="timeline-step reveal-item">
        <div class="circle">02</div>
        <div class="step-content"><b class="step-label">운영진이 직접 찾기</b><span class="step-sub">나와 맞는 사람 탐색 · 14일</span></div>
      </div>
      <div class="timeline-step reveal-item">
        <div class="circle">03</div>
        <div class="step-content"><b class="step-label">프로필 먼저 확인</b><span class="step-sub">익명 카드 보고 내가 결정</span></div>
      </div>
      <div class="timeline-step reveal-item">
        <div class="circle">04</div>
        <div class="step-content"><b class="step-label">1:1 단톡 연결</b><span class="step-sub">서로 좋으면 바로 대화 시작</span></div>
      </div>
    </div>
  </section>

  <section class="section section--alt reveal">
    <div class="section-head reveal-item">
      <h2>모임만 나가선 원하는 사람 못 만납니다</h2>
      <p>그 시간에 매칭이 되면 훨씬 낫습니다</p>
    </div>
    <div class="vs-table reveal-item">
      <div class="vs-col vs-col--old">
        <div class="vs-col-head">
          <span class="vs-badge vs-badge--old">일반 모임·네트워킹</span>
        </div>
        <ul class="vs-list">
          <li>
            <span class="vs-icon vs-icon--bad">✗</span>
            <div><strong>직접 찾아다녀야</strong><span>시간 내서 가고, 사람 걸러내고, 또 가고</span></div>
          </li>
          <li>
            <span class="vs-icon vs-icon--bad">✗</span>
            <div><strong>만나도 아이스브레이킹에 1시간</strong><span>뭘 원하는지조차 모르고 헤어짐</span></div>
          </li>
          <li>
            <span class="vs-icon vs-icon--bad">✗</span>
            <div><strong>수십 명 스쳐도 남는 사람 0</strong><span>명함은 쌓이는데, 연락 가는 사람은 없음</span></div>
          </li>
          <li>
            <span class="vs-icon vs-icon--bad">✗</span>
            <div><strong>돈·시간 둘 다 날림</strong><span>참가비에 교통비, 매번 쓰는데 뭐가 남나요</span></div>
          </li>
        </ul>
      </div>
      <div class="vs-divider" aria-hidden="true"><span>VS</span></div>
      <div class="vs-col vs-col--new">
        <div class="vs-col-head">
          <span class="vs-badge vs-badge--new">단골팅</span>
        </div>
        <ul class="vs-list">
          <li>
            <span class="vs-icon vs-icon--ok">✓</span>
            <div><strong>운영진이 대신 찾아줌</strong><span>신청서만 쓰면, 맞는 사람이 연결됨</span></div>
          </li>
          <li>
            <span class="vs-icon vs-icon--ok">✓</span>
            <div><strong>첫 대화부터 본론</strong><span>서로 뭘 원하는지 알고 만나니 깊어짐</span></div>
          </li>
          <li>
            <span class="vs-icon vs-icon--ok">✓</span>
            <div><strong>딱 한 명, 정확하게</strong><span>100명 스치지 않아도 됩니다</span></div>
          </li>
          <li>
            <span class="vs-icon vs-icon--ok">✓</span>
            <div><strong>소개 없으면 전액 환불</strong><span>1회도 못 소개하면 5만 원 그대로</span></div>
          </li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section reveal" id="offer">
    <div class="offer-box reveal-item">
      <div class="offer-badge">1기 한정 제안</div>
      <h2 class="offer-title">단돈 <em>5만 원</em>에,<br/>당신의 단골 한 명</h2>
      <p class="offer-sub">받을 건 다 받고, 못 만나면 한 푼도 안 냅니다.</p>

      <ul class="offer-list">
        <li><span class="offer-check">✓</span><span>운영진이 <b>직접</b> 신청서 읽고 맞는 사람 찾기 (14일 밀착)</span></li>
        <li><span class="offer-check">✓</span><span>상대 <b>익명 프로필 카드</b> 먼저 확인 후 내가 결정</span></li>
        <li><span class="offer-check">✓</span><span>최대 <b>2회 소개</b> 제공 — 1회씩 단계 진행</span></li>
        <li><span class="offer-check">✓</span><span>서로 좋으면 <b>1:1 단톡방</b> 바로 개설·연결</span></li>
        <li><span class="offer-check">✓</span><span>소개 1회도 못 받으면 <b>5만 원 전액 환불</b></span></li>
      </ul>

      <div class="offer-price">
        <span class="offer-price-old">보통 이런 1:1 큐레이션은 수십만 원</span>
        <span class="offer-price-now">1기는 단돈 <b>{fee}</b></span>
        <span class="offer-price-risk">못 만나면 → <b>0원</b></span>
      </div>

      <a href="#" data-external="{form}" class="btn btn-primary offer-cta">
        <span>지금 신청하고 내 사람 찾기</span>
        <span class="arrow">&rarr;</span>
      </a>
      <p class="offer-fine">잃을 게 없습니다. 소개받으면 가능성, 소개도 못 받으면 전액 환불.</p>
    </div>
  </section>

  <section class="section reveal">
    <div class="section-head reveal-item">
      <h2>먼저 만나 본 사람들</h2>
      <p>1기 참가자들이 직접 남긴 이야기</p>
    </div>
    <div class="review-grid">
      <div class="review-card reveal-item">
        <div class="review-meta">2026.06 · 마케팅 디렉터</div>
        <p>&ldquo;첫 만남부터 바로 실무 이야기로 들어갔어요. 명함만 주고받던 모임이랑은 아예 달랐습니다.&rdquo;</p>
        <div class="stars">★★★★★</div>
      </div>
      <div class="review-card reveal-item">
        <div class="review-meta">2026.06 · 프리랜서 디자이너</div>
        <p>&ldquo;나랑 잘 맞는 사람을 딱 찾아 주셔서, 시간 낭비 없이 깊은 얘기까지 갔고 결국 같이 일하게 됐어요.&rdquo;</p>
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
        <summary>외모나 나이도 보나요?</summary>
        <p>아닙니다. <strong>지금 뭐가 필요한지, 서로 뭘 주고받을 수 있는지</strong>만 봅니다. 진지하게 내 사람을 찾는 분만 받습니다.</p>
      </details>
      <details class="faq reveal-item">
        <summary>환불은 어떻게 되나요?</summary>
        <p>운영진은 최대 <strong>2회 소개</strong>를 제공합니다. <strong>소개를 1회도 못 받으면 전액 환불</strong>, 1회 소개받으면 <strong>50% 환불</strong>, 2회 소개 모두 받으면 환불 없음입니다. (자세한 내용은 아래 환불 규정 확인)</p>
      </details>
      <details class="faq reveal-item">
        <summary>신청서는 어떻게 쓰나요?</summary>
        <p><strong>[지금 내 상황] + [받고 싶은 것] + [내가 줄 수 있는 것]</strong>, 이 세 가지만 솔직하게 적으면 됩니다. 구체적일수록 더 잘 맞는 사람을 만납니다.</p>
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
    <h2 class="reveal-item">계속 혼자 버틸 건가요?</h2>
    <p class="reveal-item">
      못 만나면 돌려받고, 만나면 평생 갈 사람을 얻습니다. 잃을 게 없는 만남입니다.<br/>
      <strong style="color:#f1f5f9">1기 가격은 지금이 마지막</strong>입니다. 다음엔 이 가격으로 못 들어옵니다.
    </p>
    <a href="#" data-external="{form}" class="btn btn-primary reveal-item">
      <span>지금 신청하고 내 사람 찾기</span>
      <span class="arrow">&rarr;</span>
    </a>
    <p class="price-line" style="margin-top:16px">1기 한정 {fee} · 소개 없으면 전액 환불</p>
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
      <a href="https://open.kakao.com/me/dangolgrow" data-external-raw="https://open.kakao.com/me/dangolgrow" class="footer-link-kakao">카카오로 문의하기</a>
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
        <h4>소개 횟수별 환불 기준</h4>
        <p>운영진은 신청자에게 최대 <b>2회 소개</b>를 제공합니다. 소개 횟수에 따라 환불 기준이 달라집니다.</p>
        <ul style="margin: 10px 0 10px 16px; line-height: 1.9; font-size: 14px; color: #94a3b8;">
          <li><b style="color:#f1f5f9">소개 0회</b> (운영진이 소개를 못 해드린 경우) → 참가비 <b style="color:#f1f5f9">전액 환불</b></li>
          <li><b style="color:#f1f5f9">소개 1회</b> 제공받은 경우 → 참가비의 <b style="color:#f1f5f9">50% 환불</b></li>
          <li><b style="color:#f1f5f9">소개 2회</b> 모두 제공받은 경우 → 기회 소진, <b style="color:#f1f5f9">환불 없음</b></li>
        </ul>
        <p>소개받은 프로필이 맞지 않더라도 소개 제공 자체가 이루어진 경우에는 위 기준이 적용됩니다. 1:1 단톡방 개설 이후에는 환불이 불가합니다. 조율 과정에 적극적으로 협조 부탁드립니다.</p>
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

  function scrollParentTo(id) {{
    try {{
      var el = document.getElementById(id);
      if (!el) return;
      var rect = el.getBoundingClientRect();
      var frameRect = window.frameElement ? window.frameElement.getBoundingClientRect() : {{ top: 0 }};
      var scr = getParentScroller();
      var currentTop = (scr === window.parent.document.documentElement || scr === window.parent.document.body)
        ? (window.parent.scrollY || 0) : scr.scrollTop;
      var targetY = currentTop + frameRect.top + rect.top - 80;
      if (scr === window.parent.document.documentElement || scr === window.parent.document.body) {{
        window.parent.scrollTo({{ top: targetY, behavior: "smooth" }});
      }} else {{
        scr.scrollTo({{ top: targetY, behavior: "smooth" }});
      }}
    }} catch (e) {{}}
  }}

  function injectFAB() {{
    try {{
      var pdoc = window.parent.document;
      var existing = pdoc.getElementById("dgt-fab-top");
      if (existing) existing.remove();
      var existingStyle = pdoc.getElementById("dgt-fab-style");
      if (existingStyle) existingStyle.remove();

      var styleEl = pdoc.createElement("style");
      styleEl.id = "dgt-fab-style";
      styleEl.textContent = [
        "#dgt-fab-top{{position:fixed;bottom:28px;right:24px;width:46px;height:46px;border-radius:50%;",
        "background:rgba(15,22,42,0.92);border:1px solid rgba(96,165,250,0.4);color:#93c5fd;",
        "display:flex;align-items:center;justify-content:center;cursor:pointer;",
        "backdrop-filter:blur(12px);box-shadow:0 8px 28px rgba(0,0,0,0.45);",
        "opacity:0;transform:translateY(12px);transition:opacity .3s,transform .3s;",
        "pointer-events:none;z-index:9999;}}",
        "#dgt-fab-top svg{{width:20px;height:20px;stroke-width:2.5;stroke-linecap:round;}}",
        "#dgt-fab-top.dgt-fab-visible{{opacity:1;transform:translateY(0);pointer-events:auto;}}",
        "#dgt-fab-top:hover{{background:rgba(25,38,72,0.96);border-color:rgba(96,165,250,0.65);}}"
      ].join("");
      pdoc.head.appendChild(styleEl);

      var fab = pdoc.createElement("button");
      fab.id = "dgt-fab-top";
      fab.setAttribute("aria-label", "맨 위로");
      fab.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="18 15 12 9 6 15"/></svg>';
      pdoc.body.appendChild(fab);
      fab.addEventListener("click", scrollParentToTop);

      var scr = getParentScroller();
      function updateFAB() {{
        var top = (scr === pdoc.documentElement || scr === pdoc.body)
          ? window.parent.scrollY : scr.scrollTop;
        if (top > 320) fab.classList.add("dgt-fab-visible");
        else fab.classList.remove("dgt-fab-visible");
      }}
      scr.addEventListener("scroll", updateFAB, {{ passive: true }});
      window.parent.addEventListener("scroll", updateFAB, {{ passive: true }});
    }} catch (e) {{}}
  }}

  function scrollParentToTop() {{
    try {{
      var scr = getParentScroller();
      if (scr === window.parent.document.documentElement || scr === window.parent.document.body) {{
        window.parent.scrollTo({{ top: 0, behavior: "smooth" }});
      }} else {{
        scr.scrollTo({{ top: 0, behavior: "smooth" }});
      }}
    }} catch (e) {{
      window.scrollTo({{ top: 0, behavior: "smooth" }});
    }}
  }}

  function setHeroHeight() {{
    try {{
      var vh = window.parent.innerHeight;
      var hero = document.querySelector(".hero--fullscreen");
      var header = document.querySelector(".site-header");
      var headerH = header ? header.offsetHeight : 0;
      if (hero) hero.style.minHeight = (vh - headerH) + "px";
    }} catch (e) {{
      var hero = document.querySelector(".hero--fullscreen");
      if (hero) hero.style.minHeight = "100svh";
    }}
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
    try {{
      var pwin = window.parent;
      var scr = getParentScroller();
      var scrollTop = (scr === pwin.document.documentElement || scr === pwin.document.body)
        ? pwin.scrollY : scr.scrollTop;
      el.style.top = scrollTop + "px";
      el.style.height = pwin.innerHeight + "px";
    }} catch (e) {{
      el.style.top = "0";
      el.style.height = "100vh";
    }}
    el.classList.add("is-open");
    el.setAttribute("aria-hidden", "false");
    lockParentScroll(true);
  }}

  function closeModal(id) {{
    var el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("is-open");
    el.setAttribute("aria-hidden", "true");
    el.style.top = "";
    el.style.height = "";
    lockParentScroll(false);
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
      var soloPath = document.querySelector(".chart-path-solo");
      var duoPath = document.querySelector(".chart-path-duo");
      if (soloPath) gsap.set(soloPath, {{ strokeDashoffset: 0 }});
      if (duoPath) gsap.set(duoPath, {{ strokeDashoffset: 0 }});
      document.querySelectorAll(".chart-dot-solo, .chart-dot-duo, .chart-area-duo").forEach(function (el) {{
        el.style.opacity = "1";
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

    function initGrowthChart() {{
      var soloPath = document.querySelector(".chart-path-solo");
      var duoPath = document.querySelector(".chart-path-duo");
      var areaPath = document.querySelector(".chart-area-duo");
      var dotSolo = document.querySelector(".chart-dot-solo");
      var dotDuo = document.querySelector(".chart-dot-duo");
      if (!soloPath || !duoPath) return;

      var soloLen = soloPath.getTotalLength();
      var duoLen = duoPath.getTotalLength();

      gsap.set(soloPath, {{ strokeDasharray: soloLen, strokeDashoffset: soloLen }});
      gsap.set(duoPath, {{ strokeDasharray: duoLen, strokeDashoffset: duoLen }});
      if (dotSolo) gsap.set(dotSolo, {{ opacity: 0 }});
      if (dotDuo) gsap.set(dotDuo, {{ opacity: 0 }});
      if (areaPath) gsap.set(areaPath, {{ opacity: 0 }});

      var chartEl = document.querySelector(".growth-chart");
      if (!chartEl) return;

      var tl = gsap.timeline({{
        scrollTrigger: {{
          scroller: scroller,
          trigger: chartEl,
          start: "top 82%",
          end: "top 18%",
          scrub: 0.7
        }}
      }});

      tl.to(soloPath, {{ strokeDashoffset: 0, ease: "none", duration: 1 }}, 0)
        .to(duoPath, {{ strokeDashoffset: 0, ease: "power3.in", duration: 1 }}, 0)
        .to(areaPath, {{ opacity: 1, ease: "none", duration: 0.4 }}, 0.5)
        .to(dotSolo, {{ opacity: 1, duration: 0.15 }}, 0.88)
        .to(dotDuo, {{ opacity: 1, duration: 0.15 }}, 0.92);
    }}

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

    initHookCounters();
    initGrowthChart();

    var fabTop = document.getElementById("fabTop");
    if (fabTop) {{
      fabTop.addEventListener("click", scrollParentToTop);
      ScrollTrigger.create({{
        scroller: scroller,
        trigger: ".trust-strip",
        start: "top top",
        onEnter: function () {{ fabTop.classList.add("is-visible"); }},
        onLeaveBack: function () {{ fabTop.classList.remove("is-visible"); }}
      }});
    }}

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

  document.querySelectorAll("[data-external-raw]").forEach(function (el) {{
    el.addEventListener("click", function (e) {{
      e.preventDefault();
      openExternal(el.getAttribute("data-external-raw"));
    }});
  }});

  document.querySelectorAll("[data-scroll-to]").forEach(function (el) {{
    el.addEventListener("click", function (e) {{
      e.preventDefault();
      scrollParentTo(el.getAttribute("data-scroll-to"));
    }});
  }});

  document.querySelectorAll('a[href="#faq"]').forEach(function (el) {{
    el.addEventListener("click", function (e) {{
      e.preventDefault();
      trackEvent("faq_click");
      scrollParentTo("faq");
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
    setHeroHeight();
    syncFrameHeight();
    initMotion();
    injectFAB();
    setTimeout(syncFrameHeight, 120);
    setTimeout(syncFrameHeight, 600);
    setTimeout(setHeroHeight, 200);
  }}
  if (document.readyState === "complete") {{
    boot();
  }} else {{
    window.addEventListener("load", boot, {{ once: true }});
  }}
  window.addEventListener("resize", function () {{ syncFrameHeight(); setHeroHeight(); }});
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
