extern fetch

let tojson = do |res|
	if res:status == 200
		res.json
	else
		throw Error.new("Wrong status code: {res:status}")

export class ProductFetcher
	prop state
	prop products
	prop priceId
	prop failing

	def initialize(options = {})
		@updateDelay = options:updateDelay
		@products = []

	def sync
		# Override

	def start
		fetchProducts

	def isClosed
		products && !priceId

	def fetchProducts
		fetch("/products")
			.then(tojson)
			.then do |data|
				failing = no
				updateProducts(data)
			.catch do
				failing = yes
				sync
			.then do
				setTimeout(&, 10*1000) do fetchProducts

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

