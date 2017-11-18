var emojis = require 'emojibase-data/en/data.json'
import groups, subgroups, hierarchy from 'emojibase-data/meta/groups.json'

var styles = require 'imba-styles'

export tag EmojiPicker
	prop current
	prop unavailable

	styles.insert self,
		grid-css:
			flex-direction: 'row'
			flex-wrap: 'wrap'

			'& p':
				font-size: "30px"
				padding: "5px"
				border-radius: '5px'
				border: '1px solid #fff'

				"&.current":
					background: '#ddd'
					border: '1px solid green'

				"&.unavailable":
					background: '#666'
					opacity: 0.3

	def mount
		schedule

	def render
		<self>
			<input type="hidden" name="icon" value=current>
			<div.{@grid-css}>
				for emoji in emojis when emoji:version < 5
					if emoji:emoji in unavailable
						<p.unavailable> emoji:emoji
					else
						<p.current=(current == emoji:emoji) :tap=["setCurrent", emoji:emoji]> emoji:emoji
