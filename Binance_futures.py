import logging
logging.basicConfig(filename="log.txt", level=logging.DEBUG,
                    format="%(asctime)s %(message)s", filemode="a")
logging.basicConfig()
from binance.enums import *
import config_futures
from binance.client import Client
import math
import datetime
import time
from telegram import sendTelegram
import telegram
import pandas as pd
import json


client = Client(config_futures.API_KEY, config_futures.API_SECRET)


def lock_excel():
    try:
        with open("permiso_excel.json", "r") as f:      # read the json file
            variables = json.load(f)
        while variables['access'] != 'unlocked':
            logging.debug('esperando excel file')
            time.sleep(0.3)    # podría ser otra cantidad
            with open("permiso_excel.json", "r") as f:      # read the json file
                variables = json.load(f)
        variables['access'] = 'locked'
        with open("permiso_excel.json", "w") as f:      # write the json file  
            variables = json.dump(variables,f)
    except FileNotFoundError:
        variables = {}
        variables['access'] = 'locked'
        with open("permiso_excel.json", "w") as f:      # write the json file  
            variables = json.dump(variables,f)
    
    return

def unlock_excel():
    
    with open("permiso_excel.json", "r") as f:      # read the json file
        variables = json.load(f)
    variables['access'] = 'unlocked'
    with open("permiso_excel.json", "w") as f:      # write the json file  
        variables = json.dump(variables,f)
    return



def aper_to_excel(fecha_aper, tipo_trade, activo, precio_aper, precio_aper_target, cant_aper):

    lock_excel()
    try:
        dfTrades = pd.read_excel('Trades.xlsx')
        index = dfTrades.index[-1] + 1
        dfTrades.loc[index,'Nro trade'] = round(dfTrades["Nro trade"].iloc[-1] + 1)
    except FileNotFoundError:
        dfTrades = pd.DataFrame()
        index = 0
        dfTrades.loc[index,'Nro trade'] = 1
    dfTrades.loc[index,'Fecha apertura'] = fecha_aper #viene de la lógica del df
    dfTrades.loc[index,'Tipo trade'] = tipo_trade
    dfTrades.loc[index,'Activo'] = activo
    dfTrades.loc[index,'Precio apertura'] = round(float(precio_aper),4)
    dfTrades.loc[index,'Precio aper target'] = round(float(precio_aper_target),4)
    if tipo_trade == 'LONG':    
        dfTrades.loc[index,'Slippage aper %'] = (-1)*round((float(precio_aper)/float(precio_aper_target)-1)*100,3) 
    else:
        dfTrades.loc[index,'Slippage aper %'] = round((float(precio_aper)/float(precio_aper_target)-1)*100,3)
    dfTrades.loc[index,'Cantidad apertura'] = round(float(cant_aper),4)
    dfTrades.loc[index,'USDT apertura'] = round(float(precio_aper)*float(cant_aper),2)
    dfTrades.loc[index,'Comisión apertura'] = 0.0002*float(precio_aper)*float(cant_aper)
    dfTrades.set_index('Nro trade', inplace = True)
    dfTrades.to_excel('Trades.xlsx')
    unlock_excel()

    return

def cierre_to_excel(activo, cantidad_actual, profit_loss, resultado_usdt, resultado, fecha_cierre, precio_cierre, precio_cierre_target, motivo):
    
    lock_excel()
    dfTrades = pd.read_excel('Trades.xlsx')
    index = dfTrades.loc[dfTrades['Activo'] == activo,:].tail(1).index[0] #filtro la última fila(tail(1)) en la que Activo==activo y guardo el index
    precio_aper = dfTrades.loc[index,'Precio apertura']
    cant_aper = dfTrades.loc[index,'Cantidad apertura']
    comi_aper = dfTrades.loc[index,'Comisión apertura']
    tipo_trade = dfTrades.loc[index,'Tipo trade']
    dfTrades.loc[index,'Fecha cierre'] = fecha_cierre #viene de la lógica del df
    dfTrades.loc[index,'Precio cierre'] = round(float(precio_cierre),4)
    dfTrades.loc[index,'Precio cierre target'] = round(float(precio_cierre_target),4)
    dfTrades.loc[index,'Comisión cierre'] = 0.0002*float(precio_cierre)*float(cant_aper)
    if tipo_trade == 'SHORT':    
        dfTrades.loc[index,'Slippage cierre %'] = (-1)*round((float(precio_cierre)/float(precio_cierre_target)-1)*100,3)    
    else:
        dfTrades.loc[index,'Slippage cierre %'] = round((float(precio_cierre)/float(precio_cierre_target)-1)*100,3)
    cant_cierre = cant_aper * precio_cierre
    dfTrades.loc[index,'Cantidad cierre'] = round(float(cant_cierre),4)
    dfTrades.loc[index,'Motivo cierre'] = motivo

    dfTrades.loc[index,'Resultado USDT'] = resultado_usdt
    dfTrades.loc[index,'Resultado %'] = resultado
    if dfTrades.loc[index,'Resultado %'] >= 0:
        dfTrades.loc[index,'WIN/LOSS'] = 'WIN'
    else:
        dfTrades.loc[index,'WIN/LOSS'] = 'LOSS'
    dfTrades.loc[index,'Total USDT'] = cantidad_actual
    dfTrades.loc[index,'Resultado acum %'] = profit_loss
    dfTrades.set_index('Nro trade', inplace = True)
    dfTrades.to_excel('Trades.xlsx')
    unlock_excel()

    return


def read_cartera():

    #import json         # import the json library
    with open("cartera.json", "r") as f:      # read the json file
        variables = json.load(f)
    cant_inic = variables["cant_inic"]    # To get the value currently stored
    disponible = variables['disponible']
    cantidad_actual = variables['cantidad_actual']
    profit_loss = variables['profit_loss']
    posiciones = variables["posiciones"]

    return  cant_inic, disponible, cantidad_actual, profit_loss, posiciones

def modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones): #,cant_inic, resto, profit_loss, precio_apertura, stop_value):

    #import json         # import the json library
    with open("cartera.json", "r") as f:      # read the json file
        variables = json.load(f)
    variables["cant_inic"] = cant_inic     # To get the value currently stored
    variables['disponible'] = disponible 
    variables['cantidad_actual'] = cantidad_actual 
    variables['profit_loss'] = profit_loss 
    variables["posiciones"] = posiciones
    variables['access'] = 'unlocked' 

    with open("cartera.json", "w") as f:      # write the json file  
        variables = json.dump(variables,f)
    logging.debug(variables)
    return cant_inic, disponible, cantidad_actual, profit_loss, posiciones

def lock_json():
    #import json
    with open("cartera.json", "r") as f:      # read the json file
        variables = json.load(f)
    while variables['access'] != 'unlocked':
        logging.debug('esperando json file')
        time.sleep(0.3)    # podría ser otra cantidad
        with open("cartera.json", "r") as f:      # read the json file
            variables = json.load(f)
    variables['access'] = 'locked'
    with open("cartera.json", "w") as f:      # write the json file  
        variables = json.dump(variables,f)
    return

def unlock_json():
    #import json
    with open("cartera.json", "r") as f:      # read the json file
        variables = json.load(f)
    variables['access'] = 'unlocked'
    with open("cartera.json", "w") as f:      # write the json file  
        variables = json.dump(variables,f)
    return


def precio(activo):
    prices = client.futures_symbol_ticker()
    for i in range(len(prices)):
        if activo == prices[i]['symbol']:
            precio = prices[i]['price']
    return precio

#función para truncar decimales, de manera de ajustar a la cantidad múltiplo mínima de ETHUSDT PERPETUAL, que es 0.01
def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

def update_order(activo, orderId):
    while True:
        try:
            time.sleep(0.1)
            my_order = client.futures_get_order(symbol = activo, orderId = orderId)
        except:
            logging.debug('Esperando order status')
            continue
        break
    return my_order


def open_long(precio_input, activo, cantidad, digits, min_usdt): #compra en futuros   este 'cantidad' es en USDT
    client.futures_change_leverage(symbol=activo, contractType = 'PERPETUAL', leverage=1)
    cant_ajust = float(truncate(cantidad/float(precio_input),digits))
    cant_cripto_aper = cant_ajust
    startTime = time.time()
    trade = ''
    order_list = []
    qtty_order = 0
    qtty_usdt = 0
    qtty = 0
    while trade != 'COMPLETED':    
        estado = 'EXPIRED'
        while estado == 'EXPIRED':
            startTime = time.time()
            precio_actual = float(precio(activo))
            if (cant_ajust*precio_actual) > min_usdt:
                try: 
                    long_order_ol = client.futures_create_order(symbol=activo,contractType = 'PERPETUAL', side = 'BUY', type = 'LIMIT',price = precio_actual, quantity = cant_ajust,timeInForce = 'GTX') #acá lo pongo quoteOrderQty porque le digo los BTC que tengo (supongo que compro ETHBTC)       
                    orderId = long_order_ol['orderId']
                    logging.debug('OrderId1: ' + str(orderId))
                    long_order_ol = update_order(activo, orderId)
                    estado = long_order_ol['status']
                    logging.debug('Estado1: ' + str(estado))
                    time.sleep(0.2)
                except:
                    logging.debug('fallo en create_order')
                    time.sleep(0.2)
                    # no cambió ni trade ni estado asique lo va a volver a intentar
            else:
                estado = 'FILLED' #no realmente filled, es para que salga ok del trade
                trade = 'COMPLETED'
                logging.debug('Entry parcial. El saldo es demasiado pequeño')
                sendTelegram('ENTRY PARCIAL EN LONG @'+activo)
        delta = 0
        while (estado == 'NEW' and delta <= 10):
            long_order_ol = update_order(activo, orderId)
            estado = long_order_ol['status']
            delta = time.time() - startTime
        logging.debug('Estado2: ' + str(estado))
        if estado == 'NEW':
            try:
                long_order_ol = client.futures_cancel_order(symbol = activo, orderId = orderId)
                logging.debug(long_order_ol)
            except:
                logging.debug('no se pudo cancelar orden (en NEW)')
            time.sleep(1)
            exec_qtty = float(long_order_ol['executedQty'])
            cant_ajust -= exec_qtty  #se le resta a la cantidad por las dudas que suceda que al cancelar de "NEW" a "CANCELED", en el medio se pase a partially filled
            logging.debug(exec_qtty)
            long_order_ol = update_order(activo, orderId)
            estado = long_order_ol['status']
            logging.debug(estado)
            order_list.append(orderId)
            qtty = 0
            avg_price = 0
        if estado == 'PARTIALLY_FILLED':
            while estado == 'PARTIALLY_FILLED':
                time.sleep(10) #cambié de 5 a 10 segundos
                update_order_ol = update_order(activo, orderId)
                estado = update_order_ol['status']
                logging.debug(estado)
                if estado == 'PARTIALLY_FILLED':
                    try:
                        update_order_ol = client.futures_cancel_order(symbol = activo, orderId = orderId)
                        logging.debug(update_order_ol)
                    except:
                        logging.debug('no se pudo cancelar orden (en partially filled)') #puse esto antes para que pare de fillear pedazos y luego sí calcule las qtty
                    time.sleep(1) #agrego esto para darle tiempo a binance para actualizar el estado
                    update_order_ol = update_order(activo, orderId)
                    qtty_open_order = float(update_order_ol['cumQuote'])  #*(1-0.0002) aquí no lo sacamos para que no altere el valor cripto
                    avg_price_order = float(update_order_ol['avgPrice'])
                    exec_qtty = float(update_order_ol['executedQty'])
                    cant_ajust -= exec_qtty
                    logging.debug(cant_ajust)
                    logging.debug(exec_qtty)
                    order_list.append(orderId)
                    time.sleep(1)
                update_order_ol = update_order(activo, orderId)
                estado = update_order_ol['status']
                logging.debug(estado)   
        
        if estado == 'FILLED':                                  
            long_order_ol = update_order(activo, orderId)
            order_list.append(orderId)
            trade = 'COMPLETED'
        
    order_list = list(dict.fromkeys(order_list))
    for i in order_list:
        update_order_ol = update_order(activo, i)
        logging.debug(update_order_ol)
        while update_order_ol['status'] == 'NEW':
            sendTelegram('ORDER FILLED PASO A NEW')
            time.sleep(5)
            update_order_ol = update_order(activo, i)
            logging.debug(update_order_ol) 
        qtty_usdt_order = float(update_order_ol['cumQuote'])
        qtty_usdt += qtty_usdt_order
        qtty_order = float(update_order_ol['executedQty']) 
        qtty += qtty_order
    avg_price = float(qtty_usdt)/float(qtty)    
    return update_order_ol, qtty, avg_price, estado

