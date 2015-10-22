require 'imba/src/imba/browser'
require 'whatwg-fetch'
extern fetch
Object:assign = require 'object-assign'

let styles = require 'imba-styles'

require "./normalize.css"
require "./default.css"

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

tag stats
	let main-css = styles
		height: '100%'

	let plot-css = styles
		padding: '50px'
		height: '100%'

	def render
		<self styles=main-css>
			<style> styles.toString
			<div styles=plot-css>
				<line-plot>
