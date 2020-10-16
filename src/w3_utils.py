import os
import logging
import boto3
import botocore
import sys
from enum import Enum 
from src.errors import Errors
import time

class W3Utils:

    def __init__(self):
        self._logger = logging.getLogger()
        

    def check_os_env(self):
        mandatory_os_env = ["PYTHONPATH", "PATH", "BUCKET", "TIME_WAIT", "TIME_SLEEP"]
        for os_env in mandatory_os_env:
            if os_env not in os.environ:
                self._logger.error("It's mandatory to define [{}] environment variable".format(os_env))
                sys.exit(Errors.OS_ENV_NOT_DEFINED)
        
        self._logger.info("### ENVIRONMENT VARIABLES")
        self._logger.info(os.environ)
    
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