def open_long_sin_slip(precio_input, activo, cantidad, digits, min_usdt): #compra en futuros   # min_usdt no se usa, solo ahí para futuros cambios y no tener que cambiar argumentos
    client.futures_change_leverage(symbol=activo, contractType = 'PERPETUAL', leverage=1)
    cant_ajust = truncate(cantidad/float(precio_input),digits)
    cant_cripto_aper = cant_ajust
    startTime = time.time()
    trade = 'ACTIVE'
    #era_partial = 'NO'
    order_list = []
    qtty_order = 0
    qtty_usdt = 0
    qtty = 0
    estado = 'EXPIRED'
    while trade == 'ACTIVE':    
        #estado = 'EXPIRED'
        newStartTime = time.time()
        new_delta = 0
        while (estado == 'EXPIRED' and new_delta <= 300):
            startTime = time.time()
            precio_actual = float(precio_input) #precio(activo)
            long_order_ol = client.futures_create_order(symbol=activo, contractType = 'PERPETUAL', side = 'BUY', type = 'LIMIT',price = precio_actual, quantity = cant_ajust,timeInForce = 'GTX') #acá lo pongo quoteOrderQty porque le digo los BTC que tengo (supongo que compro ETHBTC)       
            orderId = long_order_ol['orderId']
            logging.debug('OrderId1: ' + str(orderId))
            long_order_ol = update_order(activo, orderId)
            estado = long_order_ol['status']
            logging.debug('Estado1: ' + str(estado))
            new_delta = time.time() - newStartTime
            time.sleep(0.2)
        delta = 0
        while (estado == 'NEW' and delta <= 60):
            long_order_ol = update_order(activo, orderId)
            estado = long_order_ol['status']
            delta = time.time() - startTime
        logging.debug('Estado2: ' + str(estado))
        if estado == 'NEW':
            try:
                long_order_ol = client.futures_cancel_order(symbol = activo, orderId = orderId) #era cancel_order_ol
                logging.debug(long_order_ol)
            except:
                logging.debug('no se pudo cancelar orden (en NEW)')
            time.sleep(1)
            exec_qtty = float(long_order_ol['executedQty']) #era cancel_order_ol
            cant_ajust -= exec_qtty  #se le resta a la cantidad por las dudas que suceda que al cancelar de "NEW" a "CANCELED", en el medio se pase a partially filled
            logging.debug(exec_qtty)
            long_order_ol = update_order(activo, orderId)
            estado = long_order_ol['status']
            logging.debug(estado)
            qtty = 0
            avg_price = 0
            order_list.append(orderId)
            #if (exec_qtty == 0) and (era_partial == 'NO'):
            trade = 'ABANDONED'
            logging.debug(trade)
            
        if estado == 'PARTIALLY_FILLED':
            #era_partial = 'SI'
            while estado == 'PARTIALLY_FILLED':
                time.sleep(10) # le damos 10 segs
                update_order_ol = update_order(activo, orderId)
                estado = update_order_ol['status']
                logging.debug(estado)
                if estado == 'PARTIALLY_FILLED':
                    try:
                        update_order_ol = client.futures_cancel_order(symbol = activo, orderId = orderId)
                        logging.debug(update_order_ol)
                    except:
                        logging.debug('no se pudo cancelar orden (en partially filled)') #puse esto antes para que pare de fillear pedazos y luego sí calcule las qtty
                    time.sleep(1) #agrego esto para darle tiempo a binance para actualizar el estado
                    update_order_ol = update_order(activo, orderId)
                    qtty_open_order = float(update_order_ol['cumQuote'])  #*(1-0.0002) aquí no lo sacamos para que no altere el valor cripto
                    avg_price_order = float(update_order_ol['avgPrice'])
                    exec_qtty = float(update_order_ol['executedQty'])
                    cant_ajust -= exec_qtty
                    logging.debug(cant_ajust)
                    logging.debug(exec_qtty)
                    order_list.append(orderId)
                    time.sleep(1)
                update_order_ol = update_order(activo, orderId)
                estado = update_order_ol['status']
                logging.debug(estado)
                trade = 'ABANDONED'
                logging.debug(trade)   
        
        if estado == 'FILLED':                                  
            long_order_ol = update_order(activo, orderId)
            order_list.append(orderId)
            trade = 'COMPLETED'
            logging.debug(trade)
        
    order_list = list(dict.fromkeys(order_list))
    logging.debug(order_list)
    for i in order_list:
        update_order_ol = update_order(activo, i)
        logging.debug(update_order_ol)
        while update_order_ol['status'] == 'NEW':
            sendTelegram('ORDER FILLED PASO A NEW')
            time.sleep(5)
            update_order_ol = update_order(activo, i)
            logging.debug(update_order_ol) 
        qtty_usdt_order = float(update_order_ol['cumQuote'])
        qtty_usdt+= qtty_usdt_order
        qtty_order = float(update_order_ol['executedQty']) 
        qtty += qtty_order
    if qtty > 0:
        avg_price = float(qtty_usdt)/float(qtty)
        estado = 'FILLED'
    else:
        avg_price = 0
        estado = 'ABANDONED'   

    return update_order_ol, qtty, avg_price, estado

