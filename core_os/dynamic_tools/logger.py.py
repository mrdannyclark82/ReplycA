import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOG_DIR = "core_os/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
log_file = os.path.join(LOG_DIR, f"agent_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)

def log_command_execution(command, success=True, error_message=None):
    """Log command execution results."""
    logger = get_logger("command_executor")
    if success:
        logger.info(f"Command executed successfully: {command}")
    else:
        logger.error(f"Command failed: {command} - Error: {error_message}")

def log_tool_creation(tool_name, code):
    """Log tool creation events."""
    logger = get_logger("tool_creator")
    logger.info(f"Created new tool: {tool_name}")
    logger.debug(f"Tool code length: {len(code)} characters")

def log_memory_operation(operation, key, success=True):
    """Log memory operations."""
    logger = get_logger("memory_manager")
    if success:
        logger.info(f"Memory operation successful: {operation} - Key: {key}")
    else:
        logger.error(f"Memory operation failed: {operation} - Key: {key}")