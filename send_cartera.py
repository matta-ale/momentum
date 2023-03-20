import telegram
from telegram import sendTelegram
import json
import pandas as pd
from binance.enums import *
import config_futures
from binance.client import Client
from Binance_futures import *
from datetime import datetime, timedelta
from parametros import *
#recordar que hay que autorizar la api key en las settings para que pueda gestionar margin
client = Client(config_futures.API_KEY, config_futures.API_SECRET)
#defino función para obtener precio


def precio(activo):
    prices = client.futures_symbol_ticker()
    for i in range(len(prices)):
        if activo == prices[i]['symbol']:
            precio = prices[i]['price']
    return precio
#ok, esto sería lo que me contaba el Matta, viene como un diccionario o df continuo de precios, cuando symbol sea mi symbol traigo el precio   

    
#leo la cartera actual
cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()

msg = 'CANT ACTUAL: ' + str(round(float(cantidad_actual),2))+' USDT\n'
msg += 'DISPONIBLE: ' + str(round(float(disponible),2))+' USDT\n'
msg += 'INV INIC: ' + str(round(float(cant_inic),2)) +' USDT\n'
if len(posiciones) == 0:
    msg += 'POSICIONES: NINGUNA\n'
else:
    msg += 'POSICIONES:\n'
    for item in posiciones:
        msg += f'  {item}: '+ posiciones[item]['posicion'] + '\n'
msg += 'PNL: ' + str(round(float(profit_loss),2)) +'%\n'
#FECHA INICIO BOT
finic = datetime(2022,11,24).date()
now = datetime.utcnow()
date = datetime(now.year,now.month,now.day).date()
delta = float((date - finic).days)
if delta == 0:
    delta = 1

add = 'ANUALIZADO: '+ str(round((pow(1 + (float(profit_loss)/100),365/delta)-1)*100,2))+ "%\n"
msg += add
add = 'FECHA INICIO: ' + str(finic) +'\n\n'
msg += add


balance = client.futures_account_balance()
for dict in balance:
    if dict['asset'] == 'BNB':
        bnb_balance = dict
cant_bnb = round(float(bnb_balance['balance']),4)
precio_bnb = precio('BNBUSDT')
cant_bnb_usd = str(round(float(precio_bnb)*float(cant_bnb),0))

add = 'Cantidad BNB en futures: ' + cant_bnb_usd + ' USD/' +str(round(cant_bnb,2))+' BNB'
msg = msg + add
sendTelegram(msg)