def close_long(activo, cantidad, precio_aper, precio_actual, min_usdt): #cierro long en futuros
    cant_cripto_aper = cantidad #no necesito ajustar porque ya es la cantidad con la que abrimos
    #cant_aper = float(cantidad)*float(precio_aper)
    client.futures_change_leverage(symbol=activo, contractType = 'PERPETUAL', leverage=1)
    estado = 'EXPIRED'
    delta = 0
    qtty_close = 0
    order_list = []
    while estado != 'FILLED':
        while estado == 'PARTIALLY_FILLED':
            time.sleep(10) #cambié de 5 a 10 segundos
            update_order_cl = update_order(activo, orderId)
            estado = update_order_cl['status']
            if estado == 'PARTIALLY_FILLED':
                try:
                    update_order_cl = client.futures_cancel_order(symbol = activo, orderId = orderId)
                    logging.debug(update_order_cl)
                except:
                    logging.debug('no se pudo cancelar orden (en partially filled)') #puse esto antes para que pare de fillear pedazos y luego sí calcule las qtty
                time.sleep(1) #agrego esto para darle tiempo a binance para actualizar el estado
                update_order_cl = update_order(activo, orderId)
                qtty_close_order = float(update_order_cl['cumQuote'])  #*(1-0.0002) aquí no lo sacamos para que no altere el valor cripto
                avg_price_order = float(update_order_cl['avgPrice'])
                exec_qtty = float(update_order_cl['executedQty'])
                cantidad -= exec_qtty #cantidad se transforma en cantidad que falta
                logging.debug(qtty_close)
                order_list.append(orderId)
                time.sleep(1)
            update_order_cl = update_order(activo, orderId)
            estado = update_order_cl['status']
            logging.debug(estado)  #esto es nuevo
        if estado != 'FILLED': #esto es nuevo, EXPIRED, CANCELED           
            precio_actual = float(precio(activo))
            startTime = time.time()    
            if (float(cantidad)*float(precio_actual)) > min_usdt:
                try:
                    close_long_output = client.futures_create_order(symbol=activo,contractType = 'PERPETUAL', side = 'SELL', type = 'LIMIT',price= precio_actual, quantity = cantidad,timeInForce = 'GTX',reduceOnly = False) #acá lo pongo quoteOrderQty porque le digo los BTC que tengo (supongo que compro ETHBTC)
                    orderId = close_long_output['orderId']      #acá no hay un try, nunca pasó que la data no haya llegado a tiempo como en los update?  
                    update_order_cl = update_order(activo, orderId)
                    estado = update_order_cl['status']
                    logging.debug(estado)
                    time.sleep(0.2)
                except:
                    logging.debug('fallo en create_order')
                    time.sleep(0.2)
                    # el estado va a seguir siendo el mismo asique lo va a volver a intentar while
                while estado == 'NEW':
                    delta = time.time() - startTime 
                    if delta > 30: #mayor a 30 segundos, si pasaron 30 segs me voy a cancelar la orden
                        try:
                            update_order_cl = client.futures_cancel_order(symbol = activo, orderId = orderId)
                            logging.debug(update_order_cl)
                        except:
                            logging.debug('no se pudo cancelar orden (en delta > 30)')
                        
                        update_order_cl = update_order(activo, orderId)
                        exec_qtty = float(update_order_cl['executedQty'])
                        cantidad -= exec_qtty  #se le resta a la cantidad por las dudas que suceda que al cancelar de "NEW" a "CANCELED", en el medio se pase a partially filled
                        logging.debug(exec_qtty)
                        estado = update_order_cl['status']
                        logging.debug(estado)
                        
                    else:
                        update_order_cl = update_order(activo, orderId)
                        estado = update_order_cl['status'] 
                        logging.debug(estado)
                        time.sleep(1)             # le voy diciendo que cada un segundo chequee el estado de la órden...                                  
                time.sleep(0.5)
            else:
                estado = 'FILLED' #no es realmente FILLED pero es para que salga del loop
                logging.debug('Exit parcial. El saldo es demasiado pequeño')
                sendTelegram('EXIT PARCIAL DE '+activo+'!!!!')
        try:
            order_list.append(orderId)
            logging.debug(orderId)
            logging.debug(order_list)
        except:
            logging.debug('no se pudo append orderId a order_list') #esto puede pasar por fallo en create_order

    qtty_close = 0
    qtty = 0
    order_list = list(dict.fromkeys(order_list))
    for i in order_list:
        update_order_cl = update_order(activo, i)
        logging.debug(update_order_cl)
        while update_order_cl['status'] == 'NEW':
            sendTelegram('ORDER FILLED PASO A NEW')
            time.sleep(5)
            update_order_cl = update_order(activo, i)
            logging.debug(update_order_cl) 
        qtty_close_order = float(update_order_cl['cumQuote'])
        qtty_close += qtty_close_order
        qtty_order = float(update_order_cl['executedQty'])
        qtty += qtty_order
    avg_price = float(qtty_close)/float(qtty_order)
    qtty_close = qtty_close*(1-0.0002) #ojo me puedo estar yendo de acá con un qtty_close parcial
    return update_order_cl, qtty_close, avg_price, estado 

