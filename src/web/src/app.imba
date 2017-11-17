require 'whatwg-fetch'
extern fetch

require './styling'

import Register from './register'

window:startRegister = do |dom|
	Imba.mount(<Register>, dom)
