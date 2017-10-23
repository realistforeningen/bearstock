export class ProductCollection
	prop sourceProducts

	def initialize(products, positiveFilters, negativeFilters)
		@sourceProducts = products
		@products = []

		@pendingFilters = []
		@pendingCounts = {}
		@positiveFilters = positiveFilters
		@negativeFilters = negativeFilters

		for product in products
			if matches(product)
				addProduct(product)

		cleanFilters
		sortData

	def matches product
		for filter in @negativeFilters
			if filter in product:tags
				return false

		for filter in @positiveFilters
			if !(filter in product:tags)
				return false

		return true

	def addProduct product
		for t in product:tags
			if !(t in @appliedFilters)
				if !(t in @pendingFilters)
					@pendingFilters.push(t)
					@pendingCounts[t] = 0

				@pendingCounts[t] += 1

		@products.push(product)

	def cleanFilters
		let idx = 0
		while idx < @pendingFilters:length
			let filter = @pendingFilters[idx]
			if @pendingCounts[filter] == @products:length
				# The filter already matches all the products
				@pendingFilters.splice(idx, 1)
			else
				idx++


	def sortData
		@pendingFilters.sort do |a, b|
			@pendingCounts[b] - @pendingCounts[a]

		@products.sort do |a, b|
			a:code.localeCompare(b:code)

		if @positiveFilters:length == 0 and @negativeFilters:length == 0
			let defaultBeers = ["FYPA", "FYBY", "FYPL"] # reverse order
			for code in defaultBeers
				for idx in [0 ... @products:length]
					let product = @products[idx]
					if product:code == code
						@products.splice(idx, 1)
						@products.unshift(product)
						break

	def spansAllProducts(filterList)
		let matchingCount = 0

		for product in @products
			for t in product:tags
				if t in filterList
					matchingCount += 1
					break

		return matchingCount == count

	def pendingFilters
		@pendingFilters

	def toArray
		@products

	def count
		@products:length

	def isFiltered
		count < sourceProducts:length
		