var nv = require 'nvd3'
require 'nvd3/build/nv.d3.css'
var d3 = require 'd3'
extern fetch

var styles = require 'imba-styles'

import grow from './styling'

require 'imba/src/imba/dom/svg'

export tag Stats
	def render
		<self>
			<Prices>

export tag Prices
	prop products

	def fetchData
		var data = await fetch("/products.json").then(do $1.json)
		products = data:products
		products.sort do |a, b|
			a:code.localeCompare(b:code)
		render

	def build
		products = []
		fetchData
		setInterval(&, 10000) do
			fetchData

	styles.insert self,
		main-css:
			width: '600px'
			margin: '20px auto'

		prices-css:
			display: 'grid'
			grid-template-columns: 'auto 1fr auto auto auto'
			grid-gap: '10px 20px'
			align-items: 'center'

			'& .code, & .price':
				font-weight: 'bold'

			'& .pos':
				color: 'green'

			'& .neg':
				color: 'red'

			'& .adj':
				font-size: '0.7em'

			'& > div':
				flex-direction: 'row'

	def render
		<self.{@main-css}>
			<div.{@prices-css}>
				for prod in products
					<p.code> prod:code
					<p.name> "{prod:producer} {prod:name}"
					<p.price.pos=(prod:price_adjustment < 0) .neg=(prod:price_adjustment > 0)> "{prod:current_price} NOK"
					<p.adj>
						if prod:price_adjustment > 0
							"▲"
						elif prod:price_adjustment < 0
							"▼"
					<p.diff> prod:price_adjustment/100

export tag Graph
	styles.insert self,
		main-css:
			position: 'fixed'
			height: '100%'
			width: '100%'

	def svg
		<svg:svg@svg.{grow}>

	def updateChart stocks
		d3.select(svg.dom)
			.datum(stocks)
			.call(@chart)

	def fetchData
		var data = await fetch("/stocks.json").then(do $1.json)
		updateChart(data:stocks)

	def build
		nv.addGraph do
			var chart = @chart = nv:models.lineChart
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

			updateChart([])

			fetchData
			setInterval(&, 10000) do
				fetchData

			chart

	def render
		<self.{@main-css}>
			svg
