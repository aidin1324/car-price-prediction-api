import numpy as np
import pandas as pd

import asyncio
from src.scrap import get_all_car_models_with_selenium
from src.scrap import parse_machine_kg_one_page


async def main():
    url = "https://www.mashina.kg/search/all/?region=all"
    base_url = "https://www.mashina.kg"
    columns = [
        "Год выпуска",
        "Двигатель",
        "Пробег",
        "Коробка",
        "Руль",
        "Цвет",
        "Кузов",
        "Регион, "
        "город продажи",
        "price-dollar"
    ]

    models = get_all_car_models_with_selenium(url)
    last_page = 1753  # 27.09.2024

    data = [
        parse_machine_kg_one_page(
            url=url,
            models=models,
            base_url=base_url,
            columns=columns,
            params={"page": page}
        )
        for page in range(1, last_page + 1)
    ]

    data = await asyncio.gather(*data)

    df = pd.DataFrame(
        data=data,
        columns=["Mark", "Model"]
    )

    df.to_csv("data/row.csv", index=False)


asyncio.run(main())
