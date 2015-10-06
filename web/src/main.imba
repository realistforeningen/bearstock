require 'imba'
require 'whatwg-fetch'
extern fetch

let styles = require 'imba-styles'

import ProductCollection from "./filters"

var mainApp

def window.startApp
	mainApp = <app>
	document:body.appendChild mainApp.dom

let tojson = do |data| data.json

extend class ElementTag
	def commit
		render
		self

let grow = styles.css flex: 1
let bold = styles.css fontWeight: 'bold'
let screen = styles.css height: '100%'
let hbox = styles.css flexDirection: 'column'

tag app
	prop priceId
	prop buyer
	prop products
	prop orders

	def fetchProducts
		fetch("/products")
			.then(tojson)
			.then do |data|
				updateProducts(data)

	def updateProductsNow data
		products = data:products
		priceId = data:price_id
		render

	def updateProducts data
		if !priceId
			updateProductsNow data
			return

		if data:price_id === priceId
		 	return

		# Avoid updating the UI beneath the user's finger
		products = null
		render

		setTimeout(&, 2000) do
			updateProductsNow data

	def renderContinously
		@tick = do
			window:requestAnimationFrame(@tick)
			render

		@tick()

	def build
		super
		styles.freeze
		fetchProducts
		renderContinously
		self

	let main = styles.css
		height: '100%'
		display: 'flex'
		flexDirection: 'column'

	let header = styles.css
		background: '#1E2022'
		borderBottom: '3px solid #52616B'
		color: '#fff'
		padding: '0.5em 1em'
		display: 'flex'

	let content = styles.css
		flex: 1
		display: 'flex'
		justifyContent: 'center'

	def render
		if !buyer
			orders = []

		<self styles=main>
			<style> styles.toString
			<div styles=header>
				<div> "BearStock v1"
				<div styles=grow>
				<div> Date.new.toString
			<div styles=content>
				if buyer
					if products
						<buy-view>
					else
						<div> "Loading..."
				else
					<login-view>

	def addProductToOrder product
		orders.push product

	def removeOrder idx
		orders.splice(idx, 1)

	def pay
		orders = []

	def login number
		buyer = {
			id: number
			name: "Magnus"
		}

tag buy-view
	prop appliedFilters

	def appliedFilters
		@appliedFilters ?= []

	def products
		mainApp.products

	def collection
		@collection ?= ProductCollection.new(products, appliedFilters)

	let main = styles.css
		display: 'flex'
		flexDirection: 'row'
		alignItems: 'stretch'
		flex: 1

	let column = styles.css
		padding: '0 2em'
		flex: 1
		flexDirection: 'column'

	let mainColumn = styles.css
		flex: 2

	let filterStyle = styles.css
		color: 'red'

	let notice = styles.css
		color: '#C9D6DF'
		fontSize: '0.8em'
		padding: '1em'
		paddingTop: '0.5em'
		marginBottom: '1em'
		textAlign: 'center'
		borderBottomLeftRadius: '10px'
		borderBottomRightRadius: '10px'
		background: '#52616B'

	let header = styles.css
		fontSize: '1.5em'

	let boxStyle = styles.css
		borderRadius: '10px'
		background: '#C9D6DF'
		color: '#1E2022'
		margin: "5px 0"
		padding: "1em 0.5em 1em 1em"

		display: 'flex'
		flexDirection: 'row'
		alignItems: 'baseline'

	let mark = styles.css
		fontWeight: 'bold'
		fontSize: '1em'
		height: 0


	def render
		<self styles=main>
			<div styles=column>
				<scroll-hint>
					# TODO: Can we refactor this into one thingie?
					<div styles=hbox> for filter,idx in collection.appliedFilters
						<div@{idx} styles=[boxStyle] :tap=["removeFilter", idx]>
							<div styles=mark> "\u2612"
							<div> filter

					<div styles=hbox> for filter,idx in collection.pendingFilters
						<div@{idx} styles=[boxStyle] :tap=["applyFilter", filter]>
							<div styles=mark> "\u2610"
							<div> filter
			<div styles=[column, mainColumn]>
				if collection.isFiltered
					<div styles=notice :tap="clearFilters"> "Only showing {collection.count} of {products:length} products. Tap here to clear filters."

				<scroll-hint>
					for product,idx in collection.toArray
						<div@{idx} styles=boxStyle :tap=["buy", product]>
							<div> product:name
							<div styles=grow>
							<div styles=bold> "{product:price} NOK"

			<div styles=column>
				<order-list orders=mainApp.orders>

	def removeFilter idx
		@appliedFilters.splice(idx, 1)
		@collection = null

	def applyFilter name
		@appliedFilters.push(name)
		@collection = null

	def clearFilters
		@appliedFilters = []
		@collection = null

	def buy product
		mainApp.addProductToOrder product

