var webpack = require('webpack');

module.exports = {
  entry: {
    register: './src/web/src/register',
  },

  output: {
  	filename: 'src/web/static/assets/[name].js'
  },

  module: {
  	loaders: [
      { test: /\.css$/, loader: 'style-loader!raw-loader' }
  	]
  }
}
