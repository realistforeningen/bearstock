var webpack = require('webpack');

module.exports = {
  entry: {
    register: './src/register',
    stats: './src/stats'
  },

  output: {
  	filename: 'static/assets/[name].js'
  },

  module: {
  	loaders: [
  	  { test: /\.imba$/, loader: 'imba-loader' },
      { test: /\.css$/, loader: 'style!raw' },
      {
        test: /plottable\/plottable\.js/,
        loader: 'imports?d3=d3/d3.js,_=plottable/plottable.css,require=>false'
      }
  	]
  },

  resolve: {
    modulesDirectories: ['node_modules', 'bower_components'],
    extensions: ['', '.js', '.imba']
  }
}
