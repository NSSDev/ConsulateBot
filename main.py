from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import telebot
from config import TOKEN, CHAT_ID, KEY, EMAIL, PASSWORD, LAST_NAME, FIRST_NAME, MIDDLE_NAME, DATE_OF_BIRTH, PHONE_NUMBER
from twocaptcha import TwoCaptcha
import schedule
import time
import pytz
from datetime import datetime


bot = telebot.TeleBot(token=TOKEN)


options = webdriver.ChromeOptions()
# options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1200')
d = DesiredCapabilities.CHROME
d['loggingPrefs'] = { 'browser':'ALL' }
driver = webdriver.Chrome(executable_path="chromedriver.exe", options=options, desired_capabilities=d)
# driver = webdriver.Chrome(executable_path="/home/consulate_bot/chromedriver", options=options, desired_capabilities=d)

moscow_tz = pytz.timezone("Europe/Moscow")


class Consulate:

    def auth(self):
        auth_counter = 0
        while driver.current_url != "https://q.midpass.ru/ru/Home/Index":
            if auth_counter == 10:
                bot.send_message(chat_id="", text=f"[Предупреждение] Неудачная попытка авторизации 10 раз, возможно сменен пароль.")
                print('отправил оповещение об ошибке')
            try:
                auth_counter += 1
                driver.get("https://q.midpass.ru/")
                time.sleep(3)
                if driver.current_url == "https://q.midpass.ru/ru/Account/BanPage":
                    bot.send_message(chat_id="",
                                     text="[Предупреждение] Изменен пароль. Проверьте почту пожалуйста.")
                    print('отправил оповещение об ошибке')
                driver.find_element(By.XPATH, "//select[contains(@data-bind,'options: countries,')]").click()
                driver.find_element(By.XPATH, "//*[@id='FormLogOn']/div/div[2]/div[2]/div[2]/select/option[12]").click()
                driver.find_element(By.XPATH, f"//*[@id='FormLogOn']/div/div[2]/div[3]/div[2]/select/option[2]").click()
                driver.find_element(By.XPATH, "//*[@id='Email']").send_keys(EMAIL)
                driver.find_element(By.XPATH, "//input[@id='Password']").send_keys(PASSWORD)
                time.sleep(5)
                with open('filename_captcha.png', 'wb') as file:
                    file.write(driver.find_element(By.XPATH,
                                                   "//img[@id='imgCaptcha']").screenshot_as_png)
                time.sleep(1)
                solver = TwoCaptcha(KEY)
                result = solver.normal('filename_captcha.png')
                driver.find_element(By.XPATH, "//input[@id='Captcha']").send_keys(result['code'])
                driver.find_element(By.XPATH, "//button[contains(text(),'Войти')]").click()
                time.sleep(10)
                print("Authed")
            except Exception:
                pass


    def check_places(self):
        print("Checking..")
        requests_counter = 0
        if driver.current_url == "https://q.midpass.ru/":
            self.auth()

        self.consulates = [
                    "https://q.midpass.ru/ru/Booking?serviceId=5ab34c36-c511-5973-15f6-a798d227de90",
                    "https://q.midpass.ru/ru/Booking?serviceId=3500cc92-c925-8fa1-9177-03acc92c2709",
                    "https://q.midpass.ru/ru/Booking?serviceId=d9fa268d-2323-90ed-73f5-60a1de7e9650",
                    "https://q.midpass.ru/ru/Booking?serviceId=1e0d3889-1fd3-048d-8467-b8fe313e0766",
                    "https://q.midpass.ru/ru/Booking?serviceId=a6df3a1f-0923-757d-b7d2-7b3aa9a1ddb2",
                    "https://q.midpass.ru/ru/Booking?serviceId=54030d6a-e145-08e2-60fb-33344fac2455"
                      ]

        for consulate in self.consulates:
            self.moscow_time = datetime.now(tz=moscow_tz).strftime("%m/%d/%Y, %H:%M:%S")
            try:
                requests_counter += 1
                driver.get(url=consulate)
                time.sleep(20)
                with open("logs.txt", "a") as f:
                    f.write(f"{self.moscow_time} | Method : GET | Request : OK\n")
                time.sleep(5)
                driver.execute_script("window.scrollTo(0, 1250)")
                self.city_name = ""
                if consulate == self.consulates[0]:
                    self.city_name = "Астана - Консульство"
                if consulate == self.consulates[1]:
                    self.city_name = "Уральск - Генеральное консульство"
                if consulate == self.consulates[2]:
                    self.city_name = "Уральск - Генеральное консульство"
                if consulate == self.consulates[3]:
                    self.city_name = "Усть-Каменогорск - Генеральное консульство"
                if consulate == self.consulates[4]:
                    self.city_name = "Армения - Консульство"
                self.service_name = driver.find_element(By.XPATH, "/html/body/div[2]/div/div[3]/div[6]").text
                self.cost_slots = driver.find_element(By.ID, "availableSlotsCount").text
                time.sleep(4)
                driver.find_element(By.XPATH, "//a[@class='link-next']").click()
                time.sleep(4)
                self.cost_slots_next_month = driver.find_element(By.ID, "availableSlotsCount").text
                time.sleep(4)
                if int(self.cost_slots) != 0:
                    driver.find_element(By.XPATH, "//a[@class='link-prev']").click()
                    time.sleep(2)

                    self.booking()
                if int(self.cost_slots_next_month) != 0:
                    driver.find_element(By.XPATH, "//a[@class='link-next']").click()
                    time.sleep(2)
                    self.booking()


            except Exception:
                pass


    def booking(self):
        print('Booking..')
        booked_persons = []
        client_counter = 0
        while client_counter != len(FIRST_NAME):
            if PHONE_NUMBER[client_counter] in booked_persons:
                continue
            time.sleep(2)
            for free_place in driver.find_element(By.ID, "CalendarBody").find_elements(By.TAG_NAME, "tr"):
                if free_place.find_element(By.TAG_NAME, "td").get_attribute("style"):
                    if "rgb(252, 76, 76)" in free_place.find_element(By.TAG_NAME, "td").get_attribute("style"):
                        continue
                    else:
                        date_free_place = free_place.find_element(By.TAG_NAME, "td").get_attribute("date")
                        free_place.find_element(By.TAG_NAME, "td").click()
                        time.sleep(3)
                        for free_time in driver.find_elements(By.ID, "selectable"):
                            driver.execute_script("window.scrollTo(0, 1250)")
                            if free_time.find_element(By.CLASS_NAME, "available"):
                                self.place_time = free_time.find_element(By.CLASS_NAME, "available").text
                                bot.send_message(chat_id=CHAT_ID,
                                                 text=f"╔═══════════════╗\nПоявилось место в городе:\n{self.city_name}\n\n{self.service_name}\n\nСвободных мест:\nТекущий месяц: {self.cost_slots}\nСледующий месяц: {self.cost_slots_next_month}\n\nЗабронировал на ближайшую дату: {date_free_place} в {self.place_time}\n╚═══════════════╝")
                                driver.execute_script("window.scrollTo(0, 1250)")
                                free_time.find_element(By.CLASS_NAME, "available").click()
                                time.sleep(3)
                                driver.execute_script("window.scrollTo(900, 0)")

                                driver.find_element(By.XPATH, "//button[@id='confirm']").click()
                                time.sleep(5)
                                driver.find_element(By.ID, "warningChecbox").click()
                                driver.execute_script("window.scrollTo(0, 900)")
                                driver.find_element(By.CLASS_NAME, "surname").send_keys(LAST_NAME[client_counter])
                                driver.find_element(By.CLASS_NAME, "_name").send_keys(FIRST_NAME[client_counter])
                                driver.find_element(By.CLASS_NAME, "patronymic").send_keys(MIDDLE_NAME[client_counter])
                                time.sleep(1)
                                driver.find_element(By.CLASS_NAME, "birth-date").send_keys(DATE_OF_BIRTH[client_counter])
                                time.sleep(1)
                                driver.find_element(By.CLASS_NAME, "phone-number").send_keys(PHONE_NUMBER[client_counter])
                                time.sleep(3)
                                driver.find_element(By.XPATH, "/html/body/div[2]/div/div[3]/div[8]/div[2]/button[1][1]").click()
                                time.sleep(3)
                                driver.find_element(By.XPATH, "//span[@class='l-btn-left']").click()
                                time.sleep(2)
                                booked_persons.append(PHONE_NUMBER[client_counter])
                                driver.execute_script("window.scrollTo(500, 0)")
                                time.sleep(1)
                                driver.find_element(By.XPATH, "/html/body/div[2]/div/div[3]/table/tbody/tr/td[2]/a").click()
                                time.sleep(2)
                                driver.execute_script("window.scrollTo(0, 1250)")
                                client_counter += 1
                                file = open('logs.txt', 'a')
                                file.write(f"{self.moscow_time} | Method : POST | Request : OK\n")
                                file.close()
                            else:
                                driver.find_element(By.XPATH,
                                                    "/html/body/div[2]/div/div[3]/table/tbody/tr/td[2]/a").click()
                                time.sleep(2)
                                driver.execute_script("window.scrollTo(0, 1250)")



    def main(self):
        self.auth()
        schedule.every(1).minutes.do(self.check_places)
        while True:
            schedule.run_pending()


if __name__ == "__main__":
    c = Consulate()
    c.main()
