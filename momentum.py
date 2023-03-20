import logging
logging.basicConfig(filename="log.txt", level=logging.DEBUG,
                    format="%(asctime)s %(message)s", filemode="w")
#logging.debug("Logging test...")
#logging.info("The program is working as expected")
#logging.warning("The program may not function properly")
#logging.error("The program encountered an error")
#logging.critical("The program crashed")

from telegram import sendTelegram
from datetime import datetime
import pandas as pd
import json
import config_futures
import websocket
import time
from Binance_futures import *
from parametros import *
import runpy
#import sys
#import os
#import pandas_ta as ta
import threading
import numpy as np
       

dfDict = {}  #creo el diccionario de dataFrames, acá se almacenan los df de cada ticker
#bajo los datos para armar los df de cada symbol
for token1 in tickers:
    ticker = token1 + token2
    candles = client.futures_continous_klines(pair = ticker,contractType ='PERPETUAL', interval =timeframe[interval],limit = cant_rows_df)
    data = pd.DataFrame(candles, columns = ['timestamp', 'Open','High','Low','Close','Volume','Col1','Col2','Col3','Col4','Col5','Col6'])
    data = data.drop(['Col1','Col2','Col3','Col4','Col5','Col6'],axis =1)
    data['timestamp']=data['timestamp']/1000
    data['timestamp'] = [datetime.datetime.fromtimestamp(x) for x in data['timestamp']]
    data = data.set_index('timestamp')
    data['Open'] = data['Open'].astype(float)
    data['High'] = data['High'].astype(float)
    data['Low'] = data['Low'].astype(float)
    data['Close'] = data['Close'].astype(float)
    data['Volume'] = data['Volume'].astype(float)
    
    data['fast_lag'] = data['Close'].shift(fast_lag)
    data['slow_lag'] = data['Close'].shift(slow_lag)

    data['max'] = np.maximum(data['fast_lag'],data['slow_lag'])
    data['min'] = np.minimum(data['fast_lag'],data['slow_lag'])

    data['trigger_long_in'] = data['Close'].gt(data['max']).mul(1).diff()
    data['trigger_long_out'] = data['Close'].lt(data['max']).mul(1).diff()
    data['trigger_short_in'] = data['Close'].lt(data['min']).mul(1).diff()
    data['trigger_short_out'] = data['Close'].gt(data['min']).mul(1).diff()    
    
    dfDict[token1] = data 



#creo el string del websocket para todos los tickers
socket = "wss://fstream.binance.com/stream?streams="
for ticker in tickers:   #los tickers vienen de parametros.py
    socket += ticker.lower() + 'usdt@kline_' + interval + '/'

print('arrancando')
def on_open(ws):
    sendTelegram('connection opened')

def on_close(ws, close_status_code, close_msg):
    sendTelegram('closed connection')

