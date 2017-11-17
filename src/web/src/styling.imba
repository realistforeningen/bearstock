var styles = require 'imba-styles'
var Color = require 'color'

require "./normalize.css"
require "./default.css"

export var winColors =
	desktop: Color("#008080")
	g1: Color('#dfdfdf')
	g2: Color('#bfbfbf')
	g3: Color('#808080')


export var h100 = styles.create height: '100%'
export var grow = styles.create flex: 1