def open_short(precio_input, activo, cantidad, digits, min_usdt): #short en futuros   
    client.futures_change_leverage(symbol=activo, contractType = 'PERPETUAL', leverage=1)
    cant_ajust = float(truncate(cantidad/float(precio_input),digits))
    cant_cripto_aper = cant_ajust
    startTime = time.time()
    trade = ''
    order_list = []
    qtty_order = 0
    qtty_usdt = 0
    qtty = 0
    while trade != 'COMPLETED':    
        estado = 'EXPIRED'
        while estado == 'EXPIRED':
            startTime = time.time()
            precio_actual = float(precio(activo))
            if (float(cant_ajust)*float(precio_actual)) > min_usdt: 
                try:
                    short_order_os = client.futures_create_order(symbol=activo,contractType = 'PERPETUAL', side = 'SELL', type = 'LIMIT',price = precio_actual, quantity = cant_ajust,timeInForce = 'GTX') #acá lo pongo quoteOrderQty porque le digo los BTC que tengo (supongo que compro ETHBTC)       
                    orderId = short_order_os['orderId']
                    logging.debug('OrderId1: ' + str(orderId))
                    short_order_os = update_order(activo, orderId)
                    estado = short_order_os['status']
                    logging.debug('Estado1: ' + str(estado))
                    time.sleep(0.2)
                except:
                    logging.debug('fallo en create_order')
                    time.sleep(0.2)
                    # no cambió ni trade ni estado asique lo va a volver a intentar
            else:
                estado = 'FILLED' #no es filled de verdad pero es para que salga correctamente del trade
                trade = 'COMPLETED'
                logging.debug('Entry parcial. El saldo es demasiado pequeño')
                sendTelegram('ENTRY PARCIAL EN SHORT @'+activo)

        delta = 0
        while (estado == 'NEW' and delta <= 10):
            short_order_os = update_order(activo, orderId)
            estado = short_order_os['status']
            delta = time.time() - startTime
        logging.debug('Estado2: ' + str(estado))
        if estado == 'NEW':
            try:
                short_order_os = client.futures_cancel_order(symbol = activo, orderId = orderId)
                logging.debug(short_order_os)
            except:
                logging.debug('no se pudo cancelar orden (en NEW)')
            time.sleep(1)
            exec_qtty = float(short_order_os['executedQty'])
            cant_ajust -= exec_qtty  #se le resta a la cantidad por las dudas que suceda que al cancelar de "NEW" a "CANCELED", en el medio se pase a partially filled
            logging.debug(exec_qtty)
            short_order_os = update_order(activo, orderId)
            estado = short_order_os['status']
            logging.debug(estado)
            order_list.append(orderId)
            qtty = 0
            avg_price = 0
        if estado == 'PARTIALLY_FILLED':
            while estado == 'PARTIALLY_FILLED':
                time.sleep(10) #cambié de 5 a 10 segundos
                short_order_os = update_order(activo, orderId)
                estado = short_order_os['status']
                logging.debug(estado)
                if estado == 'PARTIALLY_FILLED':
                    try:
                        short_order_os = client.futures_cancel_order(symbol = activo, orderId = orderId)
                        logging.debug(short_order_os)
                    except:
                        logging.debug('no se pudo cancelar orden (en partially filled)') #puse esto antes para que pare de fillear pedazos y luego sí calcule las qtty
                    time.sleep(1) #agrego esto para darle tiempo a binance para actualizar el estado
                    short_order_os = update_order(activo, orderId)
                    qtty_open_order = float(short_order_os['cumQuote'])  #*(1-0.0002) aquí no lo sacamos para que no altere el valor cripto
                    avg_price_order = float(short_order_os['avgPrice'])
                    exec_qtty = float(short_order_os['executedQty'])
                    cant_ajust -= exec_qtty
                    logging.debug(cant_ajust)
                    logging.debug(exec_qtty)
                    order_list.append(orderId)
                    time.sleep(1)
                update_order_os = update_order(activo, orderId)
                estado = update_order_os['status']
                logging.debug(estado)   
        
        if estado == 'FILLED':                                  
            short_order_os = update_order(activo, orderId)
            order_list.append(orderId)
            trade = 'COMPLETED'
        
    order_list = list(dict.fromkeys(order_list))
    for i in order_list:
        update_order_os = update_order(activo, i)
        logging.debug(update_order_os)
        while update_order_os['status'] == 'NEW':
            sendTelegram('ORDER FILLED PASO A NEW')
            time.sleep(5)
            update_order_os = update_order(activo, i)
            logging.debug(update_order_os)  
        qtty_usdt_order = float(update_order_os['cumQuote'])
        qtty_usdt+= qtty_usdt_order
        qtty_order = float(update_order_os['executedQty']) 
        qtty += qtty_order
    avg_price = float(qtty_usdt)/float(qtty)    
    return update_order_os, qtty, avg_price, estado

