/**
 * 단골팅 — Google Sheets → 텔레그램
 *
 * ★ 3단계만 하면 됩니다 (트리거 UI 건드릴 필요 없음)
 * 1. setupTelegram()  — token · chat_id
 * 2. installTriggers() — 알림 켜기 (이걸 안 하면 폼 제출해도 알림 없음!)
 * 3. testTelegramPing() — 테스트
 *
 * 시트 메뉴 「단골팅 알림」에서도 실행 가능 (새로고침 후 보임)
 */
const COL = {
  TS: 1,
  NAME: 2,
  CONTACT: 4,
  JOB: 5,
  REGION: 6,
  PAID: 21,
};

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('단골팅 알림')
    .addItem('1. 토큰 설정', 'setupTelegram')
    .addItem('2. 트리거 설치 ★필수', 'installTriggers')
    .addItem('3. 연동 테스트', 'testTelegramPing')
    .addItem('4. 마지막 행 알림 테스트', 'testLastRowNotify')
    .addToUi();
}

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
  ui.alert(
    '토큰 저장됨.\n\n'
    + '다음: installTriggers() 실행 ★\n'
    + '(함수 선택 → installTriggers → 실행)\n\n'
    + '이걸 해야 폼 제출·입금 체크 알림이 동작합니다.'
  );
}

/** ★ 트리거 UI 대신 이 함수 1번 실행 */
function installTriggers() {
  const ss = SpreadsheetApp.getActive();
  ScriptApp.getProjectTriggers().forEach(function (t) {
    const fn = t.getHandlerFunction();
    if (fn === 'onFormSubmit' || fn === 'onEdit') {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger('onFormSubmit')
    .forSpreadsheet(ss)
    .onFormSubmit()
    .create();
  ScriptApp.newTrigger('onEdit')
    .forSpreadsheet(ss)
    .onEdit()
    .create();
  SpreadsheetApp.getUi().alert(
    '트리거 설치 완료!\n\n'
    + '· 구글 폼 제출 → 즉시 알림\n'
    + '· U열 입금 체크 → 💰 알림\n\n'
    + '이 스프레드시트에 연결된 폼으로 테스트해 보세요.'
  );
}

function sendTelegram_(text) {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('TELEGRAM_BOT_TOKEN');
  const chatId = props.getProperty('TELEGRAM_CHAT_ID');
  if (!token || !chatId) {
    throw new Error('토큰 없음 — setupTelegram() 먼저 실행하세요.');
  }
  const resp = UrlFetchApp.fetch(
    'https://api.telegram.org/bot' + token + '/sendMessage',
    {
      method: 'post',
      payload: {
        chat_id: chatId,
        text: text,
        disable_web_page_preview: true,
      },
      muteHttpExceptions: true,
    }
  );
  if (resp.getResponseCode() !== 200) {
    throw new Error('Telegram 오류: ' + resp.getContentText());
  }
}

function cell_(sheet, row, col) {
  const v = sheet.getRange(row, col).getDisplayValue();
  return v ? String(v).trim() : '—';
}

function pickNamed_(namedValues, keys) {
  if (!namedValues) return '—';
  for (let i = 0; i < keys.length; i++) {
    const k = keys[i];
    if (namedValues[k] && namedValues[k][0]) {
      return String(namedValues[k][0]).trim();
    }
  }
  const allKeys = Object.keys(namedValues);
  for (let i = 0; i < keys.length; i++) {
    for (let j = 0; j < allKeys.length; j++) {
      if (allKeys[j].indexOf(keys[i]) >= 0 && namedValues[allKeys[j]][0]) {
        return String(namedValues[allKeys[j]][0]).trim();
      }
    }
  }
  return '—';
}

function formatFromEvent_(e, sheet, row) {
  const nv = e && e.namedValues ? e.namedValues : null;
  if (nv) {
    const paidRaw = pickNamed_(nv, ['입금', 'paid']);
    const paid =
      paidRaw === 'TRUE' || paidRaw === 'true' || paidRaw === '✓';
    const paidTxt = paid ? '✅ 입금 확인' : '⏳ 입금 대기';
    return [
      '🆕 단골팅 새 신청',
      '이름: ' + pickNamed_(nv, ['성함', '이름', 'Name']),
      '연락: ' + pickNamed_(nv, ['연락', '전화', 'phone']),
      '직군: ' + pickNamed_(nv, ['직군', '메인']),
      '지역: ' + pickNamed_(nv, ['지역', '거주', '활동']),
      '신청: ' + pickNamed_(nv, ['타임스탬프', '시간', 'Timestamp']),
      paidTxt,
    ].join('\n');
  }
  return formatNewApplicant_(sheet, row);
}

function formatNewApplicant_(sheet, row) {
  const paid = sheet.getRange(row, COL.PAID).getValue();
  const paidTxt =
    paid === true || String(paid).toUpperCase() === 'TRUE'
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

/** installTriggers()로 등록 — 폼 제출 시 (수동 실행 불가) */
function onFormSubmit(e) {
  try {
    const sheet = e.range.getSheet();
    const row = e.range.getRow();
    if (row <= 1) return;
    sendTelegram_(formatFromEvent_(e, sheet, row));
  } catch (err) {
    Logger.log(err);
  }
}

/** installTriggers()로 등록 — U열 입금 체크 */
function onEdit(e) {
  try {
    if (!e || !e.range) return;
    const sheet = e.range.getSheet();
    const row = e.range.getRow();
    const col = e.range.getColumn();
    if (row <= 1 || col !== COL.PAID) return;
    const val = e.value;
    if (val !== true && String(val || '').toUpperCase() !== 'TRUE') return;
    sendTelegram_([
      '💰 입금 확인됨',
      '이름: ' + cell_(sheet, row, COL.NAME),
      '연락: ' + cell_(sheet, row, COL.CONTACT),
      '직군: ' + cell_(sheet, row, COL.JOB),
      '행: ' + row,
    ].join('\n'));
  } catch (err) {
    Logger.log(err);
  }
}

function testTelegramPing() {
  sendTelegram_('✅ 단골팅 Apps Script 연동 테스트');
  SpreadsheetApp.getUi().alert('텔레그램으로 테스트 메시지를 보냈습니다.');
}

/** 폼 없이 마지막 데이터 행으로 알림 테스트 */
function testLastRowNotify() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const row = sheet.getLastRow();
  if (row <= 1) {
    SpreadsheetApp.getUi().alert('시트에 데이터 행이 없습니다.');
    return;
  }
  sendTelegram_(formatNewApplicant_(sheet, row));
  SpreadsheetApp.getUi().alert('마지막 행(' + row + ') 내용으로 알림을 보냈습니다.');
}
