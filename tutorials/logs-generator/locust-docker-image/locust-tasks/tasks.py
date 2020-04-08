#!/usr/bin/env python

from locust import TaskSet, task
from locust.wait_time import between
from locust.contrib.fasthttp import FastHttpLocust
import logging 


class PublishRecordTaskSet(TaskSet):
    def setup(self):
        logging.debug('Starting PublishRecordTaskSet')

    @task(1)
    def get_publish(self):
        self.client.get('/publish')


class PublishRecord(FastHttpLocust):
    def __init__(self):
        FastHttpLocust.__init__(self)

    task_set = PublishRecordTaskSet
    wait_time = between(1, 2)
