var webpack = require('webpack');

module.exports = {
  entry: './src/main',

  output: {
  	filename: 'static/assets/main.js'
  },

  module: {
  	loaders: [
  	  { test: /\.imba$/, loader: 'imba-loader' }
  	]
  },

  resolve: {
  	extensions: ['', '.js', '.imba']
  }
}
