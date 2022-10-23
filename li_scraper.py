import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class LIScraper:
    def __init__(self, path_to_li_creds):
        self.path_to_li_creds = path_to_li_creds
        self.driver = None

    def log_in_to_li_sales_nav(self):
        file = open(self.path_to_li_creds)
        lines = file.readlines()
        email = lines[0]
        password = lines[1]

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.driver.get("https://www.linkedin.com/sales?trk=d_flagship3_nav&")

        self.driver.find_element(By.CSS_SELECTOR, "#username").send_keys(email)
        self.driver.find_element(By.CSS_SELECTOR, "#password").send_keys(password)
        self.driver.find_element(
            By.CSS_SELECTOR, "div.login__form_action_container > button.btn__primary--large"
        ).click()
        print("Login Successful.")

    def scroll_to_bottom(self):
        inner_window = self.driver.find_element(By.XPATH, "/html/body/main/div/div[2]/div[2]")
        scroll = 0
        while scroll < 8:
            self.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].offsetHeight;",
                inner_window,
            )
            scroll += 1
            time.sleep(1)

    def gather_data(self, num_results):
        titles = []
        time_in_roles = []
        for i in range(1, num_results + 1):
            title = self.driver.find_element(
                By.XPATH,
                f"/html/body/main/div/div[2]/div[2]/div/ol/li[{i}]/div/div/div[2]/div[1]/div[1]/div/div[2]/div[2]/span[1]",
            ).text
            titles.append(title)

            time_in_role = self.driver.find_element(
                By.XPATH,
                f"/html/body/main/div/div[2]/div[2]/div/ol/li[{i}]/div/div/div[2]/div[1]/div[1]/div/div[2]/div[4]",
            ).text
            time_in_roles.append(time_in_role)

        return pd.DataFrame({"title": titles, "time_in_role": time_in_roles})

    def paginate(self):
        self.driver.find_element(
            By.XPATH, "/html/body/main/div/div[2]/div[2]/div/div[3]/div/button[2]"
        ).click()

    def get_number_of_results(self):
        response = self.driver.find_element(
            By.XPATH, "/html/body/main/div/div[2]/div[1]/div[2]/div[1]/div[4]/span"
        ).text.split(" ")[0]
        if response[-1] == "+":
            return 1000  # upper cap on how many we'll collect
        else:
            return int(response)

    def go_home(self):
        self.driver.find_element(By.XPATH, "/html/body/header/div/ul/li[1]/a/div").click()

    def search_for_correct_company(self, company_name, crm_only):
        if crm_only:
            self.driver.get(
                "https://www.linkedin.com/sales/search/company?query=(filters%3AList((type%3AACCOUNTS_IN_CRM%2Cvalues%3AList((id%3AACRM%2Ctext%3AAccounts%2520in%2520CRM%2CselectionType%3AINCLUDED)))))&viewAllFilters=true"
            )
        else:
            self.driver.get("https://www.linkedin.com/sales/search/company?viewAllFilters=true")
        time.sleep(4)

        # search through CRM
        self.driver.find_element(By.ID, "global-typeahead-search-input").send_keys(company_name + "\n")

        time.sleep(5)

        # capture returned company name
        try:
            return self.driver.find_element(
                By.XPATH,
                "/html/body/main/div/div[2]/div[2]/div/ol/li/div/div/div[2]/div[1]/div[1]/div/div[2]/div[1]/div/a",
            ).text
        except:
            return None

    def search_employees(self, num_in_list=1):
        self.driver.find_elements(By.XPATH, "//a[text()='All employees']")[num_in_list - 1].click()
        time.sleep(4)

    def search_for_employees(self, keyword):
        try:
            try:
                try:
                    self.driver.find_element(
                        By.XPATH,
                        '//button[normalize-space()="Expand Current job title filter"]',
                    ).click()
                except:
                    self.driver.find_element(
                        By.XPATH,
                        "/html/body/main/div/div[1]/div[2]/form/div/div[2]/fieldset[3]/div/fieldset[1]/div/button",
                    ).click()
            except:
                self.driver.find_element(
                    By.XPATH,
                    "/html/body/main/div/div[1]/div[2]/form/div/div[2]/fieldset[3]/div/fieldset[1]/div",
                ).click()
        except:
            self.driver.find_element(
                By.XPATH,
                "/html/body/main/div/div[1]/div[2]/form/div/div[2]/fieldset[3]/div/fieldset[1]/div/button/li-icon",
            ).click()

        time.sleep(1)
        # send keyword
        self.driver.find_element(
            By.XPATH,
            "//input[@placeholder='Add current titles']",
        ).send_keys(keyword)

        time.sleep(0.25)
        self.driver.find_element(
            By.XPATH,
            "//input[@placeholder='Add current titles']",
        ).send_keys("\n")

    def count_number_of_people_on_page(self):
        return (
            self.driver.find_element(By.XPATH, "/html/body/main/div/div[2]/div[2]")
                .get_attribute("innerHTML")
                .count("circle-entity")
        )

    def gather_all_data_for_company(self, company_name, crm_only=True, title_keyword='data'):
        returned_company_name = self.search_for_correct_company(company_name, crm_only)

        if not returned_company_name:
            return pd.DataFrame(
                {
                    "title": [None],
                    "time_in_role": [None],
                    "company_name": [None],
                    "original_company_name": [company_name],
                }
            )

        self.search_employees()
        self.search_for_employees(keyword=title_keyword)
        time.sleep(2.5)
        self.scroll_to_bottom()

        num_results = self.get_number_of_results()
        print(f"{num_results} results found")
        number_records_collected = 0

        p = 1
        print(f"Collecting page {p}")
        time.sleep(1)
        num_to_search = self.count_number_of_people_on_page()
        df = self.gather_data(num_to_search)
        number_records_collected += num_to_search

        while (num_results - number_records_collected) > 0:
            try:
                self.paginate()
                p += 1
                print(f"Collecting page {p}")
                time.sleep(2)

                self.scroll_to_bottom()
                num_to_search = self.count_number_of_people_on_page()
                new_df = self.gather_data(num_to_search)
                df = pd.concat([df, new_df])
                number_records_collected += num_to_search
            except:
                break

        df["company"] = [returned_company_name] * len(df)
        df["original_company"] = [company_name] * len(df)
        return df
