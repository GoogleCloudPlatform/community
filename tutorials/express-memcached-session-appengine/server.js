'use strict';

const express = require('express');
const session = require('express-session');
const cookieParser = require('cookie-parser');
const MemcachedStore = require('connect-memjs')(session);
const publicIp = require('public-ip');
const crypto = require('crypto');

// Environment variables are defined in app.yaml.
let MEMCACHE_URL = process.env.MEMCACHE_URL || '127.0.0.1:11211';

if (process.env.USE_GAE_MEMCACHE) {
  MEMCACHE_URL = `${process.env.GAE_MEMCACHE_HOST}:${process.env.GAE_MEMCACHE_PORT}`;
}

const app = express();
app.enable('trust proxy');

app.use(cookieParser());
app.use(session({
  secret: 'your-secret-here',
  key: 'view:count',
  proxy: 'true',
  store: new MemcachedStore({
    servers: [MEMCACHE_URL]
  })
}));

app.get('/', (req, res, next) => {
  // Discover requester's public IP address
  publicIp.v4().then((ip) => {
    const userIp = crypto.createHash('sha256').update(ip).digest('hex').substr(0, 7);

    // This shows the hashed IP for each
    res.write(`<div>${userIp}</div>`);

    if (req.session.views) {
      req.session.views += 1;
    } else {
      req.session.views = 1;
    }
    res.end(`Viewed <strong>${req.session.views}</strong> times.`);
  }).catch(next);
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log('App listening on port %s', PORT);
  console.log('Press Ctrl+C to quit.');
});

module.exports = app;
