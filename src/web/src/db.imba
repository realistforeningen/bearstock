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

	def fetchAll
		var data = await Promise.all [
			fetch("/products.json").then(tojson)
			fetch("/buyers.json").then(tojson)
			fetch("/orders.json").then(tojson)
		]
		products = data[0]:products
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

	def order product, buyer
		let req = fetch "/orders"
			method: 'post'
			headers: {'Content-Type': 'application/json'}
			body: JSON.stringify
				buyer_id: buyer:id
				product_code: product:code
				price: product:current_price
		await req
		fetchLoop


