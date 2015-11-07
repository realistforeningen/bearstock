require 'imba'
let fetch = require 'whatwg-fetch'
let Random = require 'random-js'
Object:assign = require 'object-assign'

let styles = require 'imba-styles'

require "./normalize.css"
require "./default.css"

import ProductFetcher from "./loader"

let Plottable = require "plottable/plottable"

def window.startApp
	styles.freeze
	let app = <stats>
	document:body.appendChild(app.dom)

tag svg < htmlelement
	prop width dom: yes
	prop height dom: yes

	def self.buildNode
		document:createElementNS("http://www.w3.org/2000/svg", "svg")

tag line-plot < svg
	prop data
	prop codes

	let legend-css = styles
		"&.legend text":
			font-family: 'monospace'

	def data=(newData)
		if newData !== @data
			@keys = Object.keys(newData)
			@datasets = for key, idx in @keys
				Plottable.Dataset.new(newData[key], code: key)
			@data = newData
			@didChange = yes
		self

	def build
		let cs = @cs = Plottable.Scales.Color.new

		let xscale = @xscale = Plottable.Scales.Time.new
		let yscale = Plottable.Scales.Linear.new

		let xaxis = @xaxis = Plottable.Axes.Time.new(xscale, 'bottom')
		xaxis.axisConfigurations([
			[
				{ interval: Plottable.TimeInterval:minute, step: 30, formatter: Plottable.Formatters.time("%H:%M") },
				{ interval: Plottable.TimeInterval:day, step: 1, formatter: Plottable.Formatters.time("%B %e") },
			]
		])
		let yaxis = @yaxis = Plottable.Axes.Numeric.new(yscale, 'left')

		let plot = @plot = Plottable.Plots.Line.new

		plot.x(&, xscale) do |d| Date.new(d:timestamp*1000)
		plot.y(&, yscale) do |d| d:value + d:jitter

		plot.attr("stroke") do |_,_,ds|
			cs.scale(ds.metadata:code)

		plot.attr("stroke-width") do |_,_,ds|
			2

		let legend = @legend = Plottable.Components.Legend.new(cs)
		legend.maxEntriesPerRow(5)
		legend.symbolOpacity do |code|
			if code in @keys
				1
			else
				0
		legend.addClass(legend-css.className)

		let title = Plottable.Components.TitleLabel.new("Highlights:")

		let chart = @chart = Plottable.Components.Table.new([
			[null, legend],
			[yaxis, plot],
			[null, xaxis]
		])
		chart.renderTo(dom)

		let svg = tag(chart.@rootSVG[0][0])
		svg.css height: 'auto', width: 'auto', flex: 1
		super

	def render
		return if !@didChange
		@didChange = no

		setTimeout(&, 0) do
			@cs.domain(codes)
			@plot.datasets(@datasets)

			@xscale.autoDomain
			var [start, end] = @xscale.domain
			if end - start < 1000*60*60*1
				end.setHours(end.getHours + 1)
				@xscale.domain([start, end])

		@chart.redraw
		@yaxis.redraw
		@xaxis.redraw
		@plot.redraw

		self

tag price-table < table
	prop products

	let table-css = styles.css
		width: '100%'

	let row-even-css = styles.css

	let row-odd-css = styles.css
		background: '#eee'

	let row-base-css = styles.css
		"& td":
			padding: '0.5em 1em'

	def row-css(idx)
		if idx % 2 == 0
			[row-base-css, row-even-css]
		else
			[row-base-css, row-odd-css]

	def render
		<self styles=table-css>
			<tbody>
				for product, idx in products
					<tr styles=[row-css(idx)]>
						<td> product:code
						<td> product:name
						<td> "{product:absolute_cost} NOK"


