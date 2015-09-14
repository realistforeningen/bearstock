extern fetch

var mainApp

def window.startApp
	mainApp = <app>
	document:body.appendChild mainApp.dom

let tojson = do |data| data.json

extend class ElementTag
	def commit
		render
		self

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
		setTimeout(&, 200) do
			render
			renderContinously

	def build
		super
		fetchProducts
		renderContinously
		self

	def render
		if !buyer
			orders = []

		<self>
			<.header>
				<.title> "BearStock v1"
				<.grow>
				<.ts> Date.new.toString
			<.content>
				if buyer
					<.left>
						<product-list products=products disabled=!buyer>
					<.right>
						if buyer
							<div> "Welcome {buyer:name}"
							<order-list orders=orders>
				else
					<.trader>
						<.header> "Enter trader code"
						<key-pad@pad :go="login">

	def addProductToOrder product
		orders.push product
		render

	def removeOrder idx
		orders.splice(idx, 1)
		render

	def pay
		orders = []
		render

	def login number
		@pad.clear
		buyer = {
			id: number
			name: "Magnus"
		}
		render

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
	def render
		<self>
			<div.label>
				<span.num> @number
				<blinker.cursor interval=0.5> "_"
			<.pad>
				for i in [1 .. 9]
					<button .number :tap=["press", i]> i
				<button .number :tap="clear"> "X"
				<button .number :tap=["press", 0]> "0"
				if @number
					<button .number.go :tap="go"> "Go"

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
		
