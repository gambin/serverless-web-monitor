import boto3
import os
import shutil
import uuid
import time
import json
import logging
import sys
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as ExpectedConditions
from src.w3_utils import W3Utils
from src.actions import TestActions

class WebDriverWrapper:

    def __init__(self, download_location=None):
        
        self._tmp_folder = "/tmp/{}".format(uuid.uuid4())
        self.download_location = download_location

        self._logger = logging.getLogger()
        self._logger.setLevel(logging.INFO)

        chrome_options = webdriver.ChromeOptions()

        if not os.path.exists(self._tmp_folder):
            os.makedirs(self._tmp_folder)

        if not os.path.exists(self._tmp_folder + "/user-data"):
            os.makedirs(self._tmp_folder + "/user-data")

        if not os.path.exists(self._tmp_folder + "/data-path"):
            os.makedirs(self._tmp_folder + "/data-path")

        if not os.path.exists(self._tmp_folder + "/cache-dir"):
            os.makedirs(self._tmp_folder + "/cache-dir")

        if self.download_location:
            prefs = {"download.default_directory": download_location,
                     "download.prompt_for_download": False,
                     "download.directory_upgrade": True,
                     "safebrowsing.enabled": False,
                     "safebrowsing.disable_download_protection": True,
                     "profile.default_content_setting_values.automatic_downloads": 1}

            chrome_options.add_experimental_option("prefs", prefs)

        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage") 
        chrome_options.add_argument("--window-size=1280x1000")
        chrome_options.add_argument("--user-data-dir={}".format(self._tmp_folder + "/user-data"))
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        chrome_options.add_argument("--v=99")
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument("--data-path={}".format(self._tmp_folder + "/data-path"))
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--homedir={}".format(self._tmp_folder))
        chrome_options.add_argument("--disk-cache-dir={}".format(self._tmp_folder + "/cache-dir"))

        chrome_options.binary_location = os.getcwd() + "/bin/headless-chromium"
        chrome_log_path=self._tmp_folder + "/chromedriver.log"

        self._driver = webdriver.Chrome(chrome_options=chrome_options, service_args=["--error", "--log-path={}".format(chrome_log_path)])
        self._driver.implicitly_wait = os.environ["TIME_WAIT"]

        self._wait = WebDriverWait(self._driver, int(os.environ["TIME_WAIT"]))

        self._utils = W3Utils()

        if self.download_location:
            self.enable_download_in_headless_chrome()


    def close(self):
        # Close webdriver connection
        self._driver.quit()

        # Remove specific tmp dir of this "run"
        shutil.rmtree(self._tmp_folder)

        # Remove possible core dumps
        folder = "/tmp"
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if "core.headless-chromi" in file_path and os.path.exists(file_path) and os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)


    def enable_download_in_headless_chrome(self):
        """
        This function was pulled from
        https://github.com/shawnbutton/PythonHeadlessChrome/blob/master/driver_builder.py#L44

        There is currently a "feature" in chrome where
        headless does not allow file download: https://bugs.chromium.org/p/chromium/issues/detail?id=696481

        Specifically this comment ( https://bugs.chromium.org/p/chromium/issues/detail?id=696481#c157 )
        saved the day by highlighting that download wasn't working because it was opening up in another tab.

        This method is a hacky work-around until the official chromedriver support for this.
        Requires chrome version 62.0.3196.0 or above.
        """
        self._driver.execute_script(
            "var x = document.getElementsByTagName('a'); var i; for (i = 0; i < x.length; i++) { x[i].target = '_self'; }")
        # add missing support for chrome "send_command"  to selenium webdriver
        self._driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

        params = {"cmd": "Page.setDownloadBehavior", "params": {"behavior": "allow", "downloadPath": self.download_location}}
        command_result = self._driver.execute("send_command", params)
        print("response from browser:")
        for key in command_result:
            print("result:" + key + ":" + str(command_result[key]))


    def set_text_input(self, selector, value_setter, to_avoid=None, ts=0):
        try:
            # check if need to avoid some selector, like a modal or loading element overlaping on z-index
            if to_avoid is not None:
                self._utils.set_avoid(self._driver, self._wait, to_avoid)

            # check if there's a pre-defined timesleep
            if int(ts) > 0:
                time.sleep(int(ts))

            # getting the element
            element = self._wait.until(ExpectedConditions.visibility_of_element_located((By.CSS_SELECTOR, selector)))
            
            # element.clear() would be awesome, but not working properly on some sites..
            element.send_keys(Keys.CONTROL + "a")

            # to be implemented, happy to working with python, not with Go-Lang LOL
            if to_avoid is not None:
                self._utils.set_avoid(self._driver, self._wait, to_avoid)

            # settings the values to selector
            element.send_keys(value_setter)

            # i don't want to waste my time to care about client side actions like on blur, on change, so...
            self.key_press("TAB")
            self.key_press("SHIFT+TAB", to_avoid)

        except:
            raise

    
    def button_click(self, selector, to_avoid=None):
        try:
            # check if need to avoid some selector, like a modal or loading element overlaping on z-index
            if to_avoid is not None:
                self._utils.set_avoid(self._driver, self._wait, to_avoid)

            # is there a way to assure that the element is ready to interact with? this way..
            self._wait.until(ExpectedConditions.visibility_of_element_located((By.CSS_SELECTOR, selector)))
            element = self._wait.until(ExpectedConditions.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            
            # and go!
            element.click()
        except: 
            raise


    def set_drop_down(self, selector, value_setter, to_avoid=None):
        try:
            # check if need to avoid some selector, like a modal or loading element overlaping on z-index
            if to_avoid is not None:
                self._utils.set_avoid(self._driver, self._wait, to_avoid)

            # is there a way to assure that the element is ready to interact with? this way..
            element = Select(self._wait.until(ExpectedConditions.visibility_of_element_located((By.CSS_SELECTOR, selector))))
            element.select_by_visible_text(value_setter)
        except: 
            raise


    def key_press(self, value_setter, to_avoid=None):
        try:
            # check if need to avoid some selector, like a modal or loading element overlaping on z-index
            if to_avoid is not None:
                self._utils.set_avoid(self._driver, self._wait, to_avoid)
            element = self._driver.switch_to.active_element


            # i'm not proud of this..
            if value_setter == 'RETURN' or value_setter == 'ENTER':
                element.send_keys(Keys.RETURN)
            elif value_setter == 'TAB':
                element.send_keys(Keys.TAB)
            elif value_setter == 'SHIFT+TAB':
                element.send_keys(Keys.SHIFT, Keys.TAB)
        except: 
            raise


    def test_runner(self, test_to_run):       
        json_result_data = []
        ex = None

        try:
            # reading previously downloaded test
            self._logger.info("Loading local downloaded test: <{}.w3swm>".format(test_to_run))
            instructions = list(open(test_to_run, "r"))
            to_avoid = None
            to_skip = None

            # reading all instructions
            for line in instructions:

                # defining each statement items
                statement = line.split('"')

                # going through all items
                for statement_item in statement:

                    # checking the verb
                    if(statement.index(statement_item) == 0):

                        # if it's a call to action
                        if (len(statement) == 3):
                            verb = statement[0].strip()
                            user_value = statement[1].strip()

                            self._logger.info("Action: <{}>. Value: <{}>.".format(verb, user_value))

                            if(verb in TestActions.TOWAIT):
                                time.sleep(int(user_value))
                            
                            if(verb in TestActions.TOAVOID):
                                to_avoid = user_value

                            if(verb in TestActions.TOACCESS):
                                self._driver.get(user_value)

                            if(verb in TestActions.TOCLICK):
                                self.button_click(user_value, to_avoid)

                            if(verb in TestActions.TOIGNORE):
                                to_skip = user_value

                            if(verb in TestActions.TOPRESS):
                                self.key_press(user_value)


                        # if has selector and value
                        if (len(statement) == 5):
                            verb = statement[0].strip()
                            css_selector = statement[1].strip()
                            user_value = statement[3].strip()

                            self._logger.info("Action: <{}>. Selector: <{}>. Value: <{}>.".format(verb, css_selector, user_value))

                            if (verb in TestActions.TOFILL):
                                if (line.strip().endswith("com delay")):
                                    self.set_text_input(css_selector, user_value, to_avoid, ts=os.environ["TIME_SLEEP"])
                                else :    
                                    self.set_text_input(css_selector, user_value, to_avoid)

                            if(verb in TestActions.TOSELECT):
                                self.set_drop_down(css_selector, user_value, to_avoid)
                               
                                
            # defining success output
            json_result_data.append({
                "status": 200,
                "description": "Test <{}> finished successfully".format(test_to_run)
            })

            # logging info
            if os.environ["LOG_LEVEL"] == "INFO":
                # setting local screenshot
                self._utils.set_screenshot(self._driver, test_to_run)

                # setting local JSON
                self._utils.set_json_output(json_result_data, test_to_run)

            # job done!
            self._logger.info("Well done!")

        except Exception as e:
            # defining exception output
            line_error_test = "line {}:  {}".format(int(instructions.index(line)) + 1, line)

            json_result_data.append({
                "status": 422,
                "error_line": line_error_test,
                "exception": getattr(e, 'message', repr(e)),
                "traceback": traceback.format_exc()
            })

            self._logger.error("# An exception has ocurred!")
            self._logger.error(line_error_test)

            if os.environ["LOG_LEVEL"] == "INFO":
                # throw full exception
                self._logger.error("Exception: " + str(e))
                
                # getting the chrome output logs
                with open(self._tmp_folder + "/chromedriver.log", "r") as logfile:
                    log_data = logfile.readlines()
                    self._logger.info("### Chrome error logs")
                    self._logger.info(log_data)

                    # defining screenshot filename
                    json_result_data[0].update({
                        "htmlOutput": self._driver.find_element_by_tag_name("html").get_attribute("innerHTML"),
                        "chrome_driver_logs": log_data
                    })
                    
                    
            # logging error
            if os.environ["LOG_LEVEL"] in ["INFO", "ERROR"]:
                # setting local screenshot
                self._utils.set_screenshot(self._driver, test_to_run)

                # setting local JSON
                self._utils.set_json_output(json_result_data, test_to_run)

            # setting error exception to raise on lambda execution
            ex = e

        finally:
    
            ## done task
            self._driver.close()

            # if error, raise exception on lambda execution
            if (ex):
                raise ex