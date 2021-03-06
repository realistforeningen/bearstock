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
			flex-direction: 'row'
			margin: '20px'

			"& .prices":
				border-right: '1px solid #ccc'
				padding-right: '20px'

	def render
		<self.{@main-css}>
			<Prices.prices>
			<Buyers>

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

export tag Buyers
	prop buyers

	def fetchData
		var data = await fetch("/buyers.json").then(do $1.json)
		buyers = data:buyers

		buyers = buyers.filter do |b| b:relative_cost_stats:count != 0

		buyers.forEach do |b|
			b:sum_relative_cost = Math.ceil(b:relative_cost_stats:sum / b:relative_cost_stats:count)

		buyers.sort do |a, b|
			a:sum_relative_cost - b:sum_relative_cost

		render

	def bigTraders
		var b = buyers.slice
		b.sort do |a, b|
			a:relative_cost_stats:count - b:relative_cost_stats:count
		b.reverse

	def build
		buyers = []
		fetchData
		setInterval(&, 10000) do
			fetchData

	styles.insert self,
		main-css:
			flex-direction: 'row'
			flex-wrap: 'wrap'
			flex: 1

			"& table":
				border-collapse: 'separate'
				border-spacing: '10px'

				":first-child":
					margin-right: '50px'

				"& th":
					text-align: 'left'

			"& .money":
				text-align: 'right'
				font-weight: 'bold'

			'& .pos':
				color: 'green'

			'& .neg':
				color: 'red'

	def losers
		var b = buyers.slice
		b.reverse

	def table headers, data
		<table>
			<thead>
				<tr>
					for header in headers
						<th> header
			<tbody>
				for buyer in data
					var num = - buyer:sum_relative_cost
					<tr>
						<td.name> "{buyer:icon or ''} {buyer:username}"
						<td.money .pos=(num > 0) .neg=(num < 1)> "{num} NOK"

	def countTable headers, data
		<table>
			<thead>
				<tr>
					for header in headers
						<th> header
			<tbody>
				for buyer in data
					<tr>
						<td.name> "{buyer:icon or ''} {buyer:username}"
						<td.money> buyer:relative_cost_stats:count

	var count = 10

	def render
		<self.{@main-css}>
			table(["Best", "Savings per order"], buyers.slice(0, count))
			table(["Worst", "Savings per order"], losers.slice(0, count))
			countTable(["Big traders", "Count"], bigTraders.slice(0, count))

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
