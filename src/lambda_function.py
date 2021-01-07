from src.webdriver_wrapper import WebDriverWrapper
from src.w3_utils import W3Utils

def lambda_handler(event, context, test_to_run = "template.w3swm", *args):

    ## starting some base checkings
    utils = W3Utils()

    # debug will starts here
    utils.check_debug()
    utils.check_os_env()

    ## check if there's a brand new test defined
    ## or must used the predefined template
    if event.get("test_to_run"):
        test_to_run = event["test_to_run"]   

    ## starting driver
    driver = WebDriverWrapper()

    ## defining and validating the test to run
    test_to_run_set = utils.set_test_to_run(test_to_run, driver._tmp_folder)  

    ## starting the test
    driver.test_runner(test_to_run_set)