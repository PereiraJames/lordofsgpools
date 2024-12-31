from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import keys
import mysql.connector

DB_CONFIG = keys.JASONDB_CONFIG

def webscrapeSite():
    # Set up options for headless mode
    firefox_options = Options()
    firefox_options.add_argument("--headless")

    # Path to GeckoDriver
    gecko_driver_path = "/usr/local/bin/geckodriver"

    # Set up the WebDriver
    service = Service(gecko_driver_path)
    driver = webdriver.Firefox(service=service, options=firefox_options)

    # Open the website
    
    # url = "https://en.lottolyzer.com/history/singapore/toto"

    drawNo = {}


    for i in range(1,34):
        print(i)

        url = f"https://en.lottolyzer.com/history/singapore/toto/page/{i}/per-page/50/summary-view"
        driver.get(url)

        # Wait for the page to load (if needed, implement WebDriverWait for dynamic content)

        # Find all elements with the class `sum-p1`
        rows = driver.find_elements(By.XPATH, "//tr")


        # results = []
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            if len(columns) >= 4:  # Ensure the row has enough columns
                draw_number = columns[0].text.strip()  # First column: draw number
                draw_date = columns[1].text.strip()    # Second column: date
                winning_numbers = columns[2].text.strip()  # Third column: numbers
                additional_number = columns[3].text.strip()  # Fourth column: additional number

                drawNo[draw_number] = [draw_number,draw_date,winning_numbers,additional_number]

                # results.append([draw_number, draw_date, winning_numbers, additional_number])

        driver.quit()

    print(drawNo)
    print(len(drawNo))

    return drawNo

# def findLastDrawNumber():
    
#     lastNumber =
    
#     return lastNumber

def insertTotoNumbers():
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()
    count = 0

    results = webscrapeSite()

    for result in results:
        if result == ('Draw', 'Date', 'Winning No.', 'Addl No.'):
            print("Skipping Headers")
            continue

        print(str(result) + " " + str(type(result)))

        query = """
            INSERT INTO toto (drawNo, drawDate, winNo, bonusNo)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
        result[0],  # Access the first element of the tuple
        result[1],  # Access the second element of the tuple
        result[2],  # Access the third element of the tuple
        result[3]   # Access the fourth element of the tuple
        ))      
        count += 1

    db.commit()
    cursor.close()
    db.close()

    print(f"Total of {count} entires")


webscrapeSite()