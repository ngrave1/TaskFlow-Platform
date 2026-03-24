import logging
import sys

import structlog


def setup_logging(environment: str = "development", debug: bool = False) -> None:
    log_level = logging.DEBUG if debug else logging.INFO

    shared_processors = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.contextvars.merge_contextvars,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    class HealthCheckFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if not debug:
                path = getattr(record, 'path', '')
                if path and '/health' in str(path):
                    return False
                
                message = getattr(record, 'message', '')
                if message and 'health' in str(message).lower():
                    return False
            return True
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.addFilter(HealthCheckFilter())
    
    if environment == "production":
        pre_chain = shared_processors + [
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
        ]
        
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=pre_chain,
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(console_handler)
    uvicorn_logger.setLevel(log_level)
    uvicorn_logger.propagate = False
    
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers.clear()
    uvicorn_access_logger.addHandler(console_handler)
    uvicorn_access_logger.setLevel(log_level)
    uvicorn_access_logger.addFilter(HealthCheckFilter())
    uvicorn_access_logger.propagate = False
    
    structlog_processors = shared_processors + [
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]
    
    structlog.configure(
        processors=structlog_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logger = structlog.get_logger("common.logger")
    logger.info(
        "logging.configured",
        environment=environment,
        debug=debug,
        log_level=logging.getLevelName(log_level),
    )