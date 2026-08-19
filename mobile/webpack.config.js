const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const appDirectory = path.resolve(__dirname);

const babelLoaderConfiguration = {
  test: /\.(js|jsx|ts|tsx)$/,
  include: [
    path.resolve(appDirectory, 'index.web.js'),
    path.resolve(appDirectory, 'src'),
    path.resolve(appDirectory, 'node_modules/@react-navigation'),
    path.resolve(appDirectory, 'node_modules/react-native-screens'),
    path.resolve(appDirectory, 'node_modules/react-native-safe-area-context'),
  ],
  use: {
    loader: 'babel-loader',
    options: {
      cacheDirectory: true,
      presets: [
        ['@babel/preset-env', { loose: true, modules: false }],
        ['@babel/preset-react', { runtime: 'automatic' }],
      ],
      plugins: [
        'react-native-web',
        ['@babel/plugin-transform-class-properties', { loose: true }],
        ['@babel/plugin-transform-private-methods', { loose: true }],
        ['@babel/plugin-transform-private-property-in-object', { loose: true }],
        [
          'module-resolver',
          {
            root: ['./src'],
            alias: {
              '@api': './src/api',
              '@screens': './src/screens',
              '@components': './src/components',
              '@navigation': './src/navigation',
              '@services': './src/services',
              '@store': './src/store',
              '@utils': './src/utils',
              '@theme': './src/theme',
              '@hooks': './src/hooks',
            },
          },
        ],
      ],
    },
  },
};

const cssLoaderConfiguration = {
  test: /\.css$/,
  use: ['style-loader', 'css-loader'],
};

module.exports = {
  entry: [path.resolve(appDirectory, 'index.web.js')],
  output: {
    path: path.resolve(appDirectory, 'dist'),
    filename: 'bundle.[contenthash].js',
    publicPath: '/',
    clean: true,
  },
  resolve: {
    extensions: ['.web.js', '.web.jsx', '.js', '.jsx', '.json', '.ts', '.tsx'],
    alias: {
      'react-native$': 'react-native-web',
      'react-native/Libraries/Utilities/Platform': 'react-native-web/dist/exports/Platform',
      'react-native-maps': path.resolve(appDirectory, 'src/components/WebMap.js'),
      '@react-native-async-storage/async-storage': path.resolve(
        appDirectory,
        'src/utils/AsyncStorageWeb.js'
      ),
      'react-native-permissions': path.resolve(
        appDirectory,
        'src/utils/PermissionsWeb.js'
      ),
      'react-native-vector-icons': path.resolve(
        appDirectory,
        'src/utils/VectorIconsWeb.js'
      ),
      'react-native-geolocation-service': path.resolve(
        appDirectory,
        'src/services/location.js'
      ),
      '@api': path.resolve(appDirectory, 'src/api'),
      '@screens': path.resolve(appDirectory, 'src/screens'),
      '@components': path.resolve(appDirectory, 'src/components'),
      '@navigation': path.resolve(appDirectory, 'src/navigation'),
      '@services': path.resolve(appDirectory, 'src/services'),
      '@store': path.resolve(appDirectory, 'src/store'),
      '@utils': path.resolve(appDirectory, 'src/utils'),
      '@theme': path.resolve(appDirectory, 'src/theme'),
      '@hooks': path.resolve(appDirectory, 'src/hooks'),
    },
  },
  module: {
    rules: [babelLoaderConfiguration, cssLoaderConfiguration],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: path.resolve(appDirectory, 'public/index.html'),
    }),
    new webpack.DefinePlugin({
      __DEV__: JSON.stringify(true),
      'process.env.NODE_ENV': JSON.stringify('development'),
    }),
  ],
  devServer: {
    port: 3000,
    open: false,
    hot: true,
    historyApiFallback: true,
    client: {
      overlay: false,
    },
  },
};
