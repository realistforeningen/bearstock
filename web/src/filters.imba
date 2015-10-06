export class ProductCollection
	def initialize(products, appliedFilters)
		@unfilteredCount = products:length
		@products = []

		@pendingFilters = []
		@pendingCounts = {}
		@appliedFilters = appliedFilters

		for product in products
			if matches(product)
				addProduct(product)

		cleanFilters

	def matches product
		for filter in @appliedFilters
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

	def appliedFilters
		@appliedFilters

	def pendingFilters
		@pendingFilters

	def toArray
		@products

	def count
		@products:length

	def isFiltered
		count < @unfilteredCount
		