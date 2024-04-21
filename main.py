import asyncio
from datetime import datetime, timedelta
import logging

# для роботи слід в вірт.оточенні встановити aiohttp модуль (pip install aiohttp)
from aiohttp import ClientSession, ClientConnectorError
from pprint import pprint

URL = 'https://api.privatbank.ua/p24api/exchange_rates?json&date={date}'

async def request(url: str): # робимо запит на апішку
    async with ClientSession() as session:
        try:
            async with session.get(url) as resp: # отримуємо відповідь
                if resp.ok:
                    r = await resp.json() # форматуємо відповідь в джейсон
                    return r
                logging.error(f"Error status: {resp.status} for {url}")
                return None
        except ClientConnectorError as e:
            logging.error(f"Connection error: {str(e)}. Check the link and/or your Internet connection.")
            return None

def pb_handler(result): # функція обробки отриманих даних з апі
    exchange_dict = result.get('exchangeRate')
    usd = None
    eur = None
    for rates in exchange_dict:
        if rates['currency'] == "USD":
            usd = rates
        if rates['currency'] == "EUR":
            eur = rates
    
    return {
        'USD': {
            'purchase': float(usd['purchaseRate']),
            'sale': float(usd['saleRate'])
        },
        'EUR': {
            'purchase': float(eur['purchaseRate']),
            'sale': float(eur['saleRate'])
        }
    }

async def get_exchange_for_date(date, pb_handler): # отримання даних з апі для конкретної дати
    url = URL.format(date=date.strftime('%d.%m.%Y')) # підставляємо потрібну дату в урл
    result = await request(url) 
    if result:
        return {date.strftime('%d.%m.%Y'): pb_handler(result)} # хендлером форматуємо отримані дані

    return {date.strftime('%d.%m.%Y'): None}

async def main(num_days: int):
    today = datetime.today()
    results = []
    tasks = [] 
    for i in range(num_days):
        date = today - timedelta(days=i)
        tasks.append(get_exchange_for_date(date, pb_handler)) # створюємо асинхронні завдання для кожної дати в межах num_days
    results = await asyncio.gather(*tasks) # виконуємо завдання паралельно
    return results

if __name__ == "__main__": 
    import sys
    num_days = int(sys.argv[1]) if len(sys.argv) > 1 else 1 # отримуємо кількість днів від користувача
    if num_days > 10:
        print("You can request data for up to 10 days only.")
    else:
        results = asyncio.run(main(num_days))
        pprint(results)
