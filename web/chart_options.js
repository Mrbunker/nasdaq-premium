/** ECharts options; null observations remain gaps in both aligned chart panels. */
(function(root) {
  const color = value => value == null || value === 0 ? '#87939f' : value > 0 ? '#cf4d4a' : '#218765';
  function createChartOptions({labels,nav,close,contribution,width,monthly,initialCount,tooltipFormatter}) {
    const unit = monthly ? '月' : '日', barWidth = width < 550 ? 10 : 14;
    const limit = bounds => Math.max(.5,Math.abs(bounds.min || 0),Math.abs(bounds.max || 0))*1.12;
    const axis = index => ({type:'category',gridIndex:index,data:labels,boundaryGap:true,
      axisTick:{show:false},axisLine:{show:false},axisLabel:{show:index===1,color:'#6b7280',fontSize:11,hideOverlap:true,formatter:value=>monthly?value:value.slice(5)}});
    const valueAxis = index => ({type:'value',gridIndex:index,min:bounds=>-limit(bounds),max:limit,
      splitNumber:4,axisLabel:{color:'#6b7280',fontSize:11,formatter:value=>value.toFixed(1)},
      axisLine:{show:false},axisTick:{show:false},splitLine:{lineStyle:{color:'#e8edf3'}}});
    const points = (values,hollow) => values.map(value=>({value,
      itemStyle:hollow?{color:'transparent',borderColor:color(value),borderWidth:1.4}:{color:color(value)}}));
    return {
      animation:false,
      title:[{text:'每'+unit+'涨跌幅 · %',left:58,top:8,textStyle:{fontSize:13,fontWeight:400,color:'#475569'}},
        {text:width<550?'溢价贡献 · 百分点':'溢价贡献 · 百分点（场内涨跌 − 净值涨跌）',left:58,top:'54%',textStyle:{fontSize:13,fontWeight:400,color:'#475569'}}],
      grid:[{left:58,right:20,top:34,height:'42%'},{left:58,right:20,top:'61%',height:'21%'}],
      xAxis:[axis(0),axis(1)],yAxis:[valueAxis(0),valueAxis(1)],
      axisPointer:{link:[{xAxisIndex:'all'}]},
      tooltip:{trigger:'axis',axisPointer:{type:'shadow'},formatter:tooltipFormatter,
        backgroundColor:'rgba(30,41,59,.97)',borderWidth:0,textStyle:{color:'#fff',fontSize:12},padding:[12,15],confine:true,extraCssText:'border-radius:0'},
      dataZoom:[{id:'history-window',type:'slider',xAxisIndex:[0,1],filterMode:'filter',
        startValue:Math.max(0,labels.length-initialCount),endValue:Math.max(0,labels.length-1),rangeMode:['value','value'],
        minValueSpan:Math.min(3,Math.max(0,labels.length-1)),left:58,right:20,bottom:10,height:26,
        borderRadius:0,borderColor:'#d8dfe7',backgroundColor:'#f3f5f8',fillerColor:'rgba(148,163,184,.25)',
        dataBackground:{lineStyle:{color:'#cbd5e1',width:1},areaStyle:{color:'#e2e8f0',opacity:.55}},
        selectedDataBackground:{lineStyle:{color:'#64748b',width:1},areaStyle:{color:'#cbd5e1',opacity:.65}},
        handleSize:'110%',handleStyle:{color:'#fff',borderColor:'#94a3b8',borderWidth:1},
        moveHandleSize:5,moveHandleStyle:{color:'#b6c2cf'},brushSelect:true,textStyle:{fontSize:10,color:'#64748b'},
        labelFormatter:(value,text)=>text || (typeof value==='string'?value:labels[Math.round(value)] || '')},
        {id:'inside-window',type:'inside',xAxisIndex:[0,1],filterMode:'filter',zoomOnMouseWheel:true,moveOnMouseMove:true,moveOnMouseWheel:'shift',
          minValueSpan:Math.min(3,Math.max(0,labels.length-1))}],
      series:[{id:'nav-return',name:'净值'+unit+'涨跌',type:'bar',xAxisIndex:0,yAxisIndex:0,barMaxWidth:barWidth,barGap:'18%',barCategoryGap:'45%',data:points(nav,true)},
        {id:'price-return',name:'场内'+unit+'涨跌',type:'bar',xAxisIndex:0,yAxisIndex:0,barMaxWidth:barWidth,barGap:'18%',barCategoryGap:'45%',data:points(close,false)},
        {id:'premium-contribution',name:'溢价贡献',type:'bar',xAxisIndex:1,yAxisIndex:1,barMaxWidth:20,barCategoryGap:'65%',data:points(contribution,false)}]
    };
  }
  root.createChartOptions = createChartOptions;
  if(typeof module!=='undefined')module.exports=createChartOptions;
})(typeof globalThis!=='undefined'?globalThis:this);
