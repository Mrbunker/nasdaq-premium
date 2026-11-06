function renderDailySummary() {
  const period = getPeriod();
  const monthly = granularity === 'monthly', unit = unitName(), key = monthly ? 'month' : 'date';
  const items = selectedFunds().map(f => ({f, rows: seriesFor(f).filter(r => r.date >= period.min && r.date <= period.max && r.premium_contribution_pp != null)})).filter(item => item.rows.length);
  const sets = items.map(item => new Set(item.rows.map(r => r[key])));
  const date = sets.length ? [...sets[0]].filter(d => sets.every(s => s.has(d))).sort().at(-1) : null;
  $('tabletitle').textContent = date ? '最新'+unit+'涨跌对比 · ' + date : '暂无共同日期涨跌数据';
  $('tableNote').textContent = date ? `${items.length} 只基金按同一${monthly?'月份（当前月为月内数据）':'日期'}比较；溢价贡献与溢价率变化均以百分点计。` : '请调整基金筛选；缺失和份额折算区间不补算。';
  document.querySelector('.tablebox thead').innerHTML = `<tr><th>基金</th><th>净值${unit}涨跌幅</th><th>场内${unit}涨跌幅</th><th><button class="sortbtn" id="sort">溢价贡献 ${descending?'↓':'↑'}</button></th><th>溢价率变化</th>${monthly?'<th>统计截至</th>':''}</tr>`;
  const pairs = date ? items.map(({f, rows}) => ({f, r: rows.find(r => r[key] === date)})).sort((a,b) => (descending?-1:1)*(a.r.premium_contribution_pp-b.r.premium_contribution_pp)) : [];
  $('summary').innerHTML = pairs.map(({f,r}) => `<tr><td><span class="code">${f.code}</span> ${f.name}</td><td style="color:${changeColor(r.daily_nav_pct)}">${pfmt(r.daily_nav_pct)}</td><td style="color:${changeColor(r.daily_close_pct)}">${pfmt(r.daily_close_pct)}</td><td style="color:${changeColor(r.premium_contribution_pp)}">${ppfmt(r.premium_contribution_pp)}</td><td style="color:${changeColor(r.premium_change_pp)}">${ppfmt(r.premium_change_pp)}</td>${monthly?`<td>${r.date}${r.is_partial?'（月内）':''}</td>`:''}</tr>`).join('');
  $('sort').onclick = () => {descending = !descending; renderDailySummary();};
}

