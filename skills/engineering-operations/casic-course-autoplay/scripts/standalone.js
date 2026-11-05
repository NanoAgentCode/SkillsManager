#!/usr/bin/env node
/**
 * 航天云课堂 · 独立常驻刷课器（Playwright 版 v2）
 *
 * v2 相比 v1：
 *  1. 集索引优先从 URL 读（/study/course/detail/{courseId}/{epIdx}），平台本身会记位置
 *  2. 「需再学」清扫：到列表末尾不急着走，回头补播仍欠学时的集
 *  3. 切集默认 seek 到 0，确保整段有效时长都记上
 *  4. 崩溃自愈：连续异常会重启浏览器上下文，凭 state.json 续刷
 *  5. 支持 --url 直达专题，避免首页误点
 *
 * 用法：
 *   node standalone.js --user 156xxxxxxxx --pass '***' --url '<专题URL>'
 *   node standalone.js --user ... --pass ... --branch 安全学院 --subject 消防
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  if (i > -1 && process.argv[i + 1] && process.argv[i + 1].slice(0, 2) !== '--') return process.argv[i + 1];
  return def;
}
const has = (n) => process.argv.includes('--' + n);

const BASE = 'https://train.casicloud.com/app/wechat/?controlsSwitch=&company_id=STATE';
const USER = arg('user');
const PASS = arg('pass');
const BRANCH = arg('branch', '安全学院');
const SUBJECT_KEY = arg('subject', null);
const TARGET_URL = arg('url', null);
const RATE = parseFloat(arg('rate', '1.5'));
const HEADLESS = !has('headed');
const CHROME = arg('chrome', null);   // 已有 chromium 二进制时直接复用，免下载
const STATE_FILE = arg('state', path.join(__dirname, 'state.json'));
const POLL_MS = parseInt(arg('poll', '3000'), 10);
const REPORT_MS = parseInt(arg('report', String(30 * 60 * 1000)), 10);
const SWITCH_COOL = 10000;
const MAX_SWEEPS = 6;

let state = { subjectUrl: null, courseIdx: null, cool: 0, done: 0, sweeps: 0, lastReport: 0, courseKey: null };
try { state = Object.assign(state, JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'))); } catch (e) {}

const saveState = () => { try { fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2)); } catch (e) {} };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (...a) => console.log('[' + new Date().toLocaleString('zh-CN', { hour12: false }) + ']', ...a);
const mmss = (s) => String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(Math.round(s % 60)).padStart(2, '0');

/* ---------------- 探针 ---------------- */
function probe(page) {
  return page.evaluate(() => {
    const v = document.querySelector('video');
    const body = document.body.innerText || '';
    const lis = Array.from(document.querySelectorAll('.catalog-box li')).filter((li) => li.offsetParent !== null);
    const items = lis.map((li) => li.innerText.replace(/\s+/g, ' ').trim());
    const activeIdx = lis.findIndex((li) => (li.className || '').indexOf('active-section') > -1);
    const pending = [];
    lis.forEach((li, i) => { if (li.innerText.indexOf('需再学') > -1) pending.push(i); });
    return {
      hash: location.hash, hasVideo: !!v,
      paused: v ? v.paused : null, rate: v ? v.playbackRate : null,
      t: v ? v.currentTime : 0, dur: v ? v.duration : 0,
      ended: v ? v.ended : false, ready: v ? v.readyState : 0,
      items, activeIdx, pending, body,
    };
  });
}

