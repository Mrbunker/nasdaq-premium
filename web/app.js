const DATA = JSON.parse(document.getElementById('data').textContent), funds = DATA.funds;
const $ = id => document.getElementById(id);
const changeColor = n => n == null || n === 0 ? '#87939f' : n > 0 ? '#cf4d4a' : '#218765';
const tooltipColor = n => n == null || n === 0 ? '#bac5d2' : n > 0 ? '#f29a98' : '#73c9a5';
const pfmt = n => n == null ? '—' : (n >= 0 ? '+' : '') + n.toFixed(2) + '%';
const ppfmt = n => n == null ? '—' : (n >= 0 ? '+' : '') + n.toFixed(2) + ' 个百分点';
let activeFund = funds[0].code, granularity = 'daily', descending = true, resizeObservers = [];
function getPeriod() { return {min: '-', max: DATA.cutoff}; }
function seriesFor(f) {
  return granularity === 'daily' ? f.series : f.monthly_series.map(r => ({...r,
    daily_nav_pct: r.monthly_nav_pct, daily_close_pct: r.monthly_close_pct,
    prev_trade_date: r.prev_date, daily_status: r.monthly_status}));
}
function unitName() {return granularity === 'monthly' ? '月' : '日';}
function selectedFunds() { return funds.filter(f => ($('category').value === 'all' || f.index === $('category').value) && (activeFund === 'all' || f.code === activeFund)); }
function renderFundTabs() {
  const available = funds.filter(f => $('category').value === 'all' || f.index === $('category').value);
  if (activeFund !== 'all' && !available.some(f => f.code === activeFund)) activeFund = 'all';
  const items = [{code:'all',name:'全部基金'}, ...available], bar = $('fundTabs'), scroll = bar.scrollLeft;
  bar.innerHTML = items.map(f => `<button type="button" role="tab" id="fund-tab-${f.code}" data-fund="${f.code}" aria-controls="fundList" aria-selected="${f.code===activeFund}" tabindex="${f.code===activeFund?0:-1}">${f.name}<span class="tab-code">${f.code==='all'?`${available.length} 只基金`:f.code}</span></button>`).join('');
  bar.scrollLeft = scroll;
  function select(code) {activeFund=code;render();const button=$('fund-tab-'+code);button.focus({preventScroll:true});button.scrollIntoView({block:'nearest',inline:'nearest'});}
  [...bar.children].forEach((button,i) => {button.onclick=()=>select(button.dataset.fund);button.onkeydown=event=>{let target=null;if(event.key==='ArrowRight')target=(i+1)%items.length;if(event.key==='ArrowLeft')target=(i+items.length-1)%items.length;if(event.key==='Home')target=0;if(event.key==='End')target=items.length-1;if(target!==null){event.preventDefault();select(items[target].code);}};});
  $('fundList').setAttribute('role',activeFund==='all'?'region':'tabpanel');$('fundList').setAttribute('aria-labelledby','fund-tab-'+activeFund);
}
function render() {
  resizeObservers.forEach(o=>o.disconnect());resizeObservers=[];$('fundList').innerHTML='';renderFundTabs();
  $('dailyPeriod').setAttribute('aria-pressed',granularity==='daily');$('monthlyPeriod').setAttribute('aria-pressed',granularity==='monthly');
  const unit = unitName();
  $('legend').innerHTML=`<span><i class="dot bar-dot series-outline"></i>净值${unit}涨跌 · 空心柱</span><span><i class="dot bar-dot series-filled"></i>场内${unit}涨跌 · 实心柱</span><span><i class="dot bar-dot up-dot"></i>上涨</span><span><i class="dot bar-dot down-dot"></i>下跌</span><span>下排：溢价贡献（正值放大收益，负值拖累收益）</span>`;
  $('rangeNote').textContent=granularity==='daily'?'日柱 · 全部历史，默认定位最近交易日。可用滚轮、＋/−缩放；拖动或底部双端滑块浏览。缺失或折算区间留空。':'月柱 · 每月最后一个价格与公布净值同日期均可用的交易日，相对前月末计算。当前月未结束，会标注月内统计截止日；滚轮缩放，拖动或滑块浏览。';
  for (const f of selectedFunds()) drawDailyCard(f, seriesFor(f));
  renderDailySummary();
}
$('tabsPrev').onclick=()=>$('fundTabs').scrollBy({left:-360,behavior:'smooth'});$('tabsNext').onclick=()=>$('fundTabs').scrollBy({left:360,behavior:'smooth'});
const categorySelect = new TomSelect('#category', {
  create:false, controlInput:null, maxOptions:4, closeAfterSelect:true, onChange:render,
  render:{option:(data,escape)=>`<div class="option"><span>${escape(data.text)}</span><span class="option-check" aria-hidden="true">✓</span></div>`}
});
categorySelect.control.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();categorySelect.close();}});
$('dailyPeriod').onclick=()=>{granularity='daily';render();};$('monthlyPeriod').onclick=()=>{granularity='monthly';render();};
$('footer').textContent='采集时间：'+DATA.fetched_at.slice(0,19).replace('T',' ')+'（北京时间） · 数据来自天天基金 / 东方财富；腾讯价格交叉核验。';
$('coverage').innerHTML=funds.map(f=>`<tr><td>${f.code} ${f.name}</td><td>${f.price_first}</td><td>${f.nav_count.toLocaleString()}</td><td>${f.price_count.toLocaleString()}</td><td>${f.matched_count.toLocaleString()}</td><td><a href="https://fundf10.eastmoney.com/jjjz_${f.code}.html" target="_blank" rel="noopener">历史净值</a> / <a href="https://quote.eastmoney.com/${f.market}${f.code}.html" target="_blank" rel="noopener">行情</a></td></tr>`).join('');
render();
