var Imba = require 'imba'

require 'whatwg-fetch'
extern fetch
var styles = require 'imba-styles'

var Color = require 'color'

require "./normalize.css"
require "./default.css"

import ProductCollection from "./filters"
import ProductFetcher from "./loader"

let colors =
	background: Color("#C9D6DF")

tag Window
	styles.insert self,
		main-css:
			height: '100%'
			background: '#bfbfbf'
			padding: '5px'
			border: '1px solid'
			border-top-color: '#dfdfdf'
			border-left-color: '#dfdfdf'
			border-right-color: '#808080'
			border-bottom-color: '#808080'

		header-css:
			background: 'linear-gradient(to right, #000080, #1084d0)'
			color: '#fff'
			padding: '0.5em 1em'
			flex-direction: 'row'

		content-css:
			flex: 1
			
tag App
	styles.insert self,
		main-css:
			height: '100%'
			background: '#bfbfbf'
			padding: '5px'
			border: '1px solid'
			border-top-color: '#dfdfdf'
			border-left-color: '#dfdfdf'
			border-right-color: '#808080'
			border-bottom-color: '#808080'

		header-css:
			background: 'linear-gradient(to right, #000080, #1084d0)'
			color: '#fff'
			padding: '0.5em 1em'
			flex-direction: 'row'

		content-css:
			flex: 1

	prop productFetcher
	prop orders

	def setup
		APP = self
		productFetcher = ProductFetcher.new(updateDelay: 500)
		productFetcher:sync = do render
		productFetcher.start
		orders = []

	def mount
		schedule

	def products
		productFetcher.products

	def isClosed
		productFetcher.isClosed

	def addProductToOrder product
		orders.push(product)

	def render
		<self .{@main-css}>
			<style> styles.toString
			<div .{@header-css}>
				<div> "BearStock v2"
			<div .{@content-css}>
				<BuyView>

tag BuyView
	styles.insert self,
		main-css:
			flex-direction: "row"

		column-css:
			flex: "1 0"
			flex-wrap: "wrap"
			overflow: "scroll"
			margin: "0 5px"

			"&.sidebar":
				flex: "0 0 200px"

		box-css:
			color: '#1E2022'
			margin: "5px 0"
			padding: "1em 0.5em"
			flex: '0 0 auto'

			border: '1px solid'
			border-top-color: '#dfdfdf'
			border-left-color: '#dfdfdf'
			border-right-color: '#808080'
			border-bottom-color: '#808080'

			"&.next":
				background: colors:background.darken(0.2).hex
				text-align: 'center'

			"& .header":
				flex-direction: "row"
				font-size: "12px"

			"& .code":
				font-weight: 'bold'
				width: '4em'

			"& .fill":
				flex: 1

		products-css:
			display: "grid"
			grid-template-columns: "repeat(auto-fill, minmax(200px, 1fr))"
			grid-gap: "10px"


	def postiveFilters
		@postiveFilters ?= []

	def negativeFilters
		@negativeFilters ?= []

	def products
		APP.products

	def collection
		@collection ?= ProductCollection.new(products, postiveFilters, negativeFilters)

	let MAX_FILTERS = 5

	def pendingFilters
		collection.pendingFilters.slice(0, MAX_FILTERS)

	def isTruncated
		collection.pendingFilters:length > MAX_FILTERS

	def applyFilter filter
		postiveFilters.push(filter)
		@collection = null

	def next
		for name in pendingFilters
			negativeFilters.push(name)
		@collection = null

	def clearFilters
		reset

	def reset
		@postiveFilters = []
		@negativeFilters = []
		@collection = null

	def buy product
		APP.addProductToOrder(product)

	def render
		if products !== collection.sourceProducts
			@collection = null

		<self .{@main-css}>
			<div .{@column-css}.sidebar> <ScrollHint> <div>
				if collection.isFiltered
					<div .{@box-css}.next :tap="clearFilters"> "Reset"

				for filter in pendingFilters
					<div .{@box-css} :tap=["applyFilter", filter]>
						filter

				if isTruncated and !collection.spansAllProducts(pendingFilters)
					<div .{@box-css}.next :tap="next"> "Next"

			<div .{@column-css}> <ScrollHint> <.{@products-css}>
				for product in collection.toArray
					<div.{@box-css} :tap=["buy", product]>
						<div.header>
							<div.code> product:code
							<div.fill>
							<div> "{product:absolute_cost} NOK"
						<div> "{product:brewery} {product:name}"

tag OrderList
	prop orders

	def render
		<self>
			for product in orders
				<div> product:name

tag ScrollHint
	prop content

	var spacing = '20px'

	tag Line
		prop text

		styles.insert self,
			main-css:
				position: 'relative'
				justifyContent: 'center'
				flexDirection: 'row'
				flex: '0 0 auto'
				fontSize: '0.5em'
				color: '#666'
				textTransform: 'uppercase'

			border-css:
				position: 'absolute'
				border-bottom: '1px solid #999'
				left: 0
				top: '0.6em'
				width: '100%'
				z-index: 1

			content-css:
				background: '#bfbfbf'
				padding: '0 1em'
				z-index: 10

		def render
			<self.{@main-css}>
				<.{@border-css}>
				<.{@content-css}> text

	styles.insert self,
		main-css:
			position: 'relative'

		top-css:
			position: 'absolute'
			top: 0
			height: spacing
			width: '100%'
			zIndex: 1000
			background: 'linear-gradient(to bottom, #bfbfbf, rgba(255,255,255,0))'

		bottom-css:
			position: 'absolute'
			bottom: 0
			height: spacing
			width: '100%'
			background: 'linear-gradient(to top, #bfbfbf, rgba(255,255,255,0))'
			zIndex: 1000

		scroller-css:
			flex: 1
			overflowY: 'scroll'
			overflow-scrolling: 'touch'

		filler-css:
			flex: '0 0 auto'
			height: spacing

	def scroller

	def render
		<self.{@main-css}>
			<.{@top-css}>
			<.{@bottom-css}>
			<.{@scroller-css}>
				<.{@filler-css}>
				<Line> "Start of list"
				content
				<Line> "End of list"
				<.{@filler-css}>

Imba.mount(<App>, document:body)
