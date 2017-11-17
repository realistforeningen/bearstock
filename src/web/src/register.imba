var styles = require 'imba-styles'

import ProductCollection from "./filters"
import DB from "./db"

import Window, Button, Inset from "./win98"

import h100, grow, winColors from './styling'

export tag Register
	prop db
	prop modal
	prop override
	prop currentError watch: yes

	styles.insert self,
		main-css:
			background: winColors:desktop
			position: "fixed"
			width: "100%"
			height: "100%"

			"& > .Window":
				margin: "20px"

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
		db:sync = do
			currentError = db.error
			render
		db.start

	def mount
		schedule(interval: 100)

	def products
		db.products

	def isClosed
		db.isClosed

	def cancelModal
		if modal?.keepModalOpen
			# do nothing
		else
			modal = null

	def currentErrorDidSet new
		if new
			override = <Bluescreen error=new>
		else
			override = null

	def buyers
		db.buyers

	def render
		<self .{@main-css}>
			if override
				override.end
			else
				<Window .{grow}>
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
			margin: "5px 0"
			padding: "1em 10px"
			flex: '0 0 auto'

			"&.next":
				background: winColors:g2.darken(0.1)
				text-align: 'center'

			"& .header":
				flex-direction: "row"
				font-size: "14px"

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
					<Button.{@box-css}.next :tap="clearFilters"> "Reset"

				for filter in pendingFilters
					<Button.{@box-css} :tap=["applyFilter", filter]>
						filter

				if isTruncated and !collection.spansAllProducts(pendingFilters)
					<Button.{@box-css}.next :tap="next"> "Next"

			<div .{@column-css}> <ScrollHint.{grow}> <.{@products-css}>
				for product in collection.toArray
					<Button.{@box-css} :tap=["buy", product]>
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

			"& .Button":
				padding: "0.5em 1em"

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
						<Button.bold.{@accept-css} :tap="accept"> "Accept"
						<Button :tap="cancel"> "Cancel"

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
				<div .{@order-css}>
					<div.left> "{order:buyer:name} {order:buyer:icon}"
					<div .{grow}>
					<div> "{order:product_code} — {order:price} NOK"


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
	prop error

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

			"& p":
				margin-bottom: "1em"
				max-width: "600px"

	def render
		<self.{@main-css}>
			<div>
				<p> "A problem has been detected and Windows has been shut down to prevent damage to your life"
				if error
					<p> "Error message: {error}"
