/**
 * Copyright 2017, Google, Inc.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const utils = require('./utils');
const {
  FILENAME_REGEXP,
  DIR_REGEXP,
  TUTORIAL_YAML_REGEXP,
  TITLE_REGEXP,
  DESCRIPTION_REGEXP,
  GITHUB_REGEXP,
  TAGS_REGEXP,
  DATE_REGEXP,
  TUTORIALS_PATH
} = utils;

const files = fs.readdirSync(TUTORIALS_PATH)
  .filter((name) => !name.startsWith('.'));

describe('tutorials/', () => {
  files.forEach((entry, i) => {
    describe(entry, () => {
      let content, filename;
      const dir = path.join(TUTORIALS_PATH, '/', entry);
      const stats = fs.statSync(dir);

      if (stats.isDirectory()) {
        filename = path.join(dir, 'index.md');
      } else if (stats.isFile()) {
        filename = dir;
      } else {
        throw new Error(`Unrecognized file: ${entry}`);
      }

      before((done) => {
        fs.readFile(filename, { encoding: 'utf8' }, (err, _content) => {
          if (err) {
            done(err);
            return;
          }
          content = _content;
          done();
        });
      });

      it.skip('tests pass, if any', (done) => {
        // TODO: Handle tests for other languages
        fs.stat(path.join(dir, 'package.json'), (err, stats) => {
          if (err) {
            // Ignore error
            done();
            return;
          }

          utils.runAsync('npm install', dir)
            .then(() => utils.runAsync('npm test', dir))
            .then((output) => {
              console.log(output);
              done();
            }).catch(done);
        });
      });

      it('filename', () => {
        if (stats.isDirectory()) {
          assert(DIR_REGEXP.test(entry), `filename should be of the form ${DIR_REGEXP}. Actual: ${entry}.`);
        } else {
          assert(FILENAME_REGEXP.test(entry), `filename should be of the form ${FILENAME_REGEXP}. Actual: ${entry}.`);
        }
      });

      it('frontmatter', () => {
        const matches = TUTORIAL_YAML_REGEXP.exec(content);
        assert(TUTORIAL_YAML_REGEXP.test(content), `frontmatter should be of the form ${TUTORIAL_YAML_REGEXP}. Actual: ${content}`);
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
        assert(DATE_REGEXP.test(datePublished), `datePublished should be of the form YYYY-MM-DD. Actual: ${datePublished}.`);
      });
    });
  });
});
