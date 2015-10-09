var webpack = require('webpack');

module.exports = {
  entry: './src/main',

  output: {
  	filename: 'static/assets/main.js'
  },

  module: {
  	loaders: [
  	  { test: /\.imba$/, loader: 'imba-loader' },
      { test: /\.css$/, loader: 'style!raw' },
      {
        test: /plottable\/plottable\.js/,
        loader: 'imports?SVGTypewriter=svg-typewriter/svgtypewriter,d3=d3/d3.js,_=plottable/plottable.css,require=>false'
      },
      {
        test: /svgtypewriter\.js/,
        loader: 'exports?SVGTypewriter'
      }
  	]
  },

  resolve: {
    modulesDirectories: ['node_modules', 'bower_components'],
    extensions: ['', '.js', '.imba']
  }
}
