import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
demo_logger = logging.getLogger('demo')
demo_handler = logging.FileHandler('./logs/demo.log')
demo_handler.setLevel(logging.INFO)
demo_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'))
demo_logger.addHandler(demo_handler)
demo_logger.info('This is a demo message')

test_logger = logging.getLogger('test')
test_logger.setLevel(logging.DEBUG)  # Ensure the logger level is set
test_handler = logging.FileHandler('./logs/test.log')
test_handler.setLevel(logging.DEBUG)
test_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'))
test_logger.addHandler(test_handler)
test_logger.debug('This is a test message')

demo_logger.info('This is another demo message')
test_logger.debug('This is another test message')
