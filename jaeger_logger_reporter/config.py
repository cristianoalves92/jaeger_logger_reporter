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
from jaeger_client import Config
from jaeger_client.reporter import (
    Reporter,
    CompositeReporter,
    NullReporter
)

from jaeger_client.sampler import RemoteControlledSampler
from jaeger_client.throttler import RemoteThrottler
from jaeger_logger_reporter.reporter import LoggerTracerReporter


default_logger = logging.getLogger('jaeger_tracing')


class LoggerTraceConfig(Config):

    def initialize_tracer(self, io_loop=None, logger_reporter=LoggerTracerReporter):
        """
        Initialize Jaeger Tracer based on the passed `jaeger_client.Config`.
        Save it to `opentracing.tracer` global variable.
        Only the first call to this method has any effect.
        """

        with Config._initialized_lock:
            if Config._initialized:
                default_logger.warn(
                    'Jaeger tracer already initialized, skipping')
                return
            Config._initialized = True

        tracer = self.new_tracer(logger_reporter, io_loop)

        self._initialize_global_tracer(tracer=tracer)
        return tracer

    def new_tracer(self, logger_reporter, io_loop=None):
        """
        Create a new Jaeger Tracer based on the passed `jaeger_client.Config`.
        """
        channel = self._create_local_agent_channel(io_loop=io_loop)
        sampler = self.sampler
        if not sampler:
            sampler = RemoteControlledSampler(
                channel=channel,
                service_name=self.service_name,
                logger=default_logger,
                metrics_factory=self._metrics_factory,
                error_reporter=self.error_reporter,
                sampling_refresh_interval=self.sampling_refresh_interval,
                max_operations=self.max_operations)
        default_logger.info('Using sampler %s', sampler)

        reporter = Reporter(
            channel=channel,
            queue_capacity=self.reporter_queue_size,
            batch_size=self.reporter_batch_size,
            flush_interval=self.reporter_flush_interval,
            logger=default_logger,
            metrics_factory=self._metrics_factory,
            error_reporter=self.error_reporter)

        if self.logging:
            reporter = CompositeReporter(
                reporter, logger_reporter)

        if not self.throttler_group() is None:
            throttler = RemoteThrottler(
                channel,
                self.service_name,
                refresh_interval=self.throttler_refresh_interval,
                logger=default_logger,
                metrics_factory=self._metrics_factory,
                error_reporter=self.error_reporter)
        else:
            throttler = None

        return self.create_tracer(
            reporter=reporter,
            sampler=sampler,
            throttler=throttler,
        )
