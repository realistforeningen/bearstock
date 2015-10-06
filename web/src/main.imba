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

	let header = styles.css
		background: '#c0392b'
		color: '#ecf0f1'
		padding: '0.5em 1em'
		display: 'flex'

	let content = styles.css
		display: 'flex'
		justifyContent: 'center'

	let trader = styles.css

	let traderHeader = styles.css
		margin: "16px 0 0"

	def render
		if !buyer
			orders = []

		<self>
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
		flex: 1

	def render
		<self styles=main>
			<div styles=grow>
				for filter,idx in collection.pendingFilters
					<div@{idx} :tap=["applyFilter", filter]> filter
			<div styles=grow>
				for product,idx in collection.toArray
					<div@{idx}> product:name
			<div styles=grow>
				<order-list orders=mainApp.orders>

	def applyFilter name
		@appliedFilters.push(name)
		@collection = null

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


tag product-list
	prop products
	prop disabled

	def render
		if !products
			<self>
				<h2> "Loading..."
			return

		<self .enabled=!disabled>
			for product in products
				<button@{product:code} .button :tap=["buy", product]>
					<p> product:name
					<p> "{product:price} NOK"

	def buy product, evt
		evt.cancel
		mainApp.addProductToOrder product

tag order-list
	prop orders

	def total
		var amount = 0
		for order in orders
			amount += order:price
		amount

	def commit
		render

	def render
		<self>
			<h2> "Order"
			for order, idx in orders
				<p :tap=["remove", idx]> order:name
			<p> "Total: {total}"
			if orders:length
				<button :tap="confirm"> "Confirm"

	def confirm evt
		evt.cancel
		onconfirm(orders)

	def remove idx, evt
		evt.cancel
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

	let button = styles.css
		width: '33%'
		height: '2em'

	let go = styles.css
		background: 'red'

	def render
		<self styles=main>
			<div>
				<span> @number
				<blinker interval=0.5> "_"
			<div>
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
		
