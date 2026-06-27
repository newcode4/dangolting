/**
 * 단골팅 — Google Sheets → 텔레그램 (알림 전용)
 *
 * 1. setupTelegram()   — token · chat_id
 * 2. installTriggers() — ★ 필수 (폼 즉시 · 입금체크 · 점심 입금대기)
 * 3. testTelegramPing()
 *
 * Streamlit 앱 telegram enabled=false 권장 (중복·지연 방지)
 */
const COL = {
  TS: 1,
  NAME: 2,
  CONTACT: 4,
  JOB: 5,
  REGION: 6,
  PAID: 21,
  REFUND: 24,
};

/** 신청 후 N시간 지난 입금 대기만 점심 알림에 포함 */
const UNPAID_MIN_HOURS = 3;
/** 매일 점심 (한국 시간) */
const DIGEST_HOUR = 12;
const DIGEST_TZ = 'Asia/Seoul';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('단골팅 알림')
    .addItem('1. 토큰 설정', 'setupTelegram')
    .addItem('2. 트리거 설치 ★필수', 'installTriggers')
    .addItem('3. 연동 테스트', 'testTelegramPing')
    .addItem('4. 새 신청 테스트 (마지막 행)', 'testLastRowNotify')
    .addItem('5. 입금대기 묶음 테스트', 'testUnpaidDigest')
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
    + '다음: installTriggers() 실행 ★\n\n'
    + '· 폼 제출 → 즉시 알림\n'
    + '· U열 입금 체크 → 💰 알림\n'
    + '· 매일 ' + DIGEST_HOUR + '시 — 입금 대기 ' + UNPAID_MIN_HOURS + '시간+ 묶음 알림'
  );
}

function installTriggers() {
  const ss = SpreadsheetApp.getActive();
  ScriptApp.getProjectTriggers().forEach(function (t) {
    const fn = t.getHandlerFunction();
    if (
      fn === 'onFormSubmit' ||
      fn === 'onEdit' ||
      fn === 'sendUnpaidDailyDigest'
    ) {
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
  ScriptApp.newTrigger('sendUnpaidDailyDigest')
    .timeBased()
    .everyDays(1)
    .atHour(DIGEST_HOUR)
    .inTimezone(DIGEST_TZ)
    .create();
  SpreadsheetApp.getUi().alert(
    '트리거 설치 완료!\n\n'
    + '· 폼 제출 → 즉시 🆕 알림\n'
    + '· U열 체크 → 💰 알림\n'
    + '· 매일 ' + DIGEST_HOUR + ':00 — 입금 대기 '
    + UNPAID_MIN_HOURS + '시간+ 묶음 알림\n\n'
    + 'Streamlit 앱 telegram enabled=false 권장'
  );
}

function getFormSheet_() {
  return SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
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

function isChecked_(val) {
  return val === true || String(val || '').toUpperCase() === 'TRUE';
}

function parseDate_(val) {
  if (!val) return null;
  if (val instanceof Date && !isNaN(val.getTime())) return val;
  const d = new Date(String(val));
  return isNaN(d.getTime()) ? null : d;
}

function hoursSince_(val) {
  const d = parseDate_(val);
  if (!d) return 9999;
  return (Date.now() - d.getTime()) / 3600000;
}

function fmtTs_(val) {
  const d = parseDate_(val);
  if (!d) return String(val || '—');
  return Utilities.formatDate(d, DIGEST_TZ, 'M/d HH:mm');
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
    const paid = paidRaw === 'TRUE' || paidRaw === 'true' || paidRaw === '✓';
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
  const paidTxt = isChecked_(paid) ? '✅ 입금 확인' : '⏳ 입금 대기';
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

function collectUnpaid_(minHours) {
  const sheet = getFormSheet_();
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return [];

  const width = Math.max(COL.REFUND, COL.PAID);
  const data = sheet.getRange(2, 1, lastRow - 1, width).getValues();
  const items = [];

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    const name = row[COL.NAME - 1];
    if (!name || !String(name).trim()) continue;
    if (isChecked_(row[COL.PAID - 1])) continue;
    if (isChecked_(row[COL.REFUND - 1])) continue;
    const hours = hoursSince_(row[COL.TS - 1]);
    if (hours < minHours) continue;
    items.push({
      rowNum: i + 2,
      name: String(name).trim(),
      contact: row[COL.CONTACT - 1] ? String(row[COL.CONTACT - 1]).trim() : '—',
      job: row[COL.JOB - 1] ? String(row[COL.JOB - 1]).trim() : '—',
      region: row[COL.REGION - 1] ? String(row[COL.REGION - 1]).trim() : '—',
      ts: fmtTs_(row[COL.TS - 1]),
      hours: Math.floor(hours),
    });
  }
  return items;
}

function formatUnpaidDigest_(items) {
  const now = Utilities.formatDate(new Date(), DIGEST_TZ, 'M/d HH:mm');
  const lines = [
    '📋 입금 대기 (점심 ' + DIGEST_HOUR + '시) — ' + items.length + '명',
    '신청 ' + UNPAID_MIN_HOURS + '시간+ · U열 미체크 · ' + now,
    '',
  ];
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const jobShort = it.job.length > 18 ? it.job.substring(0, 15) + '…' : it.job;
    lines.push(
      (i + 1) + '. ' + it.name +
      ' · ' + it.contact +
      ' · ' + jobShort +
      ' · ' + it.region +
      '\n   ' + it.ts + ' (' + it.hours + 'h) · 행 ' + it.rowNum
    );
  }
  let text = lines.join('\n');
  if (text.length > 4000) {
    text = text.substring(0, 3990) + '\n…(생략)';
  }
  return text;
}

/** 매일 점심 — installTriggers()로 등록 */
function sendUnpaidDailyDigest() {
  try {
    const items = collectUnpaid_(UNPAID_MIN_HOURS);
    if (items.length === 0) return;
    sendTelegram_(formatUnpaidDigest_(items));
  } catch (err) {
    Logger.log(err);
  }
}

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

function onEdit(e) {
  try {
    if (!e || !e.range) return;
    const sheet = e.range.getSheet();
    const row = e.range.getRow();
    const col = e.range.getColumn();
    if (row <= 1 || col !== COL.PAID) return;
    const val = e.value;
    if (!isChecked_(val)) return;
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

function testLastRowNotify() {
  const sheet = getFormSheet_();
  const row = sheet.getLastRow();
  if (row <= 1) {
    SpreadsheetApp.getUi().alert('시트에 데이터 행이 없습니다.');
    return;
  }
  sendTelegram_(formatNewApplicant_(sheet, row));
  SpreadsheetApp.getUi().alert('마지막 행(' + row + ') 내용으로 알림을 보냈습니다.');
}

/** 입금 대기 묶음 미리보기 (3시간 조건 적용) */
function testUnpaidDigest() {
  const items = collectUnpaid_(UNPAID_MIN_HOURS);
  if (items.length === 0) {
    SpreadsheetApp.getUi().alert(
      '보낼 대상 없음.\n\n'
      + '입금 미체크 + 신청 ' + UNPAID_MIN_HOURS + '시간 지난 행이 있어야 합니다.'
    );
    return;
  }
  sendTelegram_(formatUnpaidDigest_(items));
  SpreadsheetApp.getUi().alert('입금 대기 ' + items.length + '명 묶음 알림을 보냈습니다.');
}
