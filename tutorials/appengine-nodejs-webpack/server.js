'use strict';

const express = require('express');
const path = require('path');

const app = express();

// Setup view engine
app.set('view engine', 'pug');

app.use(express.static(path.resolve(path.join(__dirname, '/dist'))));

app.get('/', (req, res) => {
  res.render('index');
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`App listening on port ${PORT}`);
  console.log('Press Ctrl+C to quit.');
});
