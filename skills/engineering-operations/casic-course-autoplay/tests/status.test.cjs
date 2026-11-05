const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../scripts/status.js'), 'utf8');
function probe({ href = 'https://example.invalid/#/study/course/detail/1', hash = '#/study/course/detail/1', body = '课程', video = null, ap = null, stored = {}, cards = [] } = {}) {
  return JSON.parse(vm.runInNewContext(source, {
    location: { href, hash }, window: { __ap: ap },
    localStorage: { getItem: key => JSON.stringify(stored[key] || null) },
    document: { body: { innerText: body }, querySelector: () => video,
      querySelectorAll: selector => selector === '.s-info-right' ? cards : [] }
  }));
}
test('blank page requests reopening', () => {
  const result = probe({ href: 'about:blank', hash: '', body: '' });
  assert.equal(result.page, 'blank');
  assert.equal(result.action, 'reopen');
});
test('stored heartbeat cannot keep a refreshed controller alive', () => {
  const result = probe({ video: { paused: false, currentTime: 10, duration: 100, playbackRate: 1 },
    stored: { __casic_hb: { ts: Date.now(), on: true } } });
  assert.equal(result.alive, false);
  assert.equal(result.action, 'reinject');
});
test('notes page requests returning to the topic', () => {
  const result = probe({ body: '快速笔记' });
  assert.equal(result.no_video, 'notes');
  assert.equal(result.action, 'back_to_subject');
});
test('topic progress counts only completed courses', () => {
  const result = probe({ hash: '#/study/subject/detail/1', cards: [
    { innerText: '课程 必 第一课 已完成' }, { innerText: '课程 必 第二课 学习中' }
  ] });
  assert.equal(result.done_count, 1);
  assert.equal(result.total_count, 2);
  assert.equal(result.courses[1].learning, true);
});
