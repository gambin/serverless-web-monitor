import os
import logging
import boto3
import botocore
import sys
import time
import json

from enum import Enum 
from src.errors import Errors
from selenium.webdriver.support import expected_conditions as ExpectedConditions
from selenium.webdriver.common.by import By

class W3Utils:

    def __init__(self):
        self._logger = logging.getLogger()

    def set_avoid(self, caller_driver, caller_wait, avoid):
        avoid_element = caller_driver.find_elements_by_css_selector(str(avoid))
        check_avoid_length = len(avoid_element)
        if check_avoid_length > 0:
            caller_wait.until(ExpectedConditions.invisibility_of_element_located((By.CSS_SELECTOR, str(avoid))))

    def check_os_env(self):
        mandatory_os_env = ["PYTHONPATH", "PATH", "BUCKET", "TIME_WAIT", "TIME_SLEEP", "LOG_LEVEL"]
        for os_env in mandatory_os_env:
            if os_env not in os.environ:
                self._logger.error("It's mandatory to define [{}] environment variable".format(os_env))
                sys.exit(Errors.OS_ENV_NOT_DEFINED)
        
        self._logger.info("### ENVIRONMENT VARIABLES")
        self._logger.info(os.environ)
    

    def set_screenshot(self, caller_driver, test_to_run):
        # setting the screenshot path
        screenshot_file_path = '{}.png'.format(test_to_run)      
        
        # waiting some time to screenshot
        time.sleep(int(os.environ["TIME_SLEEP"]))

        #taking screenshot
        caller_driver.save_screenshot(screenshot_file_path)
    
    def set_json_output(self, json_result_data, test_to_run):
        # setting some path variables
        screenshot_file_path = '{}.png'.format(test_to_run)      
        screenshot_file_name = "{}.png".format(test_to_run.split("/")[3])       
        result_file_path = "{}.json".format(test_to_run)
        result_file_name = "{}.json".format(test_to_run.split("/")[3])

        # defining screenshot filename
        json_result_data[0].update({
            "screenshot": screenshot_file_name
        })
        
        # setting json temp file and structure
        with open(result_file_path, "w") as json_file:
            json.dump(json_result_data, json_file)

        # uploading to AWS
        self.upload_to_aws(screenshot_file_path, screenshot_file_name, result_file_path, result_file_name)


    def upload_to_aws(self, screenshot_file_path, screenshot_file_name, result_file_path, result_file_name):
        # uploading to AWS
        s3 = boto3.client("s3")
        s3.upload_file(screenshot_file_path, os.environ["BUCKET"], "screenshots/{}".format(screenshot_file_name))
        s3.upload_file(result_file_path, os.environ["BUCKET"], "results/{}".format(result_file_name))
        s3.upload_file(result_file_path, os.environ["BUCKET"], "results/{}.w3swm-last.json".format(result_file_name.split(".w3swm")[0],))
        self._logger.info("Screenshot <{}.png> and result <{}.json> uploaded successfully to <{}> bucket".format(screenshot_file_name, result_file_name, os.environ["BUCKET"]))


    def set_test_to_run(self, test_to_run, tmp_folder):
        if (test_to_run is None or test_to_run == ""):
            self._logger.error("It's mandatory to set the test to run.")
            sys.exit(Errors.TEST_NOT_DEFINED)

        try:
            ts = time.gmtime()
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", ts)
            local_filename = "{}/{}.{}".format(tmp_folder, test_to_run, timestamp)
           
            s3 = boto3.client("s3")
            file_content = s3.get_object(Bucket=os.environ["BUCKET"], Key='{}/{}'.format("tests", test_to_run))
            result = file_content["Body"].read()
            
            self._logger.info("Downloading test locally: [AWS]{} >> [LOCAL]{}".format(test_to_run, local_filename))
            with open(local_filename, "wb") as file:
                file.write(result)
            return local_filename

        except botocore.exceptions.ClientError as ex:
            if (ex.response["Error"]["Code"] == "404" or ex.response["Error"]["Code"] == 'NoSuchKey'):
                self._logger.error("The test you've informed [{}] doesn't exists on [{}] folder under [{}] bucket!".format(test_to_run, 'tests', os.environ["BUCKET"]))
                sys.exit(Errors.TEST_NOT_FOUND)
            else:
                # Something else has gone wrong.
                self._logger.error("General exception: {}".format(str(ex)))
                sys.exit(Errors.GENERIC_EXCEPTION)

        except Exception as ex:
            # Something else has gone wrong.
            self._logger.error("General exception: {}".format(str(ex)))
            sys.exit(Errors.GENERIC_EXCEPTION)