tag ticker
	prop products

	let main-css = styles
		background: '#ddd'
		padding: '5px 0'
		flex-direction: 'row'
		border-bottom: '2px solid #666'

	let wrapper-css = styles
		flex: '0 0 auto'
		flex-direction: 'row'
		animation: 'ticker 50s linear 0s infinite'

	let product-css = styles
		margin-right: '50px'
		flex: '0 0 auto'
		align-items: 'baseline'
		flex-direction: 'row'

	let code-css = styles.css
		font-weight: 'bold'

	let price-css = styles.css
		margin-left: '5px'

	let positive-css = styles.css
		margin-left: '5px'
		color: 'green'
		font-size: '0.8em'

	let negative-css = styles.css
		margin-left: '5px'
		color: 'red'
		font-size: '0.8em'

	def render
		<self styles=main-css>
			<div styles=wrapper-css>
				for product in products
					<div styles=product-css>
						<div styles=code-css> product:code
						<div styles=price-css> "{product:absolute_cost} NOK"
						if product:delta_cost > 0
							<div styles=positive-css> "▲"
						else
							<div styles=negative-css> "▼"


tag buyer-table < table
	prop title
	prop rows

	let row-base-css = styles
		flex-direction: 'row'

		'& td':
			vertical-align: 'top'
			padding: '3px 5px'

	let row-even-css = styles
		background: '#eee'

	let name-css = styles.css

	let profit-css = styles
		text-align: 'right'
		width: '40px'
		white-space: 'nowrap'

	def row-css(idx)
		if idx % 2 == 0
			[row-base-css, row-even-css]
		else
			[row-base-css]

	def render
		<self>
			for buyer, idx in rows
				<tr styles=row-css(idx)>
					<td> "{idx+1}. "
					<td styles=name-css> buyer:name
					<td styles=profit-css> "{buyer:profit} points"

tag stats
	prop productFetcher
	prop priceData
	prop buyerData

	def addJitter(data)
		for key of data
			let seed = (char.charCodeAt(0) for char in key.split(""))
			let r = Random.new(Random:engines.mt19937.seedWithArray(seed))
			for entry in data[key]
				# TODO: deterministic jitter?
				entry:jitter = r.real(-0.5, 0.5)
		return data

	def build
		productFetcher = ProductFetcher.new
		productFetcher:sync = do
			updateHighlights if !priceData
			updateBuyers if !buyerData
			render
		productFetcher.start

		setInterval(&, 1000) do
			render

		setInterval(&, 30000) do
			updateHighlights
			updateBuyers

		self

	def updateHighlights
		let products = productFetcher.products
		if !products
			return

		let highlights = Random.new.sample(products, 5)
		let query = ("code={product:code}" for product in highlights).join("&")

		fetch("/prices?{query}")
			.then do |res|
				res.json
			.then do |data|
				priceData = addJitter(data)
				render

	def updateBuyers
		fetch("/stats/buyers")
			.then do |res|
				res.json
			.then do |data|
				buyerData = data
				render

	let main-css = styles.css
		height: '100%'

	let left-css = styles
		flex: 2

	let right-css = styles
		flex: 2
		flex-direction: 'row'

	let price-css = styles
		flex: 3

	let buyer-css = styles
		flex: 1
		font-size: '0.8em'
		padding: '1em 2em'

		'& table':
			width: '100%'
			margin-bottom: '1em'

	let buyer-header-css = styles
		font-weight: 'bold'

	let buyer-profit-css = styles
		text-align: 'right'

	def render
		let products = productFetcher.products

		<self styles=main-css>
			<style> styles.toString
			<ticker products=products>

			# <div styles=left-css>
			#	if productFetcher.products
			#		<price-table products=productFetcher.products>
			<div styles=right-css>
				if priceData
					<div styles=price-css>
						<line-plot data=priceData codes=(product:code for product in products)>

				if buyerData and buyerData:buyers:count > 0
					<div styles=buyer-css>
						<div styles=buyer-header-css> "Top traders"
						<buyer-table rows=buyerData:buyers:top>

						<div styles=buyer-header-css> "Bad traders"
						<buyer-table rows=buyerData:buyers:bottom>


