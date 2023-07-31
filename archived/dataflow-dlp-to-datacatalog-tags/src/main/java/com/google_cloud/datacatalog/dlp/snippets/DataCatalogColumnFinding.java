/*
 * Copyright 2020 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.google_cloud.datacatalog.dlp.snippets;

import com.google.privacy.dlp.v2.Likelihood;
import java.util.Objects;
import org.apache.beam.sdk.coders.AvroCoder;
import org.apache.beam.sdk.coders.DefaultCoder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@DefaultCoder(AvroCoder.class)
public class DataCatalogColumnFinding {

  public DataCatalogColumnFinding() {
    this.countVeryUnlikely = 0;
    this.countUnlikely = 0;
    this.countPossible = 0;
    this.countLikely = 0;
    this.countVeryLikely = 0;
    this.countUndefined = 0;
    this.highestLikelihoodFound = Likelihood.LIKELIHOOD_UNSPECIFIED;
  }

  public static final Logger LOG = LoggerFactory.getLogger(DataCatalogColumnFinding.class);

  private Integer countVeryUnlikely;
  private Integer countUnlikely;
  private Integer countPossible;
  private Integer countLikely;
  private Integer countVeryLikely;
  private Integer countUndefined;

  /**
   * LIKELIHOOD_UNSPECIFIED(0), VERY_UNLIKELY(1), UNLIKELY(2), POSSIBLE(3), LIKELY(4),
   * VERY_LIKELY(5), UNRECOGNIZED(-1);
   */
  private Likelihood highestLikelihoodFound;

  public Integer getCountVeryUnlikely() {
    return countVeryUnlikely;
  }

  public void setCountVeryUnlikely(Integer countVeryUnlikely) {
    this.countVeryUnlikely = countVeryUnlikely;
  }

  public Integer getCountUnlikely() {
    return countUnlikely;
  }

  public void setCountUnlikely(Integer countUnlikely) {
    this.countUnlikely = countUnlikely;
  }

  public Integer getCountPossible() {
    return countPossible;
  }

  public void setCountPossible(Integer countPossible) {
    this.countPossible = countPossible;
  }

  public Integer getCountLikely() {
    return countLikely;
  }

  public void setCountLikely(Integer countLikely) {
    this.countLikely = countLikely;
  }

  public Integer getCountVeryLikely() {
    return countVeryLikely;
  }

  public void setCountVeryLikely(Integer countVeryLikely) {
    this.countVeryLikely = countVeryLikely;
  }

  public Integer getCountUndefined() {
    return countUndefined;
  }

  public void setCountUndefined(Integer countUndefined) {
    this.countUndefined = countUndefined;
  }

  public Likelihood getHighestLikelihoodFound() {
    return highestLikelihoodFound;
  }

  public void setHighestLikelihoodFound(Likelihood highestLikelihoodFound) {
    this.highestLikelihoodFound = highestLikelihoodFound;
  }

  public void merge(DataCatalogColumnFinding dataCatalogColumnFinding) {
    this.countVeryUnlikely =
        this.countVeryUnlikely + dataCatalogColumnFinding.getCountVeryUnlikely();
    this.countUnlikely = this.countUnlikely + dataCatalogColumnFinding.getCountUnlikely();
    this.countPossible = this.countPossible + dataCatalogColumnFinding.getCountPossible();
    this.countLikely = this.countLikely + dataCatalogColumnFinding.getCountLikely();
    this.countVeryLikely = this.countVeryLikely + dataCatalogColumnFinding.getCountVeryLikely();
    this.countUndefined = this.countUndefined + dataCatalogColumnFinding.getCountUndefined();
    incrementHighestLikelihoodFound(dataCatalogColumnFinding.getHighestLikelihoodFound());
  }

  public void incrementLikelihoodFound(Likelihood likelihood) {
    if (Likelihood.VERY_LIKELY.equals(likelihood)) {
      this.countVeryLikely++;
    } else if (Likelihood.LIKELY.equals(likelihood)) {
      this.countLikely++;
    } else if (Likelihood.POSSIBLE.equals(likelihood)) {
      this.countPossible++;
    } else if (Likelihood.UNLIKELY.equals(likelihood)) {
      this.countUnlikely++;
    } else if (Likelihood.VERY_UNLIKELY.equals(likelihood)) {
      this.countVeryUnlikely++;
    } else {
      LOG.info(
          "[Thread: {} - DataCatalogColumnFinding] undefined likelihood: {}",
          Thread.currentThread().getName(),
          likelihood);
      this.countUndefined++;
    }
  }

  public void incrementHighestLikelihoodFound(Likelihood likelihood) {
    int storedLikelihoodNumber = this.highestLikelihoodFound.getNumber();
    int newLikelihoodNumber = likelihood.getNumber();

    if (storedLikelihoodNumber < newLikelihoodNumber) {
      this.highestLikelihoodFound = likelihood;
    }
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    DataCatalogColumnFinding that = (DataCatalogColumnFinding) o;
    return Objects.equals(countVeryUnlikely, that.countVeryUnlikely)
        && Objects.equals(countUnlikely, that.countUnlikely)
        && Objects.equals(countPossible, that.countPossible)
        && Objects.equals(countLikely, that.countLikely)
        && Objects.equals(countVeryLikely, that.countVeryLikely)
        && Objects.equals(countUndefined, that.countUndefined)
        && highestLikelihoodFound == that.highestLikelihoodFound;
  }

  @Override
  public int hashCode() {
    return Objects.hash(
        countVeryUnlikely,
        countUnlikely,
        countPossible,
        countLikely,
        countVeryLikely,
        countUndefined,
        highestLikelihoodFound);
  }

  @Override
  public String toString() {
    return "DataCatalogColumnFinding{"
        + "countVeryUnlikely="
        + countVeryUnlikely
        + ", countUnlikely="
        + countUnlikely
        + ", countPossible="
        + countPossible
        + ", countLikely="
        + countLikely
        + ", countVeryLikely="
        + countVeryLikely
        + ", countUndefined="
        + countUndefined
        + ", highestLikelihoodFound="
        + highestLikelihoodFound
        + '}';
  }
}
