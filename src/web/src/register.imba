var Imba = require 'imba'

require 'whatwg-fetch'
extern fetch
var styles = require 'imba-styles'

var Color = require 'color'

require "./normalize.css"
require "./default.css"

import ProductCollection from "./filters"
import DB from "./db"

let colors =
	background: Color("#C9D6DF")

var h100 = styles.create height: '100%'
var grow = styles.create flex: 1

tag Window
	styles.insert self,
		main-css:
			margin: "20px"
			background: '#bfbfbf'
			padding: '5px'
			border: '1px solid'
			border-top-color: '#dfdfdf'
			border-left-color: '#dfdfdf'
			border-right-color: '#808080'
			border-bottom-color: '#808080'
			flex: 1

			"& > .header":
				background: 'linear-gradient(to right, #000080, #1084d0)'
				color: '#fff'
				padding: '0.5em 1em'
				flex-direction: 'row'

			"& > .content":
				flex: 1
	def render
		<self.{@main-css}>

tag Button < button
	styles.insert self,
		main-css:
			color: '#1E2022'
			margin: "5px 0"
			padding: "0.5em"

			background: "inherit"
			border-radius: 0

			border: '1px solid'
			border-top-color: '#dfdfdf'
			border-left-color: '#dfdfdf'
			border-right-color: '#808080'
			border-bottom-color: '#808080'

			font-weight: "bold"

			"&.cancel":
				font-weight: "normal"

	def render
		<self.{@main-css}>

tag Inset
	styles.insert self,
		main-css:
			background: 'white'
			border: '1px solid'
			border-top-color: '#000'
			border-left-color: '#000'
			border-bottom-color: '#dfdfdf'
			border-right-color: '#dfdfdf'

			"& > .body":
				border: '1px solid'
				border-top-color: '#808080'
				border-left-color: '#808080'
				border-bottom-color: '#fff'
				border-right-color: '#fff'
				padding: "10px"
				flex: 1

	def body
		<@body>

	def setContent content, type
		body.setChildren(content, type)
		self

	def render
		<self.{@main-css}>
			body

tag App
	prop db
	prop modal
	prop bluescreen

	styles.insert self,
		modal-css:
			position: "absolute"
			height: "100%"
			width: "100%"
			display: "flex"
			align-items: "center"
			justify-content: "center"

			"& > .backdrop":
				background: "black"
				z-index: 2000
				opacity: 0.3
				position: "absolute"
				top: 0
				right: 0
				bottom: 0
				left: 0

			"& > *":
				z-index: 3000

	def setup
		APP = self
		db = DB.new(updateDelay: 500)
		db:sync = do render
		db.start

	def mount
		schedule

	def products
		db.products

	def isClosed
		db.isClosed

	def cancelModal
		if modal?.keepModalOpen
			# do nothing
		else
			modal = null

	def buyers
		db.buyers

	def superfail
		bluescreen = <Bluescreen>

	def render
		<self .{h100}>
			<style> styles.toString
			if bluescreen
				bluescreen.end
			else
				<Window .{h100}>
					<.header>
						<p> "BearStock v2"
					<.content>
						<BuyView.{grow}>
	
				if modal
					<.{@modal-css}>
						modal.end
						<.backdrop :tap="cancelModal">

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

			"&.list":
				flex: "0 0 auto"
				max-width: "300px"

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
		APP.modal = <BuyerSelection product=product>

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

			<div .{@column-css}> <ScrollHint.{grow}> <.{@products-css}>
				for product in collection.toArray
					<div.{@box-css} :tap=["buy", product]>
						<div.header>
							<div.code> product:code
							<div.fill>
							<div> "{product:current_price} NOK"
						<div> "{product:producer} {product:name}"

			<div .{@column-css}.list> <OrderList[APP.db.orders]>

tag BuyProduct
	styles.insert self,
		grid-css:
			display: "grid"
			grid-template-columns: "100px 1fr"
			grid-row-gap: "5px"
			font-size: "14px"
			padding: "10px 5px 5px"
			min-width: "400px"

			"& > .right":
				grid-column: 2

			"& > .buttons":
				flex-direction: "row"
				font-size: "18px"

		accept-css:
			margin-right: "14px"

	prop buyer
	prop product
	prop isBuying

	def keepModalOpen
		isBuying

	def accept
		if isBuying
			return

		isBuying = yes

		await APP.db.order(product, buyer)
			.catch(do APP.superfail)

		isBuying = no
		cancel
		APP.render

	def cancel
		APP.cancelModal

	def render
		<self> <Window>
			<.header> product:name
			<.content.{@grid-css}>
				<p> "Code"
				<p> <strong> product:code
				<p> "Producer"
				<p> product:producer
				<p> "Name"
				<p> product:name
				<p> "Price"
				<p> "{product:current_price} NOK"
				<p> "Buyer"
				<p.right>
					buyer:name
					" "
					buyer:icon

				if isBuying
					<div.right> "Buying…"
				else
					<div.right.buttons>
						<Button .{@accept-css} :tap="accept"> "Accept"
						<Button.cancel :tap="cancel"> "Cancel"

tag BuyerSelection
	prop product

	styles.insert self,
		buyers-css:
			margin: "14px 0"
			flex-direction: "row"
			flex-wrap: "wrap"
			font-size: "30px"
			max-width: "400px"

			"& > p":
				padding: "0 5px"

	def selectBuyer buyer
		APP.modal = <BuyProduct product=product buyer=buyer>

	def render
		<self> <Window>
			<.header> "Buyer Identification"
			<.content>
				<.{@buyers-css}>
					for buyer in APP.buyers
						<p :tap=["selectBuyer", buyer]> buyer:icon

tag OrderList
	def orders
		data

	styles.insert self,
		main-css:
			margin: "18px 0"
			flex: 1

			"& > .Inset":
				flex: 1

		header-css:
			font-weight: "bold" 

		order-css:
			flex-direction: "row"
			font-size: "14px"
			align-items: "baseline"

			"& > .left":
				margin-right: "18px"

	def render
		<self.{@main-css}> <Inset>
			<div .{@header-css}> "Latest orders"
			if !orders
				<div> "Loading…"
				
			for order in orders
				var buyer = APP.db.findBuyer(order:buyer_id)
				<div .{@order-css}>
					<div.left> "{buyer:name} {buyer:icon}"
					<div .{grow}>
					<div> "{order:product_code} — {order:absolute_cost} NOK"


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

tag Bluescreen
	styles.insert self,
		main-css:
			background: "blue"
			color: "white"
			font-weight: "bold"
			font-family: "monospace"
			flex: 1
			align-items: "center"
			justify-content: "center"
			padding: "20px 0"

			"& > p":
				max-width: "600px"

	def render
		<self.{@main-css}>
			<p> "A problem has been detected and Windows has been shut down to prevent damange to your life"

Imba.mount(<App>, document:body)