function drawDailyCard(f, allRows) {
  const monthly=granularity==='monthly',unit=unitName();
  const rows=allRows.filter(r=>r.close!=null||r.daily_status.includes('份额折算'));
  const labels=rows.map(r=>monthly?r.month:r.date),byLabel=new Map(rows.map((r,i)=>[labels[i],r]));
  const latest=rows.filter(r=>r.close!=null).at(-1),card=document.createElement('article');
  card.className='card';card.dataset.fund=f.code;
  card.innerHTML=`<h3><span>${f.name}</span><span class="code">${f.code}</span></h3><span class="category">${f.index} · ${monthly?'月涨跌相对前月末共同日期':'日涨跌相对上一场内交易日'}</span><div class="chart-tools"><div class="zoom-controls"><button type="button" class="zoom-in" aria-label="放大图表">＋</button><span class="zoom-label"></span><button type="button" class="zoom-out" aria-label="缩小图表">−</button><button type="button" class="zoom-reset">重置</button></div><span class="gesture-hint">滚轮缩放 · 拖动平移 · 底部双端选择区间</span></div><div class="chart daily-chart" role="img" tabindex="0" aria-label="${f.name}每${unit}涨跌幅与溢价贡献图"></div><div class="bar-navigation"><span class="window-label"></span></div><div class="last">${latest?`${monthly?latest.month+(latest.is_partial?'（月内截至 '+latest.date+'）':'（统计截至 '+latest.date+'）'):latest.date}：净值${unit}涨跌 <strong style="color:${changeColor(latest.daily_nav_pct)}">${pfmt(latest.daily_nav_pct)}</strong> · 场内${unit}涨跌 <strong style="color:${changeColor(latest.daily_close_pct)}">${pfmt(latest.daily_close_pct)}</strong> · 溢价贡献 ${ppfmt(latest.premium_contribution_pp)}${latest.daily_status==='正常'?'':` · ${latest.daily_status}`}`:'暂无场内交易数据'}</div>`;
  $('fundList').appendChild(card);
  const dom=card.querySelector('.chart'),zoomIn=card.querySelector('.zoom-in'),zoomOut=card.querySelector('.zoom-out');
  const zoomReset=card.querySelector('.zoom-reset'),zoomLabel=card.querySelector('.zoom-label'),windowLabel=card.querySelector('.window-label');
  if(!rows.length){dom.textContent='暂无场内交易数据';zoomIn.disabled=true;zoomOut.disabled=true;return;}
  const initialCount=monthly?12:dom.clientWidth<550?7:20;
  const viewport=new ChartViewport(rows.length,dom.clientWidth,{initialCount,limitByWidth:false});
  const chart=echarts.init(dom,null,{renderer:'canvas'});
  let programmatic=false,userAdjusted=false;
  function tooltip(params){
    const point=Array.isArray(params)?params[0]:params;if(!point)return '';
    const r=byLabel.get(String(point.axisValue))||byLabel.get(String(point.name));if(!r)return '';
    return `<b>${monthly?r.month:r.date}</b>${monthly?`<br>${r.is_partial?'本月未结束，月内截至':'统计截至'} ${r.date}`:''}${r.prev_trade_date?`<br>对比${monthly?'前月末':'前日'} ${r.prev_trade_date}`:''}<br><span style="color:${tooltipColor(r.daily_nav_pct)}">净值${unit}涨跌：${pfmt(r.daily_nav_pct)}</span><br><span style="color:${tooltipColor(r.daily_close_pct)}">场内${unit}涨跌：${pfmt(r.daily_close_pct)}</span><br><b style="color:${tooltipColor(r.premium_contribution_pp)}">溢价贡献：${ppfmt(r.premium_contribution_pp)}</b><br>事后溢价率：${pfmt(r.prev_premium_pct)} → ${pfmt(r.premium_pct)}<br>溢价率变化：${ppfmt(r.premium_change_pp)}${r.daily_status==='正常'?'':`<br>${r.daily_status}`}`;
  }
  chart.setOption(createChartOptions({labels,nav:rows.map(r=>r.daily_nav_pct),close:rows.map(r=>r.daily_close_pct),
    contribution:rows.map(r=>r.premium_contribution_pp),width:dom.clientWidth,monthly,initialCount:viewport.count,tooltipFormatter:tooltip}));
  function updateControls(){
    card.dataset.visibleDays=String(viewport.count);card.dataset.viewOffset=String(viewport.offset);
    zoomLabel.textContent=viewport.count+' '+unit;zoomIn.disabled=viewport.count<=viewport.minCount;zoomOut.disabled=viewport.count>=viewport.maxCount;
    windowLabel.textContent=`${labels[viewport.offset]} — ${labels[viewport.offset+viewport.count-1]} · 当前 ${viewport.count} ${unit} / 共 ${rows.length} ${unit}`;
  }
  function sync(){
    const option=chart.getOption().dataZoom.find(z=>z.id==='history-window');
    const index=(value,percent,fallback)=>typeof value==='string'?labels.indexOf(value):Number.isFinite(value)?value:Number.isFinite(percent)?Math.round((rows.length-1)*percent/100):fallback;
    const start=index(option.startValue,option.start,0),end=index(option.endValue,option.end,rows.length-1);
    viewport.setRange(Math.max(0,start),Math.max(start,end));if(!programmatic)userAdjusted=true;updateControls();
  }
  function applyWindow(){programmatic=true;chart.dispatchAction({type:'dataZoom',startValue:viewport.offset,endValue:viewport.offset+viewport.count-1});programmatic=false;updateControls();}
  chart.on('datazoom',sync);updateControls();
  zoomIn.onclick=()=>{userAdjusted=true;viewport.zoom(.8);applyWindow();};zoomOut.onclick=()=>{userAdjusted=true;viewport.zoom(1.25);applyWindow();};
  zoomReset.onclick=()=>{userAdjusted=false;viewport.initialCount=monthly?12:dom.clientWidth<550?7:20;viewport.reset();applyWindow();};
  const observer=new ResizeObserver(()=>{chart.resize();viewport.resize(dom.clientWidth);if(!userAdjusted){viewport.initialCount=monthly?12:dom.clientWidth<550?7:20;viewport.reset();applyWindow();}
    const width=dom.clientWidth<550?10:14;chart.setOption({series:[{id:'nav-return',barMaxWidth:width},{id:'price-return',barMaxWidth:width}]});});
  observer.observe(dom);resizeObservers.push({disconnect(){observer.disconnect();chart.dispose();}});
  dom.onkeydown=event=>{if(event.key==='ArrowLeft')viewport.pan(-1);else if(event.key==='ArrowRight')viewport.pan(1);else if(event.key==='+'||event.key==='=')viewport.zoom(.8);else if(event.key==='-')viewport.zoom(1.25);else if(event.key==='Home')viewport.setOffset(0);else if(event.key==='End')viewport.setOffset(viewport.maxOffset);else return;event.preventDefault();userAdjusted=true;applyWindow();};
}
