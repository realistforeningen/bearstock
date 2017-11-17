var styles = require 'imba-styles'

import winColors from './styling'

export tag Window
	styles.insert self,
		main-css:
			background: winColors:g2
			padding: '5px'

			border: '1px solid'
			border-top-color: winColors:g1
			border-left-color: winColors:g1
			border-bottom-color: winColors:g3
			border-right-color: winColors:g3

			"& > .header":
				background: 'linear-gradient(to right, #000080, #1084d0)'
				color: '#fff'
				padding: '0.5em 1em'
				flex-direction: 'row'

			"& > .content":
				flex: 1
	def render
		<self.{@main-css}>

export tag Button < button
	styles.insert self,
		main-css:
			text-align: "left"
			padding: 0

			background: "inherit"
			border-radius: 0

			border: '1px solid'
			border-top-color: winColors:g1
			border-left-color: winColors:g1
			border-bottom-color: winColors:g3
			border-right-color: winColors:g3

			outline: 0

			"&.bold":
				font-weight: "bold"

	def render
		<self.{@main-css}>

export tag Inset
	styles.insert self,
		main-css:
			background: 'white'

			border: '1px solid'
			border-top-color: '#000'
			border-left-color: '#000'
			border-bottom-color: winColors:g3
			border-right-color: winColors:g3

			"& > .body":
				border: '1px solid'
				border-top-color: winColors:g3
				border-left-color: winColors:g3
				border-bottom-color: '#fff'
				border-right-color: '#fff'
				padding: "10px"
				flex: 1

	def body
		<@body>

	def setContent content, type
		body.setChildren(content, type)
		self

	def render
		<self.{@main-css}> body
