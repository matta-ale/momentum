from binance.client import Client
tickers = ['AVAX','ETH','SOL','ADA','MATIC','LINK','BNB']
#digits es la precisión de decimales del precio de cada activo 
digits = {'NIN': 0,'SOL': 3,'AVAX': 3,'ADA': 4,'ETH': 0,'MATIC': 4, 'LINK': 3, 'BNB': 2}
#digits cant es la precisión de decimales de la cantidad de cada activo a operar, expresado en activo (x eth o x btc)
digits_cant = {'NIN': 0,'SOL': 0,'AVAX': 0, 'ADA': 0,'BTC': 3,'ETH': 3,'MATIC': 0, 'LINK': 2, 'BNB': 2}
interval = '2h'
token2 = 'USDT'
timeframe = {'1m' :  Client.KLINE_INTERVAL_1MINUTE, '3m' : Client.KLINE_INTERVAL_3MINUTE,'5m' : Client.KLINE_INTERVAL_5MINUTE,'15m' : Client.KLINE_INTERVAL_15MINUTE,'30m' : Client.KLINE_INTERVAL_30MINUTE,'1h' : Client.KLINE_INTERVAL_1HOUR,'2h' : Client.KLINE_INTERVAL_2HOUR,'4h' : Client.KLINE_INTERVAL_4HOUR,'6h' : Client.KLINE_INTERVAL_6HOUR,'8h' : Client.KLINE_INTERVAL_8HOUR,'12h' : Client.KLINE_INTERVAL_12HOUR,'1d' : Client.KLINE_INTERVAL_1DAY}
minutes = {'1m' : 1, '3m' : 3,'5m' : 5,'15m' : 15,'30m' : 30,'1h' : 60,'2h' : 120,'4h' : 240,'6h' : 360,'8h' : 480,'12h' : 720,'1d' : 1440}
fast_lag = 10
slow_lag = 30
sl = {'SOL': 0.015, 'AVAX': 0.015,'ETH' : 0.015, 'BTC' : 0.015, 'ADA': 0.015,'MATIC': 0.015, 'LINK': 0.015, 'BNB': 0.015}
tp = {'SOL': 0.03,'AVAX': 0.03,'ETH' : 0.03,'BTC' : 0.03, 'ADA': 0.03,'MATIC': 0.03, 'LINK': 0.03, 'BNB': 0.03}
min_usdt = {'SOL': 5.00,'AVAX': 5.00,'ETH' : 5.00,'BTC' : 5.00, 'ADA': 5.00,'MATIC': 5.00, 'LINK': 5.00, 'BNB': 5.00}
position_size = 0.25
cant_rows_df = 120 #cantidad de filas de los df que usamos 
