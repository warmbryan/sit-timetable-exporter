from getpass import getpass

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC

from selenium.webdriver import ChromeOptions

from datetime import datetime
from icalendar import Calendar, Event

class SIT_TIMETABLE_EXPORTER:
    __timetable = []
    
    def __init__(self, accUser, accPass, headless = True) -> None:
        self.__accUser = accUser
        self.__accPass = accPass

        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        self.__driver = webdriver.Chrome(options=options)

        self.__driver.get("https://in4sit.singaporetech.edu.sg/")

        self.__waitQuick = WebDriverWait(self.__driver, 30, 1)
        self.__waitLong = WebDriverWait(self.__driver, 60, 2)

    
    def export(self, filename: str):
        cal = Calendar()

        # {
        #     "moduleTitle": moduleLabel.text,
        #     "classNo": classNo,
        #     "classSection": classSection,
        #     "classComponent": classComponent,
        #     "classDayTime": classDayTime,
        #     "classStartDateTime": datetime.strptime(f"{classDate[0]}-{classDayTime[0]}", "%d/%m/%Y-%H:%M"),
        #     "classEndDateTime": datetime.strptime(f"{classDate[1]}-{classDayTime[1]}", "%d/%m/%Y-%H:%M"),
        #     "classRoom": classRoom,
        #     "classInstructors": classInstructors,
        #     "classDate": datetime.strptime(classDate[0], "%d/%m/%Y")
        # }

        for moduleClass in self.__timetable:
            event = Event()
            event.add("summary", f'{moduleClass["moduleTitle"]} - {moduleClass["classComponent"]}')
            event.add("dtstart", moduleClass["classStartDateTime"])
            event.add("dtend", moduleClass["classEndDateTime"])
            event.add("location", moduleClass["classRoom"])
            classSection = moduleClass["classSection"]
            classNumber = moduleClass["classNo"]
            instructors = moduleClass["classInstructors"]
            event.add("description", f"Section: {classSection}\nClass Number: {classNumber}\nInstructors: {instructors}")

            cal.add_component(event)

        filenameCleaned = filename.strip(".").replace(" ", "_")

        with open(f"{filenameCleaned}.ics", "wb") as f:
            f.write(cal.to_ical())

        print("exported.")
    
    def get_timetable(self):
        self.__waitQuick.until(EC.presence_of_element_located((By.ID, "userNameInput")))

        emailTB = self.__driver.find_element(By.ID, "userNameInput")
        passTB = self.__driver.find_element(By.ID, "passwordInput")

        submitBtn = self.__driver.find_element(By.ID, "submitButton")

        emailTB.click()
        emailTB.send_keys(self.__accUser)

        passTB.click()
        passTB.send_keys(self.__accPass)

        submitBtn.click()

        self.__waitQuick.until(EC.visibility_of_element_located((By.ID, "HOMEPAGE_SELECTOR$PIMG")))

        # Course Management
        courseMgmtBtn = self.__driver.find_element(By.ID, "win0divPTNUI_LAND_REC_GROUPLET$1")
        courseMgmtBtn.click()

        # My Weekly Schedule
        mwsBtn = self.__waitLong.until(EC.element_to_be_clickable((By.ID, "win1div$ICField$11$$1")))
        mwsBtn.click()

        scheduleFrame = self.__waitQuick.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "main_target_win0")))

        print("waited, lets go, switched frame:", scheduleFrame)

        # Select Display Option: "List View" radio button
        lvRadioBtn = self.__driver.find_element(By.XPATH, '//*[@id="DERIVED_REGFRM1_SSR_SCHED_FORMAT$258$"]')
        lvRadioBtn.click()

        # modules show up
        self.__waitQuick.until(EC.visibility_of_element_located((By.ID, "win0divSSR_DUMMY_RECVW$0")))

        # find semester label
        semesterLabel = self.__waitLong.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#DERIVED_REGFRM1_SSR_STDNTKEY_DESCR\$11\$")))
        print(semesterLabel.text)

        # find all semester table
        modules = self.__driver.find_elements(By.XPATH, "/html/body/form/div[5]/table/tbody/tr/td/div/table/tbody/tr[10]/td[2]/div/table/tbody/tr/td/div/table")

        for module in modules:
            moduleLabel = module.find_element(By.XPATH, "tbody/tr[1]/td")
            print(moduleLabel.text)
            timetable = module.find_elements(By.XPATH, "tbody/tr/td/table/tbody/tr/td/div/table/tbody/tr/td/table")[-1]

            classNo = ""
            classSection = ""
            classComponent = ""

            moduleDays = timetable.find_elements(By.XPATH, "tbody/tr[position()>1]")

            print(f"{len(moduleDays)=}")

            for moduleDay in moduleDays:
                moduleDayInfo = moduleDay.find_elements(By.XPATH, "td/div/span")
                print(f"{len(moduleDayInfo)=}")
                if len(moduleDayInfo[0].text) > 2:
                    classNo = moduleDayInfo[0].text
                    classSection = moduleDayInfo[1].text
                    classComponent = moduleDayInfo[2].text

                indexOffset = -1 if len(moduleDayInfo) < 7 else 0

                classDayTime = moduleDayInfo[indexOffset + 3].text[3:].split(" - ")
                classRoom = moduleDayInfo[indexOffset + 4].text
                classInstructors = moduleDayInfo[indexOffset + 5].text.replace("\n", " ")
                classDate = moduleDayInfo[indexOffset + 6].text.split(" - ")

                # print(f"{classNo=} {classSection=} {classComponent=} {classDayTime=} {classRoom=} {classInstructors=} {classDate=}")
                if len(classDayTime) > 1:
                    self.__timetable.append({
                        "moduleTitle": moduleLabel.text,
                        "classNo": classNo,
                        "classSection": classSection,
                        "classComponent": classComponent,
                        "classDayTime": classDayTime,
                        "classStartDateTime": datetime.strptime(f"{classDate[0]}-{classDayTime[0]}", "%d/%m/%Y-%H:%M"),
                        "classEndDateTime": datetime.strptime(f"{classDate[1]}-{classDayTime[1]}", "%d/%m/%Y-%H:%M"),
                        "classRoom": classRoom,
                        "classInstructors": classInstructors,
                        "classDate": datetime.strptime(classDate[0], "%d/%m/%Y")
                    })

        print("finished scraping.")

    def cleanup(self):
        self.__driver.quit()


userEmail = input("SIT Account Address: ")
userPw = getpass("SIT Account Password: ")

exporter = SIT_TIMETABLE_EXPORTER(userEmail, userPw, headless=False)
exporter.get_timetable()
exporter.export("sem2-timetable")
exporter.cleanup()