/* ---------------- 登录 ---------------- */
async function login(page) {
  log('开始登录…');
  await page.goto(BASE + '#/login', { waitUntil: 'domcontentloaded', timeout: 45000 });
  // 页面有 6 个 input，其中 4 个是自定义键盘的隐藏镜像，必须按可见性筛选
  await page.waitForSelector('input', { state: 'attached', timeout: 25000 });
  await sleep(4000);

  const vis = page.locator('input:visible');
  if (await vis.count() < 2) throw new Error('可见输入框不足 2 个');
  await vis.nth(0).fill(USER);
  await vis.nth(1).fill(PASS);
  await sleep(400);

  // 协议勾选框是 van-checkbox，无原生 input[type=checkbox]，点 label 即可
  await page.evaluate(() => {
    const lb = document.querySelector('.van-checkbox__label') ||
      Array.from(document.querySelectorAll('span')).find((e) => e.innerText && e.innerText.indexOf('已阅读') > -1);
    if (lb) lb.click();
  });
  await sleep(400);

  await page.click('.login-btn');
  await sleep(7000);
  if ((await page.evaluate(() => location.hash)).indexOf('#/login') > -1) {
    await page.screenshot({ path: path.join(__dirname, 'login-fail.png') }).catch(() => {});
    throw new Error('登录失败，仍在 #/login');
  }
  log('登录成功');
}

/* ---------------- 分院 ---------------- */
async function switchBranch(page, name) {
  const cur = await page.textContent('.cur-branch-name').catch(() => null);
  if (cur && cur.trim() === name) return;
  log('切换分院 →', name);
  await page.click('.cur-branch-name');
  await sleep(1600);
  const ok = await page.evaluate((n) => {
    const el = Array.from(document.querySelectorAll('.nav-item')).find((e) => e.innerText.trim() === n);
    if (!el) return false;
    el.click(); return true;
  }, name);
  if (!ok) throw new Error('分院弹层无此选项: ' + name);
  await sleep(1000);
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button,div,span'))
      .filter((e) => e.children.length === 0 && e.innerText && e.innerText.trim() === '完成');
    if (b.length) b[b.length - 1].click();
  });
  await sleep(3500);
  log('分院切换完成');
}

