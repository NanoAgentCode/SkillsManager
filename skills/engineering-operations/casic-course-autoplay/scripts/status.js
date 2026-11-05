/*
 * 航天云课堂 · 播放状态快照 v4
 * 用法：agent-browser eval --stdin < scripts/status.js
 *
 * 返回单行 JSON，供外部脚本判断"该不该恢复"，无需人肉看页面。
 *
 * 关键字段：
 *   page        course | subject | login | blank | other
 *   alive       页面内控制器是否真的在跑（刷新/清空后必为 false）
 *   action      建议动作：none / reopen / relogin / enter_course / reinject / back_to_subject / holding
 *   courses     专题页才有：全部课程及完成状态
 *   no_video    课程页但找不到 video 的原因：notes（快速笔记页）/ kicked（被顶）/ loading
 *
 * v4 修正（都来自实战）：
 *   1. alive 只看页面内的 window.__ap 心跳。旧版用 localStorage 心跳兜底，
 *      导致页面刷新后仍被判为"活着"，watch 不触发自愈，卡在专题页不动。
 *   2. 课程页无 video 且列表为空 → 判 back_to_subject。平台播完会跳"快速笔记"页，
 *      那种页面注入控制器无效，只能回专题页重选课程。
 *   3. 新增 courses 清单，一次调用即可看到全景进度，不必再单独 eval 抓列表。
 */
(function () {
  var now = Date.now();
  var href = location.href || '';
  var hash = location.hash || '';
  var v = document.querySelector('video');
  var body = (document.body && document.body.innerText) || '';

  function rd(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
  var A = window.__ap || null;
  var hbLS = rd('__casic_hb');
  var stLS = rd('__casic_state');

  var page = 'other';
  if (href === 'about:blank' || !body.trim()) page = 'blank';
  else if (hash.indexOf('/study/subject/detail/') > -1) page = 'subject';
  else if (hash.indexOf('/study/course/detail/') > -1) page = 'course';
  else if (hash.indexOf('#/login') > -1) page = 'login';

  var prog = body.match(/课程总进度\s*(\d+)%/);
  var must = body.match(/必修\s*(\d+)\/(\d+)/);

  var lis = Array.prototype.slice.call(document.querySelectorAll('.catalog-box li'))
    .filter(function (li) { return li.offsetParent !== null; });
  var active = lis.findIndex(function (li) { return (li.className || '').indexOf('active-section') > -1; });
  var pendingEps = [];
  lis.forEach(function (li, i) { if (li.innerText.indexOf('需再学') > -1) pendingEps.push(i); });

  /* 只认页面内的心跳：页面一旦刷新/清空，window.__ap 必然消失，绝不能用 localStorage 兜底 */
  var alive = !!(A && A.hb && (now - A.hb) < 12000);
  var hbAge = A && A.hb ? now - A.hb : null;

  /* 专题页：课程清单 */
  var courses = null;
  var doneCount = null;
  if (page === 'subject') {
    courses = Array.prototype.slice.call(document.querySelectorAll('.s-info-right')).map(function (el, i) {
      var t = (el.innerText || '').replace(/\s+/g, ' ').trim();
      var title = t.replace(/^课程\s*必\s*/, '').replace(/(已完成|学习中|未开始)\s*$/, '').trim();
      return {
        i: i,
        title: title.slice(0, 30),
        done: t.indexOf('已完成') > -1,
        learning: t.indexOf('学习中') > -1
      };
    });
    doneCount = courses.filter(function (c) { return c.done; }).length;
  }

  /* 课程页无 video 的原因 */
  var noVideo = null;
  if (page === 'course' && !v) {
    if (body.indexOf('快速笔记') > -1 || lis.length === 0) noVideo = 'notes';
    else if (body.indexOf('其他终端') > -1) noVideo = 'kicked';
    else noVideo = 'loading';
  }

  var kicked = body.indexOf('其他终端') > -1;
  var holding = !!(A && A.hold) || !!(hbLS && hbLS.hold);

  var action = 'none';
  if (page === 'blank') action = 'reopen';
  else if (page === 'login') action = 'relogin';
  else if (kicked) action = 'reinject';
  else if (holding) action = 'holding';
  else if (page === 'course' && noVideo === 'notes') action = 'back_to_subject';
  else if (page === 'course' && !v) action = 'reinject';
  else if (page === 'course' && !alive) action = 'reinject';
  else if (page === 'subject' && !alive) action = 'enter_course';

  return JSON.stringify({
    page: page,
    course: page === 'course' ? (body.split('\n')[0] || '').trim().slice(0, 26) : null,
    progress: prog ? prog[1] + '%' : null,
    required: must ? must[1] + '/' + must[2] : null,
    index: A ? A.idx : (active > -1 ? active : null),
    active: active,
    time: v ? Math.round(v.currentTime) : null,
    duration: v ? Math.round(v.duration) : null,
    rate: v ? v.playbackRate : null,
    playing: v ? !v.paused : false,
    autopilot_on: alive && A ? !!A.on : false,
    hold: holding,
    alive: alive,
    hb_age_ms: hbAge === null ? null : Math.round(hbAge),
    need_login: page === 'login' || (A ? !!A.needLogin : false),
    stuck: A ? (A.stuck || 0) : 0,
    switches: (A && A.switches) || (stLS && stLS.switches) || 0,
    pending_eps: pendingEps,
    no_video: noVideo,
    done_count: doneCount,
    total_count: courses ? courses.length : null,
    courses: courses,
    kicked: kicked,
    action: action
  });
})();
