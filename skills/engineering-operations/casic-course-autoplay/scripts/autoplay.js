/*
 * 航天云课堂 · 自动播放控制器 v5
 * 注入：agent-browser eval --stdin < scripts/autoplay.js
 *
 * v5 修正（来自 2026-11-05 实战）：
 *  1. 修复 A.on 跨课程不重置：一门课播完后 A.on 被置 false，进入下一门后一直显示"控制器已关"。
 *     现在换课/在专题页点课时强制 A.on = true。
 *  2. 处理"快速笔记"页：平台播完一门课后会跳到 #/study/course/detail/xxx（无 video、无选集列表），
 *     v4 在那里置 kicked 就傻等。v5 连续 10 秒确认"既无 video 又无选集"后自动回专题页。
 *  3. 心跳额外带 page/noVideo 字段，外部一眼看出卡在哪一类页面。
 *
 * v4 能力（保留）：
 *  - 状态按 courseId 分存，换课重置，刷新后靠 active-section 续上原集
 *  - stopAfterCourse：本课 100% 时暂停而不跳下一门
 *  - 心跳写 localStorage，外部可判断"控制器已死"
 *  - 欠学时清扫：播到末集后回跳带"需再学"的集，最多 6 轮
 *  - 倍速每 2 秒纠偏；停滞判定要求"16s 无进展且缓冲不足"
 *
 * 配置（localStorage.__casic_cfg）：
 *   { "rate": 1.5, "stopAfterCourse": false }
 */