def open_short_sin_slip(precio_input, activo, cantidad, digits, min_usdt): #short en futuros   
    client.futures_change_leverage(symbol=activo, contractType = 'PERPETUAL', leverage=1)
    cant_ajust = truncate(cantidad/float(precio_input),digits)
    cant_cripto_aper = cant_ajust
    startTime = time.time()
    trade = 'ACTIVE'
    #era_partial = 'NO'
    order_list = []
    qtty_order = 0
    qtty_usdt = 0
    qtty = 0
    estado = 'EXPIRED'
    while trade == 'ACTIVE':    
        #estado = 'EXPIRED'
        newStartTime = time.time()
        new_delta = 0
        while (estado == 'EXPIRED' and new_delta <= 300):
            startTime = time.time()
            precio_actual = float(precio_input) #precio(activo)
            short_order_os = client.futures_create_order(symbol=activo,contractType = 'PERPETUAL', side = 'SELL', type = 'LIMIT',price = precio_actual, quantity = cant_ajust,timeInForce = 'GTX') #acá lo pongo quoteOrderQty porque le digo los BTC que tengo (supongo que compro ETHBTC)       
            orderId = short_order_os['orderId']
            logging.debug('OrderId1: ' + str(orderId))
            short_order_os = update_order(activo, orderId)
            estado = short_order_os['status']
            logging.debug('Estado1: ' + str(estado))
            new_delta = time.time() - newStartTime
            time.sleep(0.2)
        delta = 0
        while (estado == 'NEW' and delta <= 60):
            short_order_os = update_order(activo, orderId)
            estado = short_order_os['status']
            delta = time.time() - startTime
        logging.debug('Estado2: ' + str(estado))
        if estado == 'NEW':
            try:
                short_order_os = client.futures_cancel_order(symbol = activo, orderId = orderId)
                logging.debug(short_order_os)
            except:
                logging.debug('no se pudo cancelar orden (en NEW)')
            time.sleep(1)
            exec_qtty = float(short_order_os['executedQty'])
            cant_ajust -= exec_qtty  #se le resta a la cantidad por las dudas que suceda que al cancelar de "NEW" a "CANCELED", en el medio se pase a partially filled
            logging.debug(exec_qtty)
            short_order_os = update_order(activo, orderId)
            estado = short_order_os['status']
            logging.debug(estado)
            qtty = 0
            avg_price = 0
            order_list.append(orderId)
            #if (exec_qtty == 0) and (era_partial == 'NO'):
            trade = 'ABANDONED'
            logging.debug(trade)

        if estado == 'PARTIALLY_FILLED':
            #era_partial = 'SI'
            while estado == 'PARTIALLY_FILLED':
                time.sleep(10) #cambié de 5 a 10 segundos
                short_order_os = update_order(activo, orderId)
                estado = short_order_os['status']
                logging.debug(estado)
                if estado == 'PARTIALLY_FILLED':
                    try:
                        short_order_os = client.futures_cancel_order(symbol = activo, orderId = orderId)
                        logging.debug(short_order_os)
                    except:
                        logging.debug('no se pudo cancelar orden (en partially filled)') #puse esto antes para que pare de fillear pedazos y luego sí calcule las qtty
                    time.sleep(1) #agrego esto para darle tiempo a binance para actualizar el estado
                    short_order_os = update_order(activo, orderId)
                    qtty_open_order = float(short_order_os['cumQuote'])  #*(1-0.0002) aquí no lo sacamos para que no altere el valor cripto
                    avg_price_order = float(short_order_os['avgPrice'])
                    exec_qtty = float(short_order_os['executedQty'])
                    cant_ajust -= exec_qtty
                    logging.debug(cant_ajust)
                    logging.debug(exec_qtty)
                    order_list.append(orderId)
                    time.sleep(1)
                update_order_os = update_order(activo, orderId)
                estado = update_order_os['status']
                logging.debug(estado)
                trade = 'ABANDONED'
                logging.debug(trade)   
        
        if estado == 'FILLED':                                  
            short_order_os = update_order(activo, orderId)
            order_list.append(orderId)
            trade = 'COMPLETED'
        
    order_list = list(dict.fromkeys(order_list))
    logging.debug(order_list)
    for i in order_list:
        update_order_os = update_order(activo, i)
        logging.debug(update_order_os)
        while update_order_os['status'] == 'NEW':
            sendTelegram('ORDER FILLED PASO A NEW')
            time.sleep(5)
            update_order_os = update_order(activo, i)
            logging.debug(update_order_os)  
        qtty_usdt_order = float(update_order_os['cumQuote'])
        qtty_usdt+= qtty_usdt_order
        qtty_order = float(update_order_os['executedQty']) 
        qtty += qtty_order
    if qtty > 0:
        avg_price = float(qtty_usdt)/float(qtty)
        estado = 'FILLED'
    else:
        avg_price = 0
        estado = 'ABANDONED'

    return update_order_os, qtty, avg_price, estado

def close_short(activo, cantidad, precio_aper, precio_actual, min_usdt): #cierro short en futuros
    cant_cripto_aper = cantidad
    cant_aper = float(cantidad)*float(precio_aper) #los usdt de apertura
    client.futures_change_leverage(symbol=activo, contractType = 'PERPETUAL', leverage=1)
    estado = 'EXPIRED'
    delta = 0
    qtty_close = 0
    order_list = []
    while estado != 'FILLED':
        while estado == 'PARTIALLY_FILLED':
            time.sleep(10) 
            update_order_cs = update_order(activo, orderId)
            estado = update_order_cs['status']
            if estado == 'PARTIALLY_FILLED':
                try:
                    update_order_cs = client.futures_cancel_order(symbol = activo, orderId = orderId) #puse esto antes para que pare de fillear pedazos y luego sí calcule las qtty
                except:
                    logging.debug('no se pudo cancelar orden (en partially filled)')
                time.sleep(1) #agrego esto para darle tiempo a binance para actualizar el estado
                update_order_cs = update_order(activo, orderId)
                qtty_close_order = float(update_order_cs['cumQuote'])  #*(1-0.0002) aquí no lo sacamos para que no altere el valor cripto
                avg_price_order = float(update_order_cs['avgPrice'])
                exec_qtty = float(update_order_cs['executedQty'])
                cantidad -= exec_qtty
                logging.debug(qtty_close)
                order_list.append(orderId)
                time.sleep(1)
            update_order_cs = update_order(activo, orderId)
            estado = update_order_cs['status']
            logging.debug(estado)  #esto es nuevo
        if estado != 'FILLED':
            precio_actual = float(precio(activo))
            startTime = time.time()
            if (float(cantidad)*float(precio_actual)) > min_usdt:
                try: 
                    close_short_output = client.futures_create_order(symbol=activo,contractType = 'PERPETUAL', side = 'BUY', type = 'LIMIT',price= precio_actual, quantity = cantidad,timeInForce = 'GTX',reduceOnly = False) #acá lo pongo quoteOrderQty porque le digo los BTC que tengo (supongo que compro ETHBTC)
                    orderId = close_short_output['orderId']        
                    update_order_cs = update_order(activo, orderId)
                    estado = update_order_cs['status']
                    logging.debug(estado)
                    time.sleep(0.2)
                except:
                    logging.debug('fallo en create_order')
                    time.sleep(0.2)
                    # el estado va a seguir siendo el mismo asique lo va a volver a intentar while
                while estado == 'NEW':
                    delta = time.time()- startTime   
                    if delta > 30: #mayor a 30 segundos
                        try:
                            update_order_cs = client.futures_cancel_order(symbol = activo, orderId = orderId)
                            logging.debug(update_order_cs)
                        except:
                            logging.debug('no se pudo cancelar orden (en delta > 30)')
                        update_order_cs = update_order(activo, orderId)
                        exec_qtty = float(update_order_cs['executedQty'])
                        cantidad -= exec_qtty  #se le resta a la cantidad por las dudas que suceda que al cancelar de "NEW" a "CANCELED", en el medio se pase a partially filled
                        logging.debug(exec_qtty)
                        estado = update_order_cs['status']
                        logging.debug(estado)
                    else:
                        update_order_cs = update_order(activo, orderId)
                        estado = update_order_cs['status']
                        logging.debug(estado)
                        time.sleep(1)
                time.sleep(0.5)                                               
            else:
                estado = 'FILLED' #no es realmente FILLED pero es para que salga del loop
                logging.debug('Exit parcial. El saldo es demasiado pequeño')
                sendTelegram('EXIT PARCIAL DE '+activo+'!!!!')
        try:
            order_list.append(orderId)
            logging.debug(orderId)
            logging.debug(order_list)
        except:
            logging.debug('no se pudo append orderId a order_list') #esto puede pasar por fallo en create_order

    qtty_close = 0
    qtty = 0
    order_list = list(dict.fromkeys(order_list))
    for i in order_list:
        update_order_cs = update_order(activo, i)
        logging.debug(update_order_cs)
        while update_order_cs['status'] == 'NEW':
            sendTelegram('ORDER FILLED PASO A NEW')
            time.sleep(5)
            update_order_cs = update_order(activo, i)
            logging.debug(update_order_cs) 
        qtty_close_order = float(update_order_cs['cumQuote'])
        qtty_close += qtty_close_order
        qtty_order = float(update_order_cs['executedQty'])
        qtty += qtty_order
    avg_price = float(qtty_close)/float(qtty)
    qtty_close = float(cant_aper) +(float(cant_aper) - float(qtty_close))-float(qtty_close)*0.0002 # los_usdt_de_apertura + (usdt_apertura - usdt_salida) - comisión_de_salida
    return update_order_cs, qtty_close, avg_price, estado

