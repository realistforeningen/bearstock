let fetch = require 'whatwg-fetch'

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

	def sync
		# Override

	def start
		fetchProducts

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
		priceId = data:priceId
		sync

	def updateProducts data
		if !priceId
			updateProductsNow(data)
			return

		products = null
		priceId = null
		sync

		setTimeout(&, 1000) do
			updateProductsNow(data)