(function () {
  var LS_CFG = '__casic_cfg';
  var LS_ST = '__casic_state';
  var LS_HB = '__casic_hb';
  var STUCK_LIMIT = 8;        // 8 × 2s = 16s
  var SWITCH_COOL = 9000;
  var MAX_SWEEPS = 6;
  var NOVIDEO_LIMIT = 5;      // 5 × 2s = 10s 确认不是加载中

  function rd(k, d) {
    try { return JSON.parse(localStorage.getItem(k)) || d; } catch (e) { return d; }
  }
  function wr(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }

  var CFG = rd(LS_CFG, {});
  var RATE = CFG.rate || 1.5;
  var STOP_AFTER = !!CFG.stopAfterCourse;

  if (window.__apTimer) { clearInterval(window.__apTimer); window.__apTimer = null; }

  function courseId() {
    var m = (location.hash || '').match(/\/study\/course\/detail\/([^/?#]+)/);
    return m ? m[1] : null;
  }
  function epFromHash() {
    var m = (location.hash || '').match(/\/study\/course\/detail\/[^/]+\/(\d+)/);
    return m ? parseInt(m[1], 10) : null;
  }

  var cid = courseId();
  var prev = rd(LS_ST, {});
  if (prev.cid !== cid) prev = { cid: cid, idx: null, switches: 0, sweeps: 0 };

  var A = window.__ap = {
    on: true, hold: false, rate: RATE, stopAfter: STOP_AFTER,
    idx: prev.idx, switches: prev.switches || 0, sweeps: prev.sweeps || 0,
    cid: cid, t: 0, lastT: -1, stuck: 0, cool: 0, noVideo: 0,
    needLogin: false, kicked: false, done: false, page: null,
    hb: Date.now()
  };

  function persist() {
    wr(LS_ST, { cid: A.cid, idx: A.idx, switches: A.switches, sweeps: A.sweeps });
  }
  function beat() {
    A.hb = Date.now();
    wr(LS_HB, {
      ts: A.hb, cid: A.cid, idx: A.idx, on: A.on, hold: A.hold, page: A.page,
      switches: A.switches, needLogin: A.needLogin, kicked: A.kicked
    });
  }

  function items() {
    return Array.prototype.slice.call(document.querySelectorAll('.catalog-box li'))
      .filter(function (li) { return li.offsetParent !== null; });
  }
  function activeIdx(lis) {
    for (var i = 0; i < lis.length; i++) {
      if ((lis[i].className || '').indexOf('active-section') > -1) return i;
    }
    return -1;
  }
  function pendingIdx(lis) {
    var out = [];
    for (var i = 0; i < lis.length; i++) if (lis[i].innerText.indexOf('需再学') > -1) out.push(i);
    return out;
  }
  function byDuration(lis, dur) {
    if (!dur) return -1;
    var best = -1, gapBest = 99;
    for (var i = 0; i < lis.length; i++) {
      var m = lis[i].innerText.match(/(\d{2,3}):(\d{2})/);
      if (!m) continue;
      var gap = Math.abs(parseInt(m[1], 10) * 60 + parseInt(m[2], 10) - dur);
      if (gap <= 3 && gap < gapBest) { gapBest = gap; best = i; }
    }
    return best;
  }
  function backToSubject() {
    var st = rd('__casic_subject', null);
    if (st && st.url) { location.hash = st.url; return; }
    var m = (location.hash || '').match(/subjectId=([^&]+)/);
    location.hash = m ? '#/study/subject/detail/' + m[1] : '#/';
  }

  window.__apTimer = setInterval(function () {
    A.page = (location.hash || '').split('?')[0].replace('#/study/', '');
    beat();

    if ((location.hash || '').indexOf('#/login') > -1) {
      A.needLogin = true; A.on = false;
      beat();
      return;
    }
    A.needLogin = false;

    /* 记住专题页地址，供崩溃恢复后回跳 */
    if ((location.hash || '').indexOf('/study/subject/detail/') > -1) {
      var hc = (location.hash.match(/homeConfigId=([^&]+)/) || [])[1] || null;
      var cur = rd('__casic_subject', null);
      if (!cur || cur.url !== location.hash) wr('__casic_subject', { url: location.hash, homeConfigId: hc });
    }

    /* 专题页：挑下一门未完成课程 */
    if ((location.hash || '').indexOf('/study/subject/detail/') > -1) {
      A.noVideo = 0;
      if (A.done && Date.now() - A.cool > 5000) {
        A.cool = Date.now();
        var cards = Array.prototype.slice.call(document.querySelectorAll('.s-info-right'));
        var next = cards.filter(function (el) { return el.innerText.indexOf('已完成') === -1; })[0];
        if (next) {
          A.done = false; A.idx = null; A.cid = null; A.sweeps = 0;
          A.on = true; A.hold = false;          // ← v5：换课必须复活控制器
          persist();
          (next.querySelector('.sub-left') || next).click();
        }
      }
      return;
    }

    if ((location.hash || '').indexOf('/study/course/detail/') === -1) return;

    var c = courseId();
    if (c !== A.cid) {
      A.cid = c; A.idx = epFromHash(); A.sweeps = 0;
      A.on = true; A.done = false; A.noVideo = 0; A.stuck = 0; A.lastT = -1;
      persist();
    }

    var v = document.querySelector('video');
    var lis0 = items();

    if (!v) {
      /* 三种可能：被顶掉 / 平台播完跳"快速笔记" / 还在加载 */
      if (!lis0.length) {
        A.noVideo++;
        if (A.noVideo >= NOVIDEO_LIMIT) {
          A.noVideo = 0; A.cool = Date.now();
          A.idx = null; A.done = false;
          persist();
          backToSubject();                      // ← v5：笔记页无解，直接回专题页
        }
      } else {
        A.kicked = true;
        A.noVideo = 0;
      }
      beat();
      return;
    }
    A.kicked = false;
    A.noVideo = 0;

    if (Math.abs(v.playbackRate - A.rate) > 0.01) v.playbackRate = A.rate;
    if (v.paused && !v.ended) v.play().catch(function () {});

    var lis = lis0;
    if (!lis.length) return;

    var live = activeIdx(lis);
    if (live > -1) {
      if (A.idx !== live) { A.idx = live; persist(); }
    } else if (A.idx === null || A.idx >= lis.length) {
      var e = epFromHash();
      if (e === null || e >= lis.length) e = byDuration(lis, Math.round(v.duration || 0));
      A.idx = (e === null || e < 0) ? 0 : e;
      persist();
    }

    if (Math.abs((v.currentTime || 0) - A.lastT) < 0.3) A.stuck++; else A.stuck = 0;
    A.lastT = v.currentTime || 0;

    if (A.stuck >= STUCK_LIMIT && v.readyState < 3) {
      A.stuck = 0; A.cool = Date.now();
      if (lis[A.idx]) lis[A.idx].click();
      return;
    }

    var near = v.duration > 0 && v.readyState > 0 && (v.duration - v.currentTime < 1.5);
    if (!(v.ended || near) || Date.now() - A.cool <= SWITCH_COOL) return;

    A.cool = Date.now();
    A.stuck = 0;

    if (A.idx + 1 < lis.length) {
      A.idx++; persist();
      lis[A.idx].click(); A.switches++;
      return;
    }

    var pend = pendingIdx(lis);
    if (pend.length && A.sweeps < MAX_SWEEPS) {
      A.sweeps++; A.idx = pend[0]; persist();
      lis[A.idx].click(); A.switches++;
      return;
    }

    /* 本课结束 */
    if (A.stopAfter) {
      try { v.pause(); } catch (e2) {}
      A.on = false; A.hold = true;
      clearInterval(window.__apTimer); window.__apTimer = null;
      beat();
      return;
    }

    A.done = true; A.on = false; persist();
    backToSubject();
  }, 2000);

  persist(); beat();
  return 'autoplay v5: rate=' + RATE + ' stopAfterCourse=' + STOP_AFTER +
    ' cid=' + (cid || '-') + ' idx=' + A.idx + ' sweeps=' + A.sweeps;
})();
