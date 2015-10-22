require 'imba/src/imba/browser'
let fetch = require 'whatwg-fetch'
Object:assign = require 'object-assign'

let styles = require 'imba-styles'

import ProductCollection from "./filters"
import ProductFetcher from "./loader"
import animate from "./animation"

require "./normalize.css"
require "./default.css"

var mainApp

def window.startApp
	mainApp = <app>
	document:body.appendChild mainApp.dom

let grow = styles.css flex: 1
let bold = styles.css fontWeight: 'bold'
let screen = styles.css height: '100%'
let hbox = styles.css flexDirection: 'column'
let flash = styles.css
	animationName: 'flash'
	animationDuration: '300ms'
	animationIterationCount: 1

let tojson = do |res|
	if res:status == 200
		res.json
	else
		throw "Wrong status code: {res:status}"

let eventually = do |duration, start, cb|
	do |res|
		let pending = duration - (Date.new - start)
		if pending < 0
			cb(res)
		else
			setTimeout(&, pending) do cb(res)


let atleast = do |promise, duration|
	let start = Date.new
	Promise.new do |resolver, rejecter|
		promise
			.then(eventually(duration, start, resolver))
			.catch(eventually(duration, start, rejecter))

tag app
	prop productFetcher
	prop buyer
	prop orders
	prop orderState

	def failing
		productFetcher.failing

	def products
		productFetcher.products

	def priceId
		productFetcher.priceId

	def renderContinously
		setInterval(&, 500) do
			render

	def build
		productFetcher = ProductFetcher.new
		productFetcher:sync = do render
		productFetcher.start
		styles.freeze
		super
		renderContinously
		self

	let main = styles.css
		height: '100%'
		flexDirection: 'column'

	let fail-css = styles
		color: '#f00'
		margin-left: '2em'

	let header = styles.css
		background: '#1E2022'
		borderBottom: '3px solid #52616B'
		color: '#fff'
		padding: '0.5em 1em'

	let content = styles.css
		flex: 1
		justifyContent: 'center'

	def render
		if !buyer
			orders = []

		<self styles=main>
			<style> styles.toString
			<div styles=header>
				<div> "BearStock v1"
				if failing
					<div styles=fail-css> "Connection lost"
				<div styles=grow>
				<div> Date.new.toString
			<div styles=content>
				if buyer
					if products
						<buy-view@buy disabled=isLocked>
					else
						<loading-view>
				else
					<login-view>

	def addProductToOrder product
		orders.push product
		render

	def removeOrder idx
		orders.splice(idx, 1)
		render

	def clearOrder
		orders = []
		orderState = null
		render

	def isLocked
		!!orderState

	def pay
		Object.freeze(orders)
		orderState = "paying"
		render

		# TODO: Refactor into generic JSON-request?
		# TODO: Don't send name/tags
		let req = fetch "/orders"
			method: 'post'
			headers: {'Content-Type': 'application/json'}
			body: JSON.stringify
				buyer_id: buyer:id
				price_id: priceId
				orders: orders

		let startTime = Date.new

		atleast(req, 500).then do |res|
			if res:status != 200
				# TODO: Handle this better
				window.alert("Payment failed!")
			orderState = "paid"
			render

	def login newBuyer
		buyer = newBuyer
		render

	def logout
		clearOrder
		buyer = null
		@buy.reset if @buy
		render

tag loading-view
	let main = styles.css
		fontSize: '3em'
		fontWeight: 'bold'

		flexDirection: 'column'
		justifyContent: 'center'

	def render
		<self styles=main>
			<div> "Loading prices…"

tag buy-view
	prop disabled
	prop appliedFilters

	def appliedFilters
		@appliedFilters ?= []

	def products
		mainApp.products

	def collection
		@collection ?= ProductCollection.new(products, appliedFilters)

	let main = styles.css
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
		flex: '0 0 auto'

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
				<order-list@order-list>

	def alert
		@order-list.alert

	def removeFilter idx
		return alert if disabled

		@appliedFilters.splice(idx, 1)
		@collection = null
		render

	def applyFilter name
		return alert if disabled
		@appliedFilters.push(name)
		@collection = null
		render

	def clearFilters
		return alert if disabled
		reset
		render

	def reset
		@appliedFilters = []
		@collection = null

	def buy product, evt
		return alert if disabled

		let button = evt.target.closest(".{boxStyle.className}")
		if animate(button, flash)
			mainApp.addProductToOrder product

