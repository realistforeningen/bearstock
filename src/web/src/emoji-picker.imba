var emojis = require 'emojibase-data/en/data.json'
import groups, subgroups, hierarchy from 'emojibase-data/meta/groups.json'

var styles = require 'imba-styles'

export tag EmojiPicker
	prop active

	styles.insert self,
		grid-css:
			flex-direction: 'row'
			flex-wrap: 'wrap'

			'& p':
				font-size: "30px"
				padding: "5px"

				"&.active":
					background: '#ddd'
					outline: '1px solid #333'

	def mount
		schedule

	def render
		<self>
			<input type="hidden" name="icon" value=active>
			<div.{@grid-css}>
				for emoji in emojis
					if emoji:version < 5
						<p.active=(active == emoji:emoji) :tap=["setActive", emoji:emoji]> emoji:emoji
