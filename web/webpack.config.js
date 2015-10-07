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
    modulesDirectories: ['node_modules', 'bower_components'],
    extensions: ['', '.js', '.imba']
  },

  plugins: [
    new webpack.ResolverPlugin([
      new webpack.ResolverPlugin.DirectoryDescriptionFilePlugin("bower.json", ["main"])
    ], ['normal'])
  ]
}
