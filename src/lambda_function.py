from src.webdriver_wrapper import WebDriverWrapper
from src.w3_utils import W3Utils

def lambda_handler(event, context, test_to_run = "template.w3swm", *args):

    ## check if there's a brand new test defined
    if event.get("test_to_run"):
        test_to_run = event["test_to_run"]   

    ## starting some checkings
    utils = W3Utils()
    utils.check_os_env()

    ## starting driver
    driver = WebDriverWrapper()

    ## defining and validating the test to run
    test_to_run_set = utils.set_test_to_run(test_to_run, driver._tmp_folder)  

    ## starting the test
    driver.test_runner(test_to_run_set)