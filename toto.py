from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import keys
import asyncio
import mysql.connector

DB_CONFIG = keys.JASONDB_CONFIG

def webscrapeSite(AllData):
    # Set up options for headless mode
    firefox_options = Options()
    firefox_options.add_argument("--headless")

    # Path to GeckoDriver
    gecko_driver_path = "/usr/local/bin/geckodriver"

    # Set up the WebDriver
    service = Service(gecko_driver_path)
    driver = webdriver.Firefox(service=service, options=firefox_options)

    draws = {}

    url = f"https://en.lottolyzer.com/history/singapore/toto"
    driver.get(url)

    rows = driver.find_elements(By.XPATH, "//tr")


    if AllData == True:
        print("Inserting draws...")
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            if len(columns) >= 4:
                draw_number = columns[0].text.strip()
                draw_date = columns[1].text.strip()
                winning_numbers = columns[2].text.strip()
                additional_number = columns[3].text.strip()

                if draw_number == "Draw":
                    continue

                draws[draw_number] = [draw_number,draw_date,winning_numbers,additional_number]

                # results.append([draw_number, draw_date, winning_numbers, additional_number])
    else:
        print("Updating draws...")
        latestDrawNumber = getLatestToToDrawNumber()
        print(f"Latest Draw Number in Database: {latestDrawNumber}")

        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            if len(columns) >= 4:
                draw_number = columns[0].text.strip()
                draw_date = columns[1].text.strip()
                winning_numbers = columns[2].text.strip()
                additional_number = columns[3].text.strip()

                if draw_number == "Draw":
                    continue

                if draw_number > latestDrawNumber:
                    print(f"Draw No: {draw_number}")

                    draws[draw_number] = [draw_number,draw_date,winning_numbers,additional_number]

    driver.quit()
    return draws

def insertTotoNumbers(AllData):
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()
    count = 0

    results = webscrapeSite(AllData)

    if results == {}:
        print("No Updates...")
        return

    for result in results:
        if result == "Draw":
            print("Skipping Headers")
            continue

        print(str(result) + " " + str(type(result)))

        query = """
            INSERT INTO toto (drawNo, drawDate, winNo, bonusNo)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
        results[result][0],  # Access the first element of the tuple
        results[result][1],  # Access the second element of the tuple
        results[result][2],  # Access the third element of the tuple
        results[result][3]   # Access the fourth element of the tuple
        ))      
        count += 1

    db.commit()
    cursor.close()
    db.close()

    print(f"Total of {count} entires")

def getLatestToToDrawNumber():
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()

    query = f"""
        SELECT * FROM toto
        WHERE drawNo = (
            SELECT MAX(drawNo) FROM toto
        );
    """

    cursor.execute(query)
    
    response = cursor.fetchall()

    latestDrawNumber = response[0][1]

    return latestDrawNumber

def getLatestDrawDetails():
    insertTotoNumbers(False) #Updates the database first.

    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()

    query = f"""
        SELECT * FROM toto
        WHERE drawNo = (
            SELECT MAX(drawNo) FROM toto
        );
    """

    cursor.execute(query)
    
    response = cursor.fetchall()

    
    DrawNumber = response[0][1]
    DrawDate = response[0][2]
    winning_numbers = response[0][3].split(',')
    bonus_number = response[0][4]

    latestDrawDetails = {
        "drawNo" : DrawNumber,
        "drawDate" : DrawDate,
        "winNo" : winning_numbers,
        "bonusNo" : bonus_number
    }
    print("")
    print("#" * 50)
    print(f"Draw No: {DrawNumber}")
    print(f"Draw Date: {DrawDate}")
    print(f"Winning Numbers: {winning_numbers}")
    print(f"Bonus Number: {bonus_number}")
    print("#" * 50)
    print("")

    return latestDrawDetails

def calcuateNumberFrequency():
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()

    query = f"""
        SELECT winNo, bonusNo FROM toto;
    """

    cursor.execute(query)
    
    responses = cursor.fetchall()
    numberCount = {}

    for response in responses:
        winNo = response[0]
        bonusNo = response[1]

        winNo = winNo.split(',')

        winNo.append(bonusNo)

        for number in winNo:
            if number not in numberCount:
                numberCount[number] = 1
            else:
                numberCount[number] += 1
        
    return numberCount



def getLucky(printing=False):
    numberFrequency = calcuateNumberFrequency()
    latestDrawNumber = getLatestToToDrawNumber()

    sortNumbers = sorted(numberFrequency, key=numberFrequency.get)

    lowFreqNumbers = sortNumbers[:7]
    highFreqNumbers = sortNumbers[-7:]
    secondFreqNumbers = sortNumbers[-14:-7]

    if printing == False:
        return [highFreqNumbers, secondFreqNumbers, lowFreqNumbers]

    print(f"As of Draw No.: {latestDrawNumber}")

    print(f"Lowest Number Frequencies: {lowFreqNumbers}")
    print(f"Highest Number Frequencies: {highFreqNumbers}")
    print(f"Second Highest Number Frequencies: {secondFreqNumbers}")
    print("In order of Lowest to Highest Frequencies")
    print(sortNumbers)
    
    return [highFreqNumbers, secondFreqNumbers, lowFreqNumbers]

# insertTotoNumbers(False)

def validateWin(tickets=[]):

    drawDetails = getLatestDrawDetails()

    draw_winningNumbers = drawDetails['winNo']
    draw_bonusNumbers = drawDetails['bonusNo']
    
    if tickets == []:

        print("Validating Generated Numbers...")
        defaultNumbers = getLucky()
    
        for num in range(0,len(defaultNumbers)):
            results = checkTicket(defaultNumbers[num], draw_winningNumbers, draw_bonusNumbers)
            if num == 0:
                print(f"Results of the Highest Frequency: {results} | {defaultNumbers[num]}")
            elif num == 1:
                print(f"Results of the Second Highest Frequency: {results} | {defaultNumbers[num]}")
            elif num == 2:
                print(f"Results of the Lowested Frequency: {results} | {defaultNumbers[num]}")
            else:
                print("Something happened")
                print(results)
                print(defaultNumbers[num])
    else:
        for ticket in tickets:
            print("Validing Ticket...")

            results = checkTicket(ticket, draw_winningNumbers, draw_bonusNumbers)
            print(f"Result of Ticket: {results} | {ticket}")

def checkTicket(ticketnumbers, winningnumbers, bonusnumber):
    
    count = 0.0

    for number in ticketnumbers:
        if number in winningnumbers:
            count += 1
        if number == bonusnumber:
            count += 0.5

    return count

validateWin()
# validateWin([['3', '10', '13', '29', '32', '46'],['3', '10', '13', '29', '32', '46'],['3', '10', '13', '29', '32', '46'],['3', '10', '13', '29', '32', '46'],['3', '10', '13', '29', '32', '46'],['3', '10', '13', '29', '32', '46'],['3', '10', '13', '29', '32', '46']])
# validateWin([['3', '10', '13', '29', '32', '46','18']])
# checkTicket(['3', '10', '13', '29', '32', '46'], ['3', '10', '13', '29', '32', '46'], 18)

