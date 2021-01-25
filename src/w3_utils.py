import os
import ptvsd
import logging
import boto3
import botocore
import sys
import time
import json
import threading

from threading import Timer
from enum import Enum 
from src.errors import CustomErrors, HaltException
from selenium.webdriver.support import expected_conditions as ExpectedConditions
from selenium.webdriver.common.by import By


class W3Utils:

    def __init__(self):
        self._logger = logging.getLogger()

        # definig file path
        self._test_local_path = None


    def set_avoid(self, caller_driver, caller_wait, avoid):
        avoid_element = caller_driver.find_elements_by_css_selector(str(avoid))
        check_avoid_length = len(avoid_element)
        if check_avoid_length > 0:
            caller_wait.until(ExpectedConditions.invisibility_of_element_located((By.CSS_SELECTOR, str(avoid))))

    def check_os_env(self):
        mandatory_os_env = ["PYTHONPATH", "PATH", "BUCKET", "TIME_WAIT", "TIME_SLEEP", "LOG_LEVEL", "DEBUG"]
        for os_env in mandatory_os_env:
            if os_env not in os.environ:
                self._logger.error("It's mandatory to define [{}] environment variable".format(os_env))
                return
        
        self._logger.info("### ENVIRONMENT VARIABLES")
        self._logger.info(os.environ)
    

    def set_screenshot(self, caller_driver, test_to_run):
        # Setting the screenshot path
        self._screenshot_file_path = '{}.png'.format(test_to_run)      
        
        # Waiting some time to screenshot
        time.sleep(int(os.environ["TIME_SLEEP"]))

        # Taking screenshot
        caller_driver.save_screenshot(self._screenshot_file_path)      
    

    def set_json_output(self, json_result_data, test_to_run):
        # setting some path variables
        self._result_file_path = "{}.json".format(test_to_run)
        
        # Appending data to json object
        screenshot_file_name = "{}/{}.png".format(self._screenshot_file_path.split("/")[4],self._screenshot_file_path.split("/")[3])

        # Setting screenshot filename
        json_result_data[0].update({
            "screenshot": screenshot_file_name
        })
        
        # Setting json temp file and structure
        with open(self._result_file_path, "w") as json_file:
            json.dump(json_result_data, json_file)


    def upload_to_aws(self):
        try:
            # I'm not a RegEx big fan, but this parse sucks...
            screenshot_file_name = "{}/{}/UTC0-{}.png".format((self._screenshot_file_path.split("/")[4]).split(".png")[0],(self._screenshot_file_path.split("/")[3])[:10],(self._screenshot_file_path.split("/")[3]).split("_")[1])
            result_file_name = screenshot_file_name.replace(".png",".json")
            last_result_filename = "{}_last-run".format(self._screenshot_file_path.split("/")[4].replace(".png",".json"))
            
            # Uploading to AWS
            s3 = boto3.client("s3")
            s3.upload_file(self._screenshot_file_path, os.environ["BUCKET"], "screenshots/{}".format(screenshot_file_name))
            s3.upload_file(self._result_file_path, os.environ["BUCKET"], "results/{}".format(result_file_name))
            s3.upload_file(self._result_file_path, os.environ["BUCKET"], "results/{}".format(last_result_filename))
            self._logger.info("Screenshot <{}.png> and result <{}.json> uploaded successfully to <{}> bucket".format(screenshot_file_name, result_file_name, os.environ["BUCKET"]))
        except Exception as ex:
            # Something else has gone wrong.
            self._logger.error("General exception: {}".format(str(ex)))
            raise HaltException("Finishing the code")


    def check_debug(self):
        if os.environ["DEBUG"] == "TRUE":
            ptvsd.enable_attach(address=('0.0.0.0', int(os.environ["DEBUG_PORT"])), redirect_output=True)
            print(" *** Debugger waiting to be attached on port {} ***".format(int(os.environ["DEBUG_PORT"])))
            ptvsd.wait_for_attach()
            print(" *** Debugger attached bro! ***")


    def check_test_availability(self, test_to_run):
        if (test_to_run is None or test_to_run == ""):
            self._logger.error("It's mandatory to set the test to run.")
            return 


    def download_test_from_cloud(self, test_to_run):
        try:
            # Defining local filename       
            s3 = boto3.client("s3")
            file_content = s3.get_object(Bucket=os.environ["BUCKET"], Key='{}/{}'.format("tests", test_to_run))
            result = file_content["Body"].read()
            with open(self._test_local_path, "wb") as file:
                file.write(result)
            return self._test_local_path
        except botocore.exceptions.ClientError as ex:
            if (ex.response["Error"]["Code"] == "404" or ex.response["Error"]["Code"] == 'NoSuchKey'):
                self._logger.error("The test you've informed [{}] doesn't exists on [{}] folder under [{}] bucket!".format(test_to_run, 'tests', os.environ["BUCKET"]))
                return 
            else:
                # Something else has gone wrong.
                self._logger.error("General exception: {}".format(str(ex)))
                return 
        except Exception as ex:
            # Something else has gone wrong.
            self._logger.error("General exception: {}".format(str(ex)))
            raise HaltException("Finishing the code")


    def set_test_to_run(self, test_to_run, tmp_folder):
        try:
            # Check if test is available to run
            self.check_test_availability(test_to_run)

            # Defining local filename
            local_filename = "{}/{}".format(tmp_folder, test_to_run)
            self._test_local_path = local_filename

            return self.download_test_from_cloud(test_to_run)
        
        except Exception as ex:
            # Something else has gone wrong.
            self._logger.error("General exception: {}".format(str(ex)))
            raise HaltException("Finishing the code")