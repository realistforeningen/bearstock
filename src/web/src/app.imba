require 'whatwg-fetch'
extern fetch

require './styling'

import Register from './register'


var styles = require 'imba-styles'

window:insertStyles = do
	document:body.appendChild((<style> styles).dom)

window:startRegister = do |dom|
	Imba.mount(<Register>, dom)

import EmojiPicker from './emoji-picker'

window:startEmojiPicker = do |dom, props|
	Imba.mount(<EmojiPicker current=props:currentIcon unavailable=props:usedIcons>, dom)


import Stats from './stats'
window:startStats = do |dom|
	Imba.mount(<Stats>, dom)