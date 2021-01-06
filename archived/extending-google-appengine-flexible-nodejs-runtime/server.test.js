'use strict';

const assert = require('assert');
const proxyquire = require('proxyquire').noPreserveCache();
const sinon = require('sinon');
const supertest = require('supertest');

const result = 'You won!';

const app = proxyquire('./server', {
  child_process: {
    exec: sinon.stub().yields(null, result)
  }
});

it('should play the fortunes game', (done) => {
  supertest(app)
    .get('/')
    .end((err, response) => {
      assert.ifError(err);
      assert.equal(response.text, result);
      done();
    });
});
