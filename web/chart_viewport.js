/** Date-window model shared by zoom buttons, wheel, dragging and the range slider. */
(function(root) {
  class ChartViewport {
    constructor(total, width, options = {}) {
      this.total = total;
      this.initialCount = options.initialCount || 20;
      this.limitByWidth = options.limitByWidth !== false;
      this.desiredCount = this.initialCount;
      this.offset = 0;
      this.count = 0;
      this.width = null;
      this.resize(width);
      this.offset = this.maxOffset;
    }
    get maxOffset() { return Math.max(0, this.total - this.count); }
    clamp(value, min, max) { return Math.min(max, Math.max(min, value)); }
    resize(width) {
      if (width === this.width) return;
      const atEnd = this.offset >= this.maxOffset;
      const center = this.offset + this.count / 2;
      this.width = width;
      this.minCount = Math.min(4, this.total);
      this.maxCount = this.limitByWidth ? Math.max(this.minCount, Math.min(this.total, Math.floor(Math.max(0, width - 73) / (width < 550 ? 36 : 28)))) : this.total;
      this.count = this.clamp(this.desiredCount, this.minCount, this.maxCount);
      this.offset = atEnd ? this.maxOffset : this.clamp(Math.round(center - this.count / 2), 0, this.maxOffset);
    }
    setOffset(value) { this.offset = this.clamp(Math.round(value), 0, this.maxOffset); }
    setRange(start, end) {
      this.count = this.clamp(Math.round(end - start + 1), this.minCount, this.maxCount);
      this.desiredCount = this.count;
      this.setOffset(start);
    }
    pan(delta) { this.setOffset(this.offset + delta); }
    zoom(factor, fraction = .5) {
      fraction = this.clamp(fraction, 0, 1);
      const anchor = this.offset + fraction * this.count;
      let count = Math.round(this.count * factor);
      if (count === this.count && factor !== 1) count += factor > 1 ? 1 : -1;
      this.count = this.clamp(count, this.minCount, this.maxCount);
      this.desiredCount = this.count;
      this.setOffset(anchor - fraction * this.count);
    }
    reset() {
      this.desiredCount = this.initialCount;
      this.count = this.clamp(this.initialCount, this.minCount, this.maxCount);
      this.offset = this.maxOffset;
    }
  }
  root.ChartViewport = ChartViewport;
  if (typeof module !== 'undefined') module.exports = ChartViewport;
})(typeof globalThis !== 'undefined' ? globalThis : this);
