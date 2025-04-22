from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import flet as ft

import re

def get_latest_filing(ticker):
    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome()
    try:
        # Navigate to the SEC Edgar search page
        driver.get("https://www.sec.gov/search-filings")
        
        # Wait for the search box to load and enter the ticker
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "edgar-company-person"))
        )
        
        search_box.send_keys(ticker + "\n")  # "\n" simulates pressing Enter
        
        # Wait for the filings table to load
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "latest-filings"))
        )
        
        # Find all rows in the filings table
        rows = table.find_elements(By.TAG_NAME, "li")
        if len(rows) < 2:
            return "No filings found for the ticker."
        
        # Get the latest filing (second row, as first is the header)
        latest_filing = rows[0]
        # cells = latest_row.find_elements(By.TAG_NAME, "td")
        
        split = re.split(' - |[\n\r]', latest_filing.text)
        filling_link = latest_filing.find_element(By.TAG_NAME, "a").get_attribute('href')

        # Return the filing information as a dictionary
        return {
            "filing_type": split[1],
            "filing_date": split[0],
            "filing_link": filling_link
        }
    except Exception as e:
        return f"An error occurred: {str(e)}"
    finally:
        # Always close the browser
        driver.quit()

def get_latest_filings(tickers):
    latest_filings = []
    for ticker in tickers:
        result = get_latest_filing(ticker)
        result['ticker'] = ticker
        latest_filings.append(result)
    return latest_filings

tickers = ["APPL", "AMZN"]
latest_filings = get_latest_filings(tickers)

def main(page: ft.Page):
    page.title = "Edgar latest filings"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    def highlight_link(e):
        e.control.style.color = ft.Colors.BLUE
        e.control.update()

    def unhighlight_link(e):
        e.control.style.color = None
        e.control.update()

    page.add(
        ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Ticker")),
                ft.DataColumn(ft.Text("Type")),
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Link"))
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(latest_filing['ticker'], selectable=True)),
                        ft.DataCell(ft.Text(latest_filing['filing_type'], selectable=True)),
                        ft.DataCell(ft.Text(latest_filing['filing_date'], selectable=True)),
                        ft.DataCell(ft.Text(
                            spans=[  
                                ft.TextSpan(
                                    "Visit",
                                    ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                                    url=latest_filing['filing_link'],
                                    on_enter=highlight_link,
                                    on_exit=unhighlight_link,
                            ),]
                        )),
                    ]
                )
            for latest_filing in latest_filings]
        )
    )


ft.app(main)

        # Extract filing details
        # filing_type = cells[0].find_element(By.TAG_NAME, "a").text  # e.g., "10-Q"
        # filing_date = cells[3].text  # e.g., "2023-08-01"
        # filing_link = cells[0].find_element(By.TAG_NAME, "a").get_attribute("href")
        
        # split = re.split('; | - |: ', latest_filing.text)