/* ---------------- 进专题 ---------------- */
async function enterSubject(page) {
  if (TARGET_URL) {
    await page.evaluate((h) => { location.hash = h; }, TARGET_URL.replace(/^[^#]*#/, '#'));
    await sleep(5000);
    const st = await probe(page);
    if (st.hash.indexOf('/study/subject/detail/') === -1) throw new Error('直达专题失败: ' + st.hash.slice(0, 60));
    state.subjectUrl = st.hash; saveState();
    log('已进入专题:', (st.body.split('\n')[0] || '').trim());
    return;
  }
  const clicked = await page.evaluate((key) => {
    const btns = Array.from(document.querySelectorAll('*'))
      .filter((e) => e.children.length === 0 && e.innerText && e.innerText.trim() === '我要学');
    if (!btns.length) return false;
    if (key) {
      const hit = btns.find((b) => {
        let p = b;
        for (let i = 0; i < 6 && p; i++, p = p.parentElement) if (p.innerText && p.innerText.indexOf(key) > -1) return true;
        return false;
      });
      if (!hit) return false;
      hit.click(); return true;
    }
    btns[0].click(); return true;
  }, SUBJECT_KEY);
  if (!clicked) {
    const st = await probe(page);
    if (st.hash.indexOf('/study/subject/detail/') > -1) return;
    throw new Error('首页未找到「我要学」');
  }
  await sleep(5000);
  const st = await probe(page);
  if (st.hash.indexOf('/study/subject/detail/') === -1) throw new Error('进入专题失败');
  state.subjectUrl = st.hash; saveState();
  log('已进入专题:', (st.body.split('\n')[0] || '').trim());
}

/* ---------------- 工具 ---------------- */
async function clickItem(page, i, reset) {
  await page.evaluate(({ idx }) => {
    const lis = Array.from(document.querySelectorAll('.catalog-box li')).filter((li) => li.offsetParent !== null);
    if (lis[idx]) lis[idx].click();
  }, { idx: i });
  await sleep(2500);
  if (reset) {
    await page.evaluate(() => { try { const v = document.querySelector('video'); if (v && v.currentTime > 3) v.currentTime = 0; } catch (e) {} });
  }
  await page.evaluate((r) => {
    try { const v = document.querySelector('video'); if (v) { v.playbackRate = r; if (v.paused) v.play().catch(() => {}); } } catch (e) {}
  }, RATE);
}

const epFromHash = (h) => { const m = h.match(/\/study\/course\/detail\/[^/]+\/(\d+)/); return m ? parseInt(m[1], 10) : null; };
const courseFromHash = (h) => { const m = h.match(/\/study\/course\/detail\/([^/?#]+)/); return m ? m[1] : null; };

/* ---------------- 主步进 ---------------- */
async function step(page) {
  const s = await probe(page);

  if (s.hash.indexOf('#/login') > -1) { await login(page); return; }

  /* ===== 课程页 ===== */
  if (s.hash.indexOf('/study/course/detail/') > -1) {
    const cid = courseFromHash(s.hash);
    if (state.courseKey !== cid) { state.courseKey = cid; state.sweeps = 0; saveState(); }

    if (!s.hasVideo) {
      if (s.body.indexOf('其他终端') > -1) log('⚠ 多端登录提示，播放器被顶掉');
      if (state.subjectUrl) { await page.evaluate((h) => { location.hash = h; }, state.subjectUrl); await sleep(4500); }
      else { await page.reload({ waitUntil: 'domcontentloaded' }).catch(() => {}); await sleep(4000); }
      return;
    }
    if (!s.items.length) return;

    await page.evaluate((r) => {
      const v = document.querySelector('video');
      if (!v) return;
      if (Math.abs(v.playbackRate - r) > 0.01) v.playbackRate = r;
      if (v.paused && !v.ended) v.play().catch(() => {});
    }, RATE);

    let idx = s.activeIdx > -1 ? s.activeIdx : epFromHash(s.hash);
    if (idx === null || idx >= s.items.length) idx = state.courseIdx !== null ? state.courseIdx : 0;
    if (state.courseIdx !== idx) { state.courseIdx = idx; saveState(); }

    /* 停滞自愈 */
    if (Math.abs(s.t - lastT) < 0.3) stuckCount++; else stuckCount = 0;
    lastT = s.t;
    if (stuckCount >= 10) {
      stuckCount = 0;
      log('播放停滞 ' + mmss(s.t) + '，重播当前集');
      await clickItem(page, idx, false);
      state.cool = Date.now(); saveState();
      return;
    }

    /* 播完 → 下一集 / 清扫 / 离开课程 */
    const near = s.dur > 0 && s.ready > 0 && (s.dur - s.t < 1.5 || s.ended);
    if (near && Date.now() - state.cool > SWITCH_COOL) {
      state.cool = Date.now();
      stuckCount = 0;

      if (idx + 1 < s.items.length) {
        state.courseIdx = idx + 1; saveState();
        await clickItem(page, idx + 1, true);
        log('切换视频 →', idx + 2, '/', s.items.length);
        return;
      }

      const pend = s.pending.filter((i) => i !== idx);
      if (pend.length && state.sweeps < MAX_SWEEPS) {
        state.sweeps++;
        state.courseIdx = pend[0]; saveState();
        await clickItem(page, pend[0], true);
        log('↺ 回补欠学时 第', pend[0] + 1, '集（第', state.sweeps, '轮）');
        return;
      }

      log('本课程完成，回专题页');
      state.courseIdx = null; state.done += 1; saveState();
      if (state.subjectUrl) { await page.evaluate((h) => { location.hash = h; }, state.subjectUrl); await sleep(5000); }
      return;
    }
    return;
  }

  /* ===== 专题页 ===== */
  if (s.hash.indexOf('/study/subject/detail/') > -1) {
    if (state.subjectUrl !== s.hash) { state.subjectUrl = s.hash; saveState(); }
    if (Date.now() - state.cool < 6000) return;
    state.cool = Date.now();

    const r = await page.evaluate(() => {
      const items = Array.from(document.querySelectorAll('.s-info-right'));
      const rest = items.filter((el) => el.innerText.indexOf('已完成') === -1);
      if (!rest.length) return { done: true, total: items.length };
      const el = rest[0];
      const t = (el.querySelector('.c-info-title') || {}).innerText || '';
      (el.querySelector('.sub-left') || el).click();
      return { done: false, title: t.trim(), left: rest.length, total: items.length };
    });

    if (r.done) { log('✅ 专题内所有课程已完成（' + r.total + ' 门）'); process.exit(0); }
    state.courseIdx = null; state.sweeps = 0; saveState();
    log('进入课程 →', r.title, '(' + (r.total - r.left + 1) + '/' + r.total + ')');
    await sleep(5500);
    return;
  }

  /* ===== 其他页：兜底 ===== */
  if (s.hash.indexOf('/login') > -1) { await login(page); return; }
  try {
    log('页面异常 hash=' + s.hash.slice(0, 50) + '，回专题页');
    if (state.subjectUrl) { await page.goto('https://train.casicloud.com/app/wechat/?controlsSwitch=&company_id=STATE' + state.subjectUrl, { waitUntil: 'domcontentloaded', timeout: 40000 }); await sleep(5000); }
    else { await page.reload({ waitUntil: 'domcontentloaded' }).catch(() => {}); }
  } catch (e) { log('兜底异常:', e.message); }
}

/* ---------------- 启动 ---------------- */
let lastT = -1, stuckCount = 0;

async function boot(page) {
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await sleep(3500);
  if ((await page.evaluate(() => location.hash)).indexOf('#/login') > -1) await login(page);
  if (TARGET_URL) { await enterSubject(page); return; }
  try { await switchBranch(page, BRANCH); } catch (e) { log('切分院跳过:', e.message); }
  await enterSubject(page);
}

(async () => {
  if (!USER || !PASS) { console.error('缺少 --user / --pass'); process.exit(2); }
  log('启动', { HEADLESS, BRANCH, RATE, TARGET_URL: TARGET_URL ? 'yes' : 'no' });

  for (;;) {
    let browser;
    try {
      browser = await chromium.launch({
        headless: HEADLESS,
        ...(CHROME ? { executablePath: CHROME } : {}),
        args: ['--no-sandbox', '--disable-dev-shm-usage', '--autoplay-policy=no-user-gesture-required', '--mute-audio'],
      });
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
      const page = await ctx.newPage();
      page.setDefaultTimeout(30000);
      await boot(page);
      log('初始化完成，进入主循环');

      let errs = 0;
      for (;;) {
        try {
          await step(page);
          errs = 0;
        } catch (e) {
          errs++;
          log('循环异常(' + errs + '):', e.message);
          if (errs >= 6) throw new Error('连续异常过多，重启浏览器');
          await sleep(8000);
        }
        if (Date.now() - state.lastReport > REPORT_MS) {
          state.lastReport = Date.now(); saveState();
          try {
            const s = await probe(page);
            const m = s.body.match(/课程总进度\s*(\d+)%/);
            const n = s.body.match(/必修\s*(\d+)\/(\d+)/);
            log('— 进度 |' + (s.body.split('\n')[0] || '').trim().slice(0, 22) +
              '| ' + (m ? m[1] + '%' : '-') + ' | 必修 ' + (n ? n[1] + '/' + n[2] : '-') +
              ' | ' + mmss(s.t) + '/' + mmss(s.dur || 0) + ' | 已完成课程 ' + state.done +
              ' | 待补集 ' + (s.pending.length ? s.pending.join(',') : '无'));
          } catch (e) {}
        }
        await sleep(POLL_MS);
      }
    } catch (e) {
      log('❌ 浏览器层异常:', e.message, '— 10 秒后重启');
      try { if (browser) await browser.close(); } catch (e2) {}
      await sleep(10000);
    }
  }
})();
