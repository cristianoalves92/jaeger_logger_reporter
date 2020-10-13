# Jaeger Logger Reporter

This packages enables a way to log your span in a simple way. It provides a `LoggerReporter` with some configurations. But enables a way to create custom logger reporters.

It extends the [jaeger-client](https://github.com/jaegertracing/jaeger-client-python) packages, change the configuration in a way it's possible use customer logger reporters.

## Installation

Running the following command:

```
$ pip install jaeger-logger-reporter
```

## Usage

It's very similar to the [jaeger-client](https://github.com/jaegertracing/jaeger-client-python), the only difference will be the configuration.

```python
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

```

It will produce a logger output similar to:

```
2020-10-13T22:37:02.538850
[INFO][2020-10-13T22:37:02.538850] my.logger [TestSpan] STARTED
INFO:my.logger:
2020-10-13T22:37:02.538918
[INFO][2020-10-13T22:37:02.538918] my.logger [TestSpan][ChildSpan] STARTED
INFO:my.logger:
2020-10-13T22:37:02.538924
[DEBUG][2020-10-13T22:37:02.538924] my.logger [TestSpan][ChildSpan] LOG down below
DEBUG:my.logger:down below
2020-10-13T22:37:02.538940
[INFO][2020-10-13T22:37:02.538940] my.logger [TestSpan][ChildSpan] FINISHED  2.2172927856445312e-05s
INFO:my.logger: 2.2172927856445312e-05s
2020-10-13T22:37:02.538887
[DEBUG][2020-10-13T22:37:02.538887] my.logger [TestSpan] LOG test message 42
DEBUG:my.logger:test message 42
2020-10-13T22:37:02.538985
[INFO][2020-10-13T22:37:02.538985] my.logger [TestSpan] FINISHED  0.00013494491577148438s
INFO:my.logger: 0.00013494491577148438s
```

# LoggerTracerReporter

`LoggerTracerReporter` have some configurations.

## Span identifier

By default the span it's identifier by `operation_name` eg:

```
[get_user]
```

But can be changed:

```python
def span_identifier(span):
    return f'**{span}**'

...
tracer = config.initialize_tracer(
    logger=LoggerTracerReporter(span_identifier=span_identifier))

```

And the output will be something like:

```
**79408c731416c394:55150307c2aa6ca8:0:1 test.TestSpan**
```

_Note_: if the span has a parent the parent identifier will be display before the span identifier:

```
[parent_id][span_id]
```

## Logger formatter

The logger follows this formatter:

```python
'%(levelname)s][%(date)s] %(name)s %(span)s %(event)s %(message)s'
```

Where:

- `levelname` is the log level of message;
- `date` is the time of event;
- `name` is the logger name;
- `span` is the span identifier;
- `event` is the span event
- `message` is the message of the log

The logger can be overrider on `LoggerTracerReporter`instaciation.

## Span life cycle

### Defined tags

There are some Tags keys defined. Can be used to improve the log quality:

- `LOG_HTTP_METHOD`
- `LOG_HTTP_URL`
- `LOG_HTTP_STATUS_CODE`
- `LOG_SPAN_ERROR`
- `LOG_SPAN_HTML_DATA`
- `LOG_SPAN_HTML_RESPONSE`
- `LOG_SPAN_SERIALIZER_RESPONSE`

### Events

There's some different events types:

#### STARTED

Identify the start of the event. It will show:

- `date` of the begin of the span
- `LOG_HTTP_METHOD` and `LOG_HTTP_URL` if exist, as a `message`

#### TAG

Represent a value of a span tag `(log_level = DEBUG)`

#### LOG

Represent a value of a `log_kv `(log_level = DEBUG)`

#### FINISHED

Identify the end of the event. It will show:

- `date` of the end of the span
- `LOG_HTTP_STATUS_CODE` if exist, and the duration fo the span as a `message`