def balance():
    balance_total = client.futures_account_balance()[1]['balance']
    balance_transferible = client.futures_account_balance()[1]['withdrawAvailable']
    return balance_total, balance_transferible

def position(activo):
    
    position = client.futures_position_information()
    for i in range(len(position)):
        if activo == position[i]['symbol']:
            pos_activo = position[i]
    #para los short hay que multiplicar x -1 el resultado
    if float(pos_activo['positionAmt']) >= 0:
        profit_loss = 100*float(pos_activo['unRealizedProfit'])/(float(pos_activo['entryPrice'])*float(pos_activo['positionAmt']))
    else:
        profit_loss = -100*float(pos_activo['unRealizedProfit'])/(float(pos_activo['entryPrice'])*float(pos_activo['positionAmt']))
    profit_loss = round(profit_loss,2)
    profit_loss_abs = str(round(float(pos_activo['unRealizedProfit']),2))+' USDT'
    return profit_loss_abs, profit_loss


def open_long_thread(precio_input, activo, cantidad_aper, digits_cant, digits, sl, tp, min_usdt):
    estado = 'START'
    # mandamos a abrir el trade y traer feedback:
    try:
        long_order, qtty, avg_price, estado = open_long_sin_slip(precio_input, activo, cantidad_aper, digits_cant[activo[:-4]], min_usdt[activo[:-4]])
    except Exception as e:
        sendTelegram(e)
        sendTelegram('FALLO OPEN LONG DE '+activo)
    # hacemos el resto de las operaciones con el feedback:
    if estado == 'FILLED':
        lock_json()
        cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
        posiciones[activo] = {}
        posiciones[activo]['posicion'] = 'COMPRADO'
        posiciones[activo]['cantidad'] = float(qtty) #la cantidad en crypto
        posiciones[activo]['precio_aper'] = float(avg_price)
        posiciones[activo]['stop_value'] = float(avg_price)*(1-float(sl[activo[:-4]]))
        posiciones[activo]['take_profit'] = float(avg_price)*(1+float(tp[activo[:-4]]))
        disponible += float(cantidad_aper) - (float(qtty)*float(avg_price)*(1.0002)) #le devuelvo el teórico que le resté antes y le resto el definitivo
        cantidad_actual -= (float(qtty)*float(avg_price)*(0.0002)) #resto la comisión de la cartera
        cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
        msg = 'OPERADO LONG DE ' +str(round(float(cantidad_aper),2)) + ' USDT de ' + str(activo)+'\nCant Operado: ' +str(round(float(qtty),digits_cant[activo[:-4]]))+' '+str(activo[:-4])+'\nPrecio Operado: '+str(round(float(avg_price),digits[activo[:-4]]))+' USDT\nStop Loss: '+str(round(float(posiciones[activo]['stop_value']),digits[activo[:-4]]))+' USDT\nTake_Profit: '+str(round(float(posiciones[activo]['take_profit']),digits[activo[:-4]]))
        sendTelegram(msg)
        time_aper = datetime.datetime.fromtimestamp(float(long_order['updateTime'])/1000).strftime('%Y/%m/%d %H:%M:%S')
        aper_to_excel(time_aper,'LONG', activo, avg_price, precio_input, qtty)
    else:
        lock_json()
        cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
        disponible += float(cantidad_aper)*(1.0002) #en caso de no abrir le devuelvo lo 'reservado' a disponible
        cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
        sendTelegram('NO SE PUDO ABRIR LONG DE '+ activo)
    import runpy
    runpy.run_path('send_cartera.py')
    return

