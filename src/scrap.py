import numpy as np

import aiohttp
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
import time


async def fetch_url(url: str, params: dict) -> str | None:
    timeout = aiohttp.ClientTimeout(total=80)
    connector = aiohttp.TCPConnector(limit=100)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            print(f"Request failed: {e}")
            return None


def get_all_car_models_with_selenium(
        url: str
) -> list:
    driver = webdriver.Chrome()

    driver.get(url)
    time.sleep(3)

    dropdown_button = driver.find_element(By.CLASS_NAME, 'btn.dropdown-toggle.bs-placeholder.btn-default')
    dropdown_button.click()

    dropdown_menu_items = driver.find_elements(By.CLASS_NAME, 'name-selected-mark.ellipsis')
    dropdown_menu_items = [element.text for element in dropdown_menu_items if element.text != '']

    driver.quit()
    return dropdown_menu_items


def split_name_and_model(models: list, car_string: str) -> list:
    for model in models:
        if car_string.startswith(model):
            return [model, car_string[len(model):].strip()]
    return [None, car_string]


def other_detail_parse(
        car_banner
) -> list:
    color = car_banner.find(
        "div", class_="item-info-wrapper"
    ).find(
        "p", "year-miles"
    ).i["title"]

    year_miles = car_banner.find(
        "div", class_="block info-wrapper item-info-wrapper"
    ).find(
        "p", class_="year-miles"
    ).text.replace("\n", "").replace(" ", "").split(",")

    if len(year_miles) == 2:
        year, v_engine, gearbox = year_miles[0], None, year_miles[1]
    else:
        year, v_engine, gearbox = year_miles

    body_type, fuel_type = car_banner.find(
        "div", class_="block info-wrapper item-info-wrapper"
    ).find(
        "p", class_="body-type"
    ).text.replace("\n", "").replace(" ", "").split(",")

    volume = car_banner.find(
        "div", class_="block info-wrapper item-info-wrapper"
    ).find(
        "p", class_="volume"
    ).text.strip().replace("\n", "").split(",")

    if len(volume) == 1:
        sw_location, mileage = volume[0], None
    else:
        sw_location, mileage = volume

    location = car_banner.find(
        "p", class_="city"
    ).text.replace("\n", "").split()[0]

    price_in_usd = car_banner.find(
        "div", class_="block price"
    ).find("strong").text.replace("\n", "").replace(" ", "")
    return [
        color,
        year, v_engine, gearbox,
        body_type, fuel_type,
        sw_location, mileage,
        location,
        price_in_usd
    ]


async def parse_machine_kg_one_page(
        url: str,
        models: list[str],
        params: dict
) -> np.ndarray:
    text = await fetch_url(url, params)
    soup = BeautifulSoup(text, "lxml")

    car_banners = soup.find_all("div", class_="list-item list-label")

    data = np.array(
        [
            split_name_and_model(
                models,
                car_banner.find("h2").text.strip()
            )
            + other_detail_parse(
                car_banner
            )

            for car_banner in car_banners
        ]
    )
    print(f"page {params.get('page')} parsed!")
    return data
