// Copyright 2015-2016, Google, Inc.
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const utils = require('./utils');
const {
  FILENAME_REGEXP,
  TUTORIAL_YAML_REGEXP,
  TITLE_REGEXP,
  DESCRIPTION_REGEXP,
  GITHUB_REGEXP,
  TAGS_REGEXP,
  DATE_REGEXP,
  TUTORIALS_PATH
} = utils;

const files = fs.readdirSync(TUTORIALS_PATH);

describe('tutorials/', function () {
  files.forEach(function (entry, i) {
    describe(entry, function () {
      before(function (done) {
        fs.readFile(path.join(TUTORIALS_PATH, '/', entry), { encoding: 'utf8' }, (err, content) => {
          if (err) {
            return done(err);
          }
          this.content = content;
          return done();
        });
      });
      it('filename', function () {
        assert(FILENAME_REGEXP.test(entry), `filename should be of the form ${FILENAME_REGEXP}. Actual: ${entry}.`);
      });
      it('frontmatter', function () {
        const matches = TUTORIAL_YAML_REGEXP.exec(this.content);
        assert(TUTORIAL_YAML_REGEXP.test(this.content), `frontmatter should be of the form ${TUTORIAL_YAML_REGEXP}. Actual: ${matches[0]}`);
        const [
          ,
          title,
          description,
          author,
          tags,
          datePublished
        ] = matches;

        assert(TITLE_REGEXP.test(title), `title should be of the form ${TITLE_REGEXP}. Actual: ${title}.`);
        assert(DESCRIPTION_REGEXP.test(description), `description should be of the form ${DESCRIPTION_REGEXP}. Actual: ${description}.`);
        assert(GITHUB_REGEXP.test(author), `author should be of the form ${GITHUB_REGEXP}. Actual: ${author}.`);
        assert(TAGS_REGEXP.test(tags), `tags should be of the form ${TAGS_REGEXP}. Actual: ${tags}.`);
        assert(DATE_REGEXP.test(datePublished), `datePublished should be of the form ${DATE_REGEXP}. Actual: ${datePublished}.`);
      });
    });
  });
});
