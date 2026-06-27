/**
 * 단골팅 — Google Sheets 텔레그램 알림
 *
 * 설치:
 * 1. 스프레드시트 → 확장 프로그램 → Apps Script
 * 2. 이 파일 붙여넣기 → setupTelegram() 1회 실행 (토큰·chat_id 입력)
 * 3. 트리거 추가:
 *    - onFormSubmit (폼에서 새 행)
 *    - onEdit (U열 입금 체크)
 *
 * 열 번호는 시트 구조에 맞게 COL 아래 숫자만 수정하세요.
 */
const COL = {
  TS: 1,       // A 타임스탬프
  NAME: 2,     // B 이름/성함
  CONTACT: 4,  // D 연락처
  JOB: 5,      // E 직군
  REGION: 6,   // F 지역
  PAID: 21,    // U 입금확인
};

function setupTelegram() {
  const ui = SpreadsheetApp.getUi();
  const token = ui.prompt('Telegram bot_token').getResponseText().trim();
  const chatId = ui.prompt('Telegram chat_id').getResponseText().trim();
  if (!token || !chatId) {
    ui.alert('bot_token과 chat_id가 필요합니다.');
    return;
  }
  PropertiesService.getScriptProperties().setProperties({
    TELEGRAM_BOT_TOKEN: token,
    TELEGRAM_CHAT_ID: chatId,
  });
  ui.alert('저장됐습니다. 이제 트리거(onFormSubmit, onEdit)를 추가하세요.');
}

function sendTelegram_(text) {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('TELEGRAM_BOT_TOKEN');
  const chatId = props.getProperty('TELEGRAM_CHAT_ID');
  if (!token || !chatId) return;
  UrlFetchApp.fetch('https://api.telegram.org/bot' + token + '/sendMessage', {
    method: 'post',
    payload: {
      chat_id: chatId,
      text: text,
      disable_web_page_preview: true,
    },
    muteHttpExceptions: true,
  });
}

function cell_(sheet, row, col) {
  const v = sheet.getRange(row, col).getDisplayValue();
  return v ? String(v).trim() : '—';
}

function formatNewApplicant_(sheet, row) {
  const paid = sheet.getRange(row, COL.PAID).getValue();
  const paidTxt = paid === true || String(paid).toUpperCase() === 'TRUE'
    ? '✅ 입금 확인'
    : '⏳ 입금 대기';
  return [
    '🆕 단골팅 새 신청',
    '이름: ' + cell_(sheet, row, COL.NAME),
    '연락: ' + cell_(sheet, row, COL.CONTACT),
    '직군: ' + cell_(sheet, row, COL.JOB),
    '지역: ' + cell_(sheet, row, COL.REGION),
    '신청: ' + cell_(sheet, row, COL.TS),
    paidTxt,
  ].join('\n');
}

/** 폼 제출 트리거 — 시트에 행이 추가될 때 */
function onFormSubmit(e) {
  try {
    const sheet = e.range.getSheet();
    const row = e.range.getRow();
    if (row <= 1) return;
    sendTelegram_(formatNewApplicant_(sheet, row));
  } catch (err) {
    console.error(err);
  }
}

/** 편집 트리거 — U열 입금 체크 시 */
function onEdit(e) {
  try {
    if (!e || !e.range) return;
    const sheet = e.range.getSheet();
    const row = e.range.getRow();
    const col = e.range.getColumn();
    if (row <= 1 || col !== COL.PAID) return;
    const val = e.value;
    if (val !== true && String(val || '').toUpperCase() !== 'TRUE') return;
    const name = cell_(sheet, row, COL.NAME);
    sendTelegram_([
      '💰 입금 확인됨',
      '이름: ' + name,
      '연락: ' + cell_(sheet, row, COL.CONTACT),
      '직군: ' + cell_(sheet, row, COL.JOB),
      '행: ' + row,
    ].join('\n'));
  } catch (err) {
    console.error(err);
  }
}

/** 수동 테스트 */
function testTelegramPing() {
  sendTelegram_('✅ 단골팅 Apps Script 연동 테스트');
}
