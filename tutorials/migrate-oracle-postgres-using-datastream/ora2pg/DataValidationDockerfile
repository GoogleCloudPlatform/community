# Copyright 2020 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM python:3.8.0-slim

ARG ORACLE_ODBC_VERSION=12.2

RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get install wget -y \
&& apt-get clean

RUN wget https://storage.googleapis.com/professional-services-data-validator/releases/latest/google_pso_data_validator-latest-py3-none-any.whl

RUN pip install --upgrade pip
RUN pip install google_pso_data_validator-latest-py3-none-any.whl
RUN pip install cx_Oracle

# Install Oracle ODBC required packages
ENV ORACLE_SID oracle
ENV ORACLE_HOME /usr/lib/oracle/${ORACLE_ODBC_VERSION}/client64

RUN apt-get -y install --fix-missing --upgrade vim alien unixodbc-dev wget libaio1 libaio-dev

COPY oracle/*.rpm ./
RUN alien -i *.rpm && rm *.rpm \
    && echo "/usr/lib/oracle/${ORACLE_ODBC_VERSION}/client64/lib/" > /etc/ld.so.conf.d/oracle.conf \
    && ln -s /usr/include/oracle/${ORACLE_ODBC_VERSION}/client64 $ORACLE_HOME/include \
    && ldconfig -v

RUN mkdir /config
VOLUME /config
ENV PSO_DV_CONFIG_HOME=/config 
ENTRYPOINT ["python", "-m", "data_validation"]

