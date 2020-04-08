#!/usr/bin/env python

from datetime import datetime
from locust import HttpLocust, TaskSet, task, between 
from locust import seq_task, TaskSequence, web, events
from locust.wait_time import between
from locust.contrib.fasthttp import FastHttpLocust
from random import randint
import logging
import os

class PublishRecordTaskSet(TaskSequence):
    def setup(self):
        logging.debug('Starting PublishRecordTaskSet')

    @seq_task(1)
    def get_publish(self):
        self.client.get('/publish')


class PublishRecord(FastHttpLocust):
    def __init__(self):
        FastHttpLocust.__init__(self)

    task_set = PublishRecordTaskSet
    wait_time = between(1, 2)
