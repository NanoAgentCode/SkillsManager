// 从 agent-browser eval 返回的 JSON 里取字段
// 用法：echo "$JSON" | node jq.js page
let s = '';
process.stdin.on('data', (d) => { s += d; }).on('end', () => {
  let o = {};
  try { o = JSON.parse(s); } catch (e) {}
  if (typeof o === 'string') { try { o = JSON.parse(o); } catch (e) { o = {}; } }
  const k = process.argv[2];
  const v = o[k];
  if (v === undefined || v === null) process.stdout.write('');
  else if (typeof v === 'object') process.stdout.write(JSON.stringify(v));
  else process.stdout.write(String(v));
});