def close_long_thread(activo, cantidad, precio_aper, precio_cierre_target, motivo, min_usdt):
    # mandamos a cerrar la op y traer feedback:
    try:
        close_long_order, qtty_close, avg_price, estado = close_long(activo, cantidad, precio_aper, precio_cierre_target, min_usdt[activo[:-4]])
    except Exception as e:
        sendTelegram(e)
        sendTelegram('CUIDADO ERROR EN CIERRE DE '+activo)
    # hacemos el resto de las operaciones con el feedback:
    sendTelegram('CERRADO LONG DE ' + activo +' POR ' + motivo)
    cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
    precio_aper = posiciones[activo]['precio_aper']
    resultado_usdt = float(qtty_close) - (float(precio_aper)*float(cantidad)*(1 + 0.0002)) #qtty_close ya tiene la comisión de salida y *(1+0.0002) añade la comisión de entrada
    resultado = ((resultado_usdt)/(float(precio_aper)*float(cantidad)))*100 
    sendTelegram('P/L OPERACIÓN: ' + str(round(float(resultado),2)) + '%')
    # leer de nuevo cartera para minimizar cambios de otros threads:
    lock_json()
    cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
    disponible += float(qtty_close)
    cantidad_actual += resultado_usdt #que podría ser negativo
    profit_loss = (float(cantidad_actual)/float(cant_inic)-1)*100
    del posiciones[activo]
    # actualizar cartera:
    cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
    # actualizar excel:
    time_close = datetime.datetime.fromtimestamp(float(close_long_order['updateTime'])/1000).strftime('%Y/%m/%d %H:%M:%S')
    precio_cierre = float(avg_price)
    cierre_to_excel(activo, cantidad_actual, profit_loss, resultado_usdt, resultado, time_close, precio_cierre, precio_cierre_target, motivo)
    import runpy
    runpy.run_path('send_cartera.py')
    return


def open_short_thread(precio_input, activo, cantidad_aper, digits_cant, digits, sl, tp, min_usdt):
    estado = 'START'
    # mandamos a abrir el trade y traer feedback:
    try:
        short_order, qtty, avg_price, estado = open_short_sin_slip(precio_input, activo, cantidad_aper, digits_cant[activo[:-4]], min_usdt[activo[:-4]])
    except Exception as e:
        sendTelegram(e)
        sendTelegram('FALLO OPEN SHORT DE '+activo)
    # hacemos el resto de las operaciones con el feedback:
    if estado == 'FILLED':
        lock_json()
        cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
        posiciones[activo] = {}
        posiciones[activo]['posicion'] = 'VENDIDO'
        posiciones[activo]['cantidad'] = float(qtty) #la cantidad en crypto
        posiciones[activo]['precio_aper'] = float(avg_price)
        posiciones[activo]['stop_value'] = float(avg_price)*(1+float(sl[activo[:-4]]))
        posiciones[activo]['take_profit'] = float(avg_price)*(1-float(tp[activo[:-4]]))
        disponible += float(cantidad_aper) - (float(qtty)*float(avg_price)*(1.0002)) #le devuelvo el teórico que le resté antes y le resto el definitivo
        cantidad_actual -= (float(qtty)*float(avg_price)*(0.0002)) #resto la comisión de la cartera
        cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
        msg = 'OPERADO SHORT DE ' +str(round(float(cantidad_aper),2)) + ' USDT de ' + str(activo)+'\nCant Operado: ' +str(round(float(qtty),digits_cant[activo[:-4]]))+' '+str(activo[:-4])+'\nPrecio Operado: '+str(round(float(avg_price),digits[activo[:-4]]))+' USDT\nStop Loss: '+str(round(float(posiciones[activo]['stop_value']),digits[activo[:-4]]))+' USDT\nTake_Profit: '+str(round(float(posiciones[activo]['take_profit']),digits[activo[:-4]]))
        sendTelegram(msg)
        time_aper = datetime.datetime.fromtimestamp(float(short_order['updateTime'])/1000).strftime('%Y/%m/%d %H:%M:%S')
        aper_to_excel(time_aper,'SHORT', activo, avg_price, precio_input, qtty)
    else:
        lock_json()
        cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
        disponible += float(cantidad_aper)*(1.0002) #en caso de no abrir le devuelvo lo 'reservado' a disponible
        cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
        sendTelegram('NO SE PUDO ABRIR SHORT DE '+ activo)
    import runpy
    runpy.run_path('send_cartera.py')
    return

def close_short_thread(activo, cantidad, precio_aper, precio_cierre_target, motivo, min_usdt):
    # mandamos a cerrar la op y traer feedback:
    try:
        close_short_order, qtty_close, avg_price, estado = close_short(activo, cantidad, precio_aper, precio_cierre_target, min_usdt[activo[:-4]])
    except Exception as e:
        sendTelegram(e)
        sendTelegram('CUIDADO ERROR EN CIERRE DE '+activo)
    # hacemos el resto de las operaciones con el feedback:
    sendTelegram('CERRADO SHORT DE ' + activo +' POR ' + motivo)
    cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
    precio_aper = posiciones[activo]['precio_aper']
    resultado_usdt = float(qtty_close) - (float(precio_aper)*float(cantidad)*(1 + 0.0002)) #qtty_close ya tiene la comisión de salida y *(1+0.0002) añade la comisión de entrada
    resultado = ((resultado_usdt)/(float(precio_aper)*float(cantidad)))*100 
    sendTelegram('P/L OPERACIÓN: ' + str(round(float(resultado),2)) + '%')
    # leer de nuevo cartera para minimizar cambios de otros threads:
    lock_json()
    cant_inic, disponible, cantidad_actual, profit_loss, posiciones = read_cartera()
    disponible += float(qtty_close)
    cantidad_actual += resultado_usdt #que podría ser negativo
    profit_loss = (float(cantidad_actual)/float(cant_inic)-1)*100
    del posiciones[activo]
    # actualizar cartera:
    cant_inic, disponible, cantidad_actual, profit_loss, posiciones = modify_cartera(cant_inic, disponible, cantidad_actual, profit_loss, posiciones)
    # actualizar excel:
    time_close = datetime.datetime.fromtimestamp(float(close_short_order['updateTime'])/1000).strftime('%Y/%m/%d %H:%M:%S')
    precio_cierre = float(avg_price)
    cierre_to_excel(activo, cantidad_actual, profit_loss, resultado_usdt, resultado, time_close, precio_cierre, precio_cierre_target, motivo)
    import runpy
    runpy.run_path('send_cartera.py')
    return

