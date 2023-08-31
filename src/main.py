import requests

def main():
    print('test')
    get()
    
def get():
    # r = requests.get('https://ttlivewebapi.fxopen.net:8443/api/v2/public/quotehistory/EURUSD/5/bars/ask?timestamp=1693254648000&count=5')
    r = requests.get('https://xapi.xtb.com:5124/getChartRangeRequest')
    print(r.json())
    
def post():
    data = {
	"command": "getChartRangeRequest",
	"arguments": {
		"info": CHART_RANGE_INFO_RECORD
	}
}

    r = requests.post('https://httpbin.org/post', json=data)
    print(r.json())
    
if __name__ == '__main__':
    main()