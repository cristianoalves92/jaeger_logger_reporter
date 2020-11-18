# Copyright (c) 2020 IOTIC
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

import logging
from datetime import datetime

from jaeger_client.reporter import (
    Reporter,
    CompositeReporter,
    NullReporter
)
from opentracing.ext import tags


default_logger = logging.getLogger('tracer.logger')

default_logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '[%(levelname)s][%(date)s] %(name)s %(span)s %(event)s %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
default_logger.handlers = []
default_logger.addHandler(handler)


LOG_SPAN_START = 'STARTED'
LOG_SPAN_END = 'FINISHED'
LOG_SPAN_TAG = 'TAG'
LOG_SPAN_LOG = 'LOG'

LOG_HTTP_METHOD = 'http.method'
LOG_HTTP_URL = 'http.url'
LOG_HTTP_STATUS_CODE = 'http.status_code'
LOG_SPAN_ERROR = tags.ERROR
LOG_SPAN_HTML_DATA = 'http.data'
LOG_SPAN_HTML_RESPONSE = 'html.response'
LOG_SPAN_SERIALIZER_RESPONSE = 'serializer.response'

FILTER_TAGS = ['sampler.type', 'sampler.param', 'component',
               'span.kind', LOG_HTTP_METHOD, LOG_HTTP_STATUS_CODE, LOG_HTTP_URL, LOG_SPAN_ERROR]


def span_identifier(span):
    return f'[{span.operation_name}]'


class LoggerTracerReporter(NullReporter):
    """Logs all spans."""

    def __init__(self, logger=None, level=logging.INFO, span_identifier=span_identifier):
        self.logger = logger if logger else default_logger
        self.level = level
        self.spans = {}
        self.span_identifier = span_identifier

    def report_span(self, span):
        if span.parent_id:
            if span.parent_id not in self.spans:
                self.spans[span.parent_id] = []
            self.spans[span.parent_id].append(span)
        else:
            self.log_span(span)

    def log_span(self, span, parent=''):
        tags_values = LoggerTracerReporter._filter_tags_values(span)
        error = tags_values[LOG_SPAN_ERROR] if LOG_SPAN_ERROR in tags_values else False
        log_level = logging.ERROR if error else self.level

        self._log_start(span, parent, tags_values, log_level)
        self._log_child(span, parent)
        self._log_tags(span, parent, log_level)
        self._log_logs(span, parent, log_level)
        self._log_end(span, parent, tags_values, log_level)

    def _log_child(self, span, parent):
        parent = f'{parent}[{span.operation_name}]'
        if span.span_id in self.spans:
            for child_span in self.spans[span.span_id]:
                self.log_span(child_span, parent=parent)
            del self.spans[span.span_id]

    @staticmethod
    def _span_date(date):
        return datetime.fromtimestamp(date).isoformat()

    def _log_tags(self, span, parent, log_level):
        if isinstance(span.tags, list):
            for tag in span.tags:
                if tag.key not in FILTER_TAGS:
                    value = LoggerTracerReporter._tag_value(tag)
                    tag_string = f'{tag.key} {value}'
                    self._log_event(span, parent, LOG_SPAN_TAG, message=tag_string,
                                    level=logging.DEBUG if log_level != logging.ERROR else log_level)

    def _log_logs(self, span, parent, log_level):
        if isinstance(span.logs, list):
            for log in span.logs:
                value = None
                for tag in log.fields:
                    value = LoggerTracerReporter._tag_value(
                        tag) if value is None else f'{value} {LoggerTracerReporter._tag_value(tag)}'
                self._log_event(span, parent, LOG_SPAN_LOG, timestamp=log.timestamp, message=value,
                                level=logging.DEBUG if log_level != logging.ERROR else log_level)

    @staticmethod
    def _filter_tags_values(span):
        tags_values = {}
        for tag in span.tags:
            if tag.key in FILTER_TAGS:
                tags_values[tag.key] = LoggerTracerReporter._tag_value(tag)

        return tags_values

    def _log_start(self, span, parent, tags_values, log_level):
        methods = tags_values[LOG_HTTP_METHOD] if LOG_HTTP_METHOD in tags_values else ''
        url = tags_values[LOG_HTTP_URL] if LOG_HTTP_URL in tags_values else ''
        message = f'{methods} {url}'
        self._log_event(span, parent, LOG_SPAN_START,
                        message=message, level=log_level)

    def _log_end(self, span, parent, tags_values, log_level):
        status_code = tags_values[LOG_HTTP_STATUS_CODE] if LOG_HTTP_STATUS_CODE in tags_values else ''
        duration = span.end_time - span.start_time
        message = f'{status_code} {duration}s'

        self._log_event(span, parent, LOG_SPAN_END,
                        timestamp=span.end_time, message=message, level=log_level)

    # pylint: disable=too-many-arguments
    def _log_event(self, span, parent, event, level=None, timestamp=None, message=''):
        level = self.level if level is None else level
        if timestamp is None:
            date = LoggerTracerReporter._span_date(span.start_time)
        else:
            try:
                date = LoggerTracerReporter._span_date(timestamp)
            except ValueError:
                # for some reason the timestamp comes from log it's not a float
                timestamp = timestamp / 1000000
                date = LoggerTracerReporter._span_date(timestamp)
        span_identifier = f'{parent}{self.span_identifier(span)}'
        self.logger.log(level, '%s', message, extra={
                        'date': date, 'span': span_identifier, 'event': event})

    @staticmethod
    def _tag_value(tag):
        value = tag.vStr
        if value is None:
            value = tag.vDouble
        if value is None:
            value = tag.vBool
        if value is None:
            value = tag.vLong
        if value is None:
            value = tag.vBinary
        return value