tag login-view
	let main = styles.css
		fontSize: '42px'
		display: 'flex'
		flexDirection: 'column'
		alignItems: 'center'

	let header = styles.css
		marginTop: '16px'

	def go number
		@pad.clear
		mainApp.login(number)

	def render
		<self styles=main>
			<div styles=header> "Enter trader code"
			<key-pad@pad :go="go">


tag scroll-hint
	prop contentStyles

	let spacing = '30px'

	let main = styles.css
		position: 'relative'
		flex: '1 0 0'
		flexDirection: 'inherit'

	let topGradient = styles.css
		position: 'absolute'
		top: 0
		height: spacing
		width: '100%'
		zIndex: 1000
		background: 'linear-gradient(to bottom, white, rgba(255,255,255,0)'

	let bottomGradient = styles.css
		position: 'absolute'
		bottom: 0
		height: spacing
		width: '100%'
		background: 'linear-gradient(to top, white, rgba(255,255,255,0)'
		zIndex: 1000

	let scrollerStyles = styles.css
		flexDirection: 'inherit'
		flex: '1 0 0'
		overflowY: 'scroll'
		padding: "{spacing} 0"

	let contentStyles = styles.css
		flexDirection: 'inherit'

	let lineText = styles.css
		fontSize: '0.5em'
		color: '#ccc'
		textTransform: 'uppercase'


	def scroller
		<div@scroller styles=scrollerStyles>
			<div styles=lineText> <line> "Start of list"
			content
			<div styles=lineText> <line> "End of list"

	def content
		<div@content styles=contentStyles>

	def setContent c
		content.setContent c
		self

	def render
		<self styles=main>
			<div styles=topGradient>
			<div styles=bottomGradient>
			scroller

tag line
	prop text
	prop borderStyle

	let main = styles.css
		position: 'relative'
		justifyContent: 'center'
		flexDirection: 'row'
		flex: '1 0 0'

	let border = styles.css
		position: 'absolute'
		border-bottom: '1px solid #999'
		left: 0
		top: '0.6em'
		width: '100%'
		z-index: 1

	let content = styles.css
		background: 'white'
		padding: '0 1em'
		z-index: 100

	def render
		<self styles=main>
			<div styles=[border, borderStyle]>
			<div styles=content> text


tag order-list
	prop orders

	def total
		var amount = 0
		for order in orders
			amount += order:price
		amount

	let main = styles.css
		padding: '30px 0'
		flexDirection: 'column'
		overflow: 'hidden'

	let extra = styles.css
		color: '#333'

	let totalStyle = styles.css
		fontSize: '2em'

	let confirm = styles.css
		background: '#E84545'
		padding: '1em 1em'
		alignSelf: 'flex-start'
		borderRadius: '10px'
		margin: '0.5em 0 1em'

	let orderStyle = styles.css
		background: '#C9D6DF'
		padding: '1em 1em'
		alignSelf: 'flex-start'
		borderRadius: '10px'
		margin: "5px 0"


	def render
		<self styles=main>
			<div styles=hbox>
				<div styles=extra> "Amount to pay:"
				<div styles=totalStyle> "{total} NOK"

			if orders:length
				<div styles=confirm :tap="confirm"> "Confirm"

				<div> "Order:"

				for order, idx in orders
					<div@{idx} styles=orderStyle :tap=["remove", idx]> "1 \u00d7 {order:name}"

	def remove idx
		mainApp.removeOrder idx

tag blinker < span
	prop interval
	prop visible, default: true
	prop timeout

	def setVisibleTimeout
		if timeout
			return

		timeout = setTimeout(&, interval * 1000) do
			timeout = null
			visible = !visible
			render
			setVisibleTimeout

	def build
		setVisibleTimeout
		super

	def render
		if visible
			css 'visibility', 'visible'
		else
			css 'visibility', 'hidden'

tag key-pad
	let main = styles.css
		width: '6em'
		flexWrap: 'wrap'

	let button = styles.css
		width: '33%'
		height: '2em'

	let pad = styles.css
		flexWrap: 'wrap'

	let go = styles.css
		background: 'red'

	def render
		<self styles=main>
			<div>
				<span> @number
				<blinker interval=0.5> "_"
			<div styles=pad>
				for i in [1 .. 9]
					<button@{i} styles=button :tap=["press", i]> i
				<button styles=button :tap="clear"> "X"
				<button styles=button :tap=["press", 0]> "0"
				if @number
					<button styles=[button, go] :tap="go"> "Go"

	def press num, evt
		evt.cancel
		if @number
			@number = @number*10 + num
		else
			@number = num
		render

	def clear evt
		evt.cancel if evt
		@number = null
		render

	def go evt
		evt.cancel
		ongo(@number)
		
