var webpack = require('webpack');

module.exports = {
  entry: {
    app: './src/web/src/app',
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
