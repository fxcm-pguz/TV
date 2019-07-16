import fxcmrest
import time
import logging
import json
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('token', help="token to use when logging in")
parser.add_argument('logfile', help="logfile to save to")
parser.add_argument('--server', '-s', default="demo", help="server to connect to (demo/real)")
args = parser.parse_args()

def onMessage(event, message=''):
	if event == 'Order':
		m = json.loads(message)
		if m.get('action','') == 'I':
			r.positionId = m.get('tradeId',False)
			logging.info("got positionID: {0}".format(r.positionId))
	else:
		logging.info("message: {0}:{1}".format(event,message))

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s %(message)s",
	handlers=[
		logging.FileHandler(args.logfile),
		logging.StreamHandler(sys.stdout)
	])

c = fxcmrest.Config(args.server, token=args.token)
r = fxcmrest.FXCMRest(c)
r.onMessage = onMessage
r.connect()

r.request('POST','/trading/subscribe', {'models':'Order'})
r.account = r.request('GET','/trading/get_model',{'models':'Account'}).json()['accounts'][0]['accountId']

while(True):
	orderId = False
	ok1 = False
	ok2 = False
	try:
		orderId = r.request('POST','/trading/open_trade',{'account_id':r.account, 'symbol':'EUR/USD', 'is_buy':'true', 'amount':100, 'time_in_force':'FOK'}).json().get('data',{}).get('orderId',False)
		time.sleep(3)
		if r.positionId:
			ok1 = r.request('POST','/trading/change_trade_stop_limit',{'trade_id':r.positionId, 'is_stop':'true', 'rate':-20}).json().get('response',{}).get('executed',False)
			ok2 = r.request('POST','/trading/close_trade',{'trade_id':r.positionId, 'amount':100, 'order_type':'AtMarket', 'time_in_force':'FOK'}).json().get('response',{}).get('executed',False)
		else:
			logging.info("positionId not found!")
			break
		if ok1 and ok2:
			time.sleep(60*10)
		else:
			logging.info("trade change or trade close failed")
			break
	except Exception as e:
		logging.info("exception: {0}".format(e))
		break