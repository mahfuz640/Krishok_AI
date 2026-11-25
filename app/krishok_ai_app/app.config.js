const app = require('./app.json');

module.exports = ({ config }) => ({
  ...app.expo,
  ...config,
  extra: {
    ...app.expo.extra,
    onlineApiBaseUrl: process.env.EXPO_PUBLIC_API_URL || '',
  },
});
