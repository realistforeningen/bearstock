var nv = require 'nvd3'
require 'nvd3/build/nv.d3.css'
var d3 = require 'd3'
extern fetch

var styles = require 'imba-styles'

import grow from './styling'

require 'imba/src/imba/dom/svg'

export tag Stats
	styles.insert self,
		main-css:
			position: 'fixed'
			height: '100%'
			width: '100%'

	def svg
		<svg:svg@svg.{grow}>

	def updateChart stocks, chart = @chart
		d3.select(svg.dom)
			.datum(stocks)
			.call(chart)

	def fetchData
		var data = await fetch("/stocks.json").then(do $1.json)
		updateChart(data:stocks)


	def build
		nv.addGraph do
			var chart = nv:models.lineChart
				.showYAxis(yes)
				.showXAxis(yes)
				.focusEnable(no)

			var format = d3:time:format('%H:%M')

			chart:xAxis
				.axisLabel('Time')
				.tickFormat(do format(Date.new($1*1000)))

			chart:yAxis
				.axisLabel('Price (NOK)')

			chart:tooltip.enabled(no)

			updateChart([], chart)

			@chart = chart

		setInterval(&, 10000) do
			fetchData

	def render
		<self.{@main-css}>
			svg
