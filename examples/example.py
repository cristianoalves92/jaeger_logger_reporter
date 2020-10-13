import time
import logging
import sys
from jaeger_logger_reporter import LoggerTraceConfig, LoggerTracerReporter


if __name__ == "__main__":

    config = LoggerTraceConfig(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'local_agent': {
                'reporting_host': 'localhost',
                'reporting_port': '5775',
            },
            'logging': True,
            'max_tag_value_length': sys.maxsize
        },
        service_name='test',
        validate=True,
    )

    # setup my logger (optional)
    tracer_logger = logging.getLogger('my.logger')
    tracer_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(levelname)s][%(date)s] %(name)s %(span)s %(event)s %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    tracer_logger.addHandler(handler)

    # define the logger to use, by default LoggerTracerReporter but can be changed.
    tracer = config.initialize_tracer(
        logger_reporter=LoggerTracerReporter(logger=tracer_logger))

    with tracer.start_span('TestSpan') as span:
        span.log_kv({'event': 'test message', 'life': 42})

        with tracer.start_span('ChildSpan', child_of=span) as child_span:
            child_span.log_kv({'event': 'down below'})

    # yield to IOLoop to flush the spans - https://github.com/jaegertracing/jaeger-client-python/issues/50
    time.sleep(2)
    tracer.close()  # flush any buffered spans