def on_message(ws,message):
    
    json_message = json.loads(message)
    candle = json_message['data']['k']
    ticker = candle['s']
    is_candle_closed = candle['x']
    open = float(candle['o'])
    high = float(candle['h'])
    low = float(candle['l'])
    close = float(candle['c'])
    volume = float(candle['v'])
    timestamp = datetime.datetime.fromtimestamp((candle['t'])/1000)
    #actualizo df
    data = dfDict[ticker[:-4]]
    data.loc[timestamp,'Open'] = open
    data.loc[timestamp,'High'] = high
    data.loc[timestamp,'Low'] = low
    data.loc[timestamp,'Close'] = close
    data.loc[timestamp,'Volume'] = volume

    data['fast_lag'] = data['Close'].shift(fast_lag)
    data['slow_lag'] = data['Close'].shift(slow_lag)
    data['max'] = np.maximum(data['fast_lag'],data['slow_lag'])
    data['min'] = np.minimum(data['fast_lag'],data['slow_lag'])

    data['trigger_long_in'] = data['Close'].gt(data['max']).mul(1).diff()
    data['trigger_long_out'] = data['Close'].lt(data['max']).mul(1).diff()
    data['trigger_short_in'] = data['Close'].lt(data['min']).mul(1).diff()
    data['trigger_short_out'] = data['Close'].gt(data['min']).mul(1).diff()  

    dfDict[ticker[:-4]] = data
    
    activo = ticker
    cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()

    if activo in posiciones:
        posicion = posiciones[activo]['posicion']
    else:
        posicion = "LIQUIDO"

    if posicion == 'COMPRADO':
        if data.loc[timestamp,'Close'] <= posiciones[activo]['stop_value']:
            motivo = 'STOP LOSS'
            precio_cierre_target = data.loc[timestamp,'Close']
            cantidad = posiciones[activo]['cantidad']
            precio_aper = posiciones[activo]['precio_aper']
            #mandar thread de cierre:
            t1 = threading.Thread(target=close_long_thread,args=(activo, cantidad, precio_aper, precio_cierre_target, motivo, min_usdt))
            t1.start()
            #cambiar posicion para no mandar a cerrar dos veces:
            lock_json()
            cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
            posiciones[activo]['posicion'] = 'CERRANDO'
            cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
            sendTelegram('CERRAR LONG DE ' + activo +' POR ' + motivo)

        elif data.loc[timestamp,'Close'] >= posiciones[activo]['take_profit']:
            motivo = 'TAKE PROFIT'
            precio_cierre_target = data.loc[timestamp,'Close']
            cantidad = posiciones[activo]['cantidad']
            precio_aper = posiciones[activo]['precio_aper']
            #mandar thread de cierre
            t1 = threading.Thread(target=close_long_thread,args=(activo, cantidad, precio_aper, precio_cierre_target, motivo, min_usdt))
            t1.start()
            #cambiar posicion para no mandar a cerrar dos veces:
            lock_json()
            cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
            posiciones[activo]['posicion'] = 'CERRANDO'
            cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
            sendTelegram('CERRAR LONG DE ' + activo +' POR ' + motivo)

    elif posicion == 'VENDIDO':
        if data.loc[timestamp,'Close'] >= posiciones[activo]['stop_value']:
            motivo = 'STOP LOSS'
            precio_cierre_target = data.loc[timestamp,'Close']
            cantidad = posiciones[activo]['cantidad']
            precio_aper = posiciones[activo]['precio_aper']
            #mandar thread de cierre
            t1 = threading.Thread(target=close_short_thread,args=(activo, cantidad, precio_aper, precio_cierre_target, motivo, min_usdt))
            t1.start()
            #cambiar posicion para no mandar a cerrar dos veces:
            lock_json()
            cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
            posiciones[activo]['posicion'] = 'CERRANDO'
            cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
            sendTelegram('CERRAR SHORT DE ' + activo +' POR ' + motivo)

        elif data.loc[timestamp,'Close'] <= posiciones[activo]['take_profit']:
            motivo = 'TAKE PROFIT'
            precio_cierre_target = data.loc[timestamp,'Close']
            cantidad = posiciones[activo]['cantidad']
            precio_aper = posiciones[activo]['precio_aper']
            #mandar thread de cierre
            t1 = threading.Thread(target=close_short_thread,args=(activo, cantidad, precio_aper, precio_cierre_target, motivo, min_usdt))
            t1.start()
            #cambiar posicion para no mandar a cerrar dos veces:
            lock_json()
            cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
            posiciones[activo]['posicion'] = 'CERRANDO'
            cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
            sendTelegram('CERRAR SHORT DE ' + activo +' POR ' + motivo)

    if is_candle_closed == True:
        
        # SALIDAS LONG Y SHORT POR CONDICION DE SALIDA:
        if posicion == 'COMPRADO':
            if data.loc[timestamp,'trigger_long_out'] == 1:
                motivo = 'CONDICION DE SALIDA'
                precio_cierre_target = data.loc[timestamp,'Close']
                cantidad = posiciones[activo]['cantidad']
                precio_aper = posiciones[activo]['precio_aper']
                #mandar thread de cierre
                t1 = threading.Thread(target=close_long_thread,args=(activo, cantidad, precio_aper, precio_cierre_target, motivo, min_usdt))
                t1.start()
                #cambiar posicion para no mandar a cerrar dos veces:
                lock_json()
                cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
                posiciones[activo]['posicion'] = 'CERRANDO'
                cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
                sendTelegram('CERRAR LONG DE ' + activo +' POR ' + motivo)

        elif posicion == 'VENDIDO':
            if data.loc[timestamp,'trigger_short_out'] == 1:
                motivo = 'CONDICION DE SALIDA'
                precio_cierre_target = data.loc[timestamp,'Close']
                cantidad = posiciones[activo]['cantidad']
                precio_aper = posiciones[activo]['precio_aper']
                #mandar thread de cierre
                t1 = threading.Thread(target=close_short_thread,args=(activo, cantidad, precio_aper, precio_cierre_target, motivo, min_usdt))
                t1.start()
                #cambiar posicion para no mandar a cerrar dos veces:
                lock_json()
                cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
                posiciones[activo]['posicion'] = 'CERRANDO'
                cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
                sendTelegram('CERRAR SHORT DE ' + activo +' POR ' + motivo)

        elif posicion == 'LIQUIDO':

            if data.loc[timestamp,'trigger_long_in'] == 1:
                lock_json()
                cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
                if disponible >= cantidad_actual * position_size:
                    precio_aper_target = data.loc[timestamp,'Close']
                    cantidad_aper = cantidad_actual * position_size * 0.9998
                    if cantidad_aper > min_usdt[activo[:-4]]:
                        disponible -= cantidad_actual * position_size
                        cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
                        # mandar al thread a comprar:
                        t1 = threading.Thread(target=open_long_thread,args=(precio_aper_target, activo, cantidad_aper, digits_cant, digits, sl, tp, min_usdt))
                        t1.start()
                        sendTelegram('ABRIR LONG DE '+ activo +' @ '+str(round(float(precio_aper_target),digits[activo[:-4]])))
                    else:
                        unlock_json()
                        logging.debug(f'{cantidad_aper} menor a min_usdt para {activo}')
                        sendTelegram(f'{cantidad_aper} < a min_usdt para {activo}')
                else:
                    unlock_json()
                    logging.debug('no hay fondos suficientes para nuevas posiciones')

            elif  data.loc[timestamp,'trigger_short_in'] == 1:
                lock_json()
                cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
                if disponible >= cantidad_actual * position_size:
                    precio_aper_target = data.loc[timestamp,'Close']
                    cantidad_aper = cantidad_actual * position_size * 0.9998
                    if cantidad_aper > min_usdt[activo[:-4]]:
                        disponible -= cantidad_actual * position_size
                        cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
                        # mandar al thread a comprar:
                        t1 = threading.Thread(target=open_short_thread,args=(precio_aper_target, activo, cantidad_aper, digits_cant, digits, sl, tp, min_usdt))
                        t1.start()
                        sendTelegram('ABRIR SHORT DE '+ activo +' @ '+str(round(float(precio_aper_target),digits[activo[:-4]])))
                    else:
                        unlock_json()
                        logging.debug(f'{cantidad_aper} menor a min_usdt para {activo}')
                        sendTelegram(f'{cantidad_aper} < a min_usdt para {activo}')
                else:
                    unlock_json()
                    logging.debug('no hay fondos suficientes para nuevas posiciones')


        if ticker[:-4] == tickers[0]:
            runpy.run_path('send_cartera.py')

        
    if len(dfDict[ticker[:-4]]) > cant_rows_df:
        dfDict[ticker[:-4]].drop(index=dfDict[ticker[:-4]].index[0],axis=0,inplace=True)
            
while True:       
    try:
        ws = websocket.WebSocketApp(socket, on_open=on_open,on_close=on_close,on_message=on_message)
        ws.run_forever() 
    except Exception as e:
        logging.debug("Websocket connection Error  : {0}".format(e))                    
        logging.debug("Reconnecting websocket  after 5 sec")
        time.sleep(5)
