extern fetch

let tojson = do |res|
	if res:status == 200
		res.json
	else
		throw Error.new("Wrong status code: {res:status}")

export class DB
	prop state
	prop products
	prop buyers
	prop orders
	prop priceId
	prop error

	def initialize(options = {})
		@updateDelay = options:updateDelay
		@products = []
		@buyers = []
		@orders = null
		@timeout = null
		@error = null

	def sync
		# Override

	def start
		fetchLoop

	def isClosed
		products && !priceId

	def fetchAll
		var data = await Promise.all [
			fetch("/products.json").then(tojson)
			fetch("/buyers.json").then(tojson)
			fetch("/orders.json").then(tojson)
		]
		updateProducts(data[0])
		buyers = data[1]:buyers
		orders = data[2]:orders

	def fetchLoop
		if @timeout
			clearTimeout(@timeout)

		fetchAll
			.then(do error = null)
			.catch(do |err| error = err)
			.then do
				sync
				@setTimeout = setTimeout(&, 10*1000) do fetchLoop

	def updateProductsNow data
		products = data:products
		priceId = data:price_id
		sync

	def updateProducts data
		if !priceId or !@updateDelay
			updateProductsNow(data)
			return

		if priceId == data:price_id
			return

		products = null
		priceId = null
		sync

		setTimeout(&, @updateDelay) do
			updateProductsNow(data)

	def findBuyer id
		for buyer in buyers
			if buyer:id == id
				return buyer
		return null

	def order product, buyer
		orders = null

		let req = fetch "/orders"
			method: 'post'
			headers: {'Content-Type': 'application/json'}
			body: JSON.stringify
				buyer_id: buyer:id
				product_code: product:code
				price: product:current_price
		await req
		fetchLoop


