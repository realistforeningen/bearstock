require 'imba/src/imba/browser'
let fetch = require 'whatwg-fetch'
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
	setTimeout(&, 500) do app.render

tag svg < htmlelement
	prop width dom: yes
	prop height dom: yes

	def self.buildNode
		document:createElementNS("http://www.w3.org/2000/svg", "svg")

tag line-plot < svg

	def build
		let xscale = Plottable.Scales.Linear.new
		let yscale = Plottable.Scales.Linear.new

		let xaxis = Plottable.Axes.Numeric.new(xscale, 'bottom')
		let yaxis = @yaxis = Plottable.Axes.Numeric.new(yscale, 'left')

		let plot = Plottable.Plots.Line.new

		let data = for i in [1 .. 100]
			{x: i, y: i*i}

		plot.addDataset(Plottable.Dataset.new(data))

		plot.x(&, xscale) do |d| d:x
		plot.y(&, yscale) do |d| d:y

		let chart = @chart = Plottable.Components.Table.new([
			[yaxis, plot],
			[null, xaxis]
		])
		chart.renderTo(dom)

	def render
		@chart.redraw
		@yaxis.redraw
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
						<td> "{product:price} NOK"


tag stats
	prop productFetcher

	let main-css = styles
		flex-direction: 'row'
		height: '100%'
		padding: '50px'

	let left-css = styles
		flex: 2

	let right-css = styles
		flex: 2

	def build
		productFetcher = ProductFetcher.new
		productFetcher:sync = do render
		productFetcher.start
		self

	def render
		<self styles=main-css>
			<style> styles.toString
			if productFetcher.products
				<div styles=left-css>
					<price-table products=productFetcher.products>
			<div styles=right-css>