tag login-view
	let main = styles.css
		fontSize: '42px'
		flexDirection: 'column'
		alignItems: 'center'

	let header = styles.css
		marginTop: '16px'

	def go number
		@pad.clear
		@error = null

		@isLoading = yes
		render

		let p = fetch("/buyer?id={number}")
		atleast(p, 500)
			.then(tojson)
			.then do |data|
				@isLoading = no
				if data:buyer
					mainApp.login(data:buyer)
				else
					@error = "Error: Unknown trader code"
				render
			.catch do |err|
				@isLoading = no
				@error = "Error: Server failed"
				render

	let error-css = styles
		color: 'red'
		font-size: '0.5em'
		font-weight: 'bold'
		margin-top: '5px'

	let pending-css = styles
		margin-top: '15px'
		font-size: '1.5em'
		color: '#1E2022'

	def render
		<self styles=main>
			<div styles=header> "Enter trader code"
			if @isLoading
				<div styles=pending-css> "Logging in..."
			else
				if @error
					<div styles=error-css> @error
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
		background: 'linear-gradient(to bottom, white, rgba(255,255,255,0))'

	let bottomGradient = styles.css
		position: 'absolute'
		bottom: 0
		height: spacing
		width: '100%'
		background: 'linear-gradient(to top, white, rgba(255,255,255,0))'
		zIndex: 1000

	let scrollerStyles = styles.css
		flexDirection: 'inherit'
		flex: '1 0 0'
		overflowY: 'scroll'
		overflow-scrolling: 'touch'

	let contentStyles = styles.css
		flexDirection: 'inherit'
		flex: '0 0 auto'

	let lineText = styles.css
		flex: '0 0 auto'
		fontSize: '0.5em'
		color: '#ccc'
		textTransform: 'uppercase'

	let filler = styles.css
		flex: '0 0 auto'
		height: spacing

	def scroller
		<div@scroller styles=scrollerStyles>
			<div styles=filler>
			<div styles=lineText> <line> "Start of list"
			content
			<div styles=lineText> <line> "End of list"
			<div styles=filler>

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
	def orders
		mainApp.orders

	def orderState
		mainApp.orderState

	def buyer
		mainApp.buyer

	def total
		var amount = 0
		for order in orders
			amount += order:price
		amount

	let main = styles.css
		padding: '30px 0'
		flexDirection: 'column'
		overflow: 'hidden'

	let name = styles.css
		marginBottom: '1em'
		fontSize: '1.2em'

	let extra = styles.css
		color: '#333'

	let totalStyle = styles.css
		fontSize: '2em'

	let buttons = styles.css
		flexDirection: 'row'
		justifyContent: 'space-between'

	let button = styles.css
		padding: '1em 1em'
		borderRadius: '10px'
		margin: '0.5em 0 1em'
		alignSelf: 'flex-start'
		
	let positive = styles.css
		background: '#27ae60'

	let negative = styles.css
		background: '#E84545'

	let neutral = styles.css
		background: '#C9D6DF'

	let orderStyle = styles.css
		fontSize: '0.8em'
		alignSelf: 'flex-start'
		margin: "5px 0"


	def render
		<self styles=main>
			<div styles=hbox>
				<div styles=name> "Welcome {buyer:name}"
				<div styles=extra>
					if orderState == "paid"
						"You paid:"
					else
						"Amount to pay:"

				<div styles=totalStyle> "{total} NOK"

				<div styles=buttons>
					if orderState == "paying"
						<div@pendingButton styles=[button, neutral]>
							<span> "Confirming order"
							<blinker interval=1> "…"
					elif orderState == "paid"
						<div@paidButton styles=[button, positive] :tap="logout">
							<span> "Order confirmed! Log out."
					elif orders:length
						<div styles=[button, negative] :tap="abort"> "Abort"
						<div styles=[button, positive] :tap="confirm"> "Confirm"
					
				if orders:length
					<div> "Order:"

					for order, idx in orders
						<div@{idx} styles=orderStyle :tap=["remove", idx]> "1 \u00d7 {order:name} @ {order:price} NOK"
				else
					<div styles=[button, neutral] :tap="logout"> "Log out"

	def alert
		if orderState == "paying"
			animate(@pendingButton, flash)
		else
			animate(@paidButton, flash)

	def remove idx
		mainApp.removeOrder idx

	def abort
		mainApp.clearOrder

	def confirm
		mainApp.pay

	def logout
		mainApp.logout

tag blinker < span
	prop interval
	prop visible
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
		visible = yes
		setVisibleTimeout
		super

	def commit
		# don't render
		self

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

	def commit
		self

	def render
		<self styles=main>
			<div>
				<span> (@number.toString if @number)
				<blinker interval=0.5> "_"
			<div styles=pad>
				for i in [1 .. 9]
					<button@{i} styles=button :tap=["press", i]> i.toString
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
		
