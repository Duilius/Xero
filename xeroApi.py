import json
import requests
import webbrowser
import base64

client_id=''
client_secret=''
redirect_url='https://xero.com'
scope='offline_access accounting.transactions'
b64_id_secret= base64.urlsafe_b64encode(bytes(client_id + ':' + client_secret, 'utf-8'))

def XeroFirstAuth():
    # 1. Send a user to authorize your app
    auth_url = ('''https://login.xero.com/identity/connect/authorize?''' + 
                '''response_type=code''' + 
                '''&client_id=''' + redirect_url +
                '''&scope=''' + scope +
                '''&state=Duilius1511''')
    webbrowser.open_new(auth_url)

    # 2. Users are redirected back to you with a code
    auth_res_url = input('What is the response URL? ')
    start_number = auth_res_url.find('code=') + len('code=')
    end_number = auth_res_url.find('&scope')
    auth_code = auth_res_url[start_number:end_number]
    print(auth_code)
    print('\n')

    # 3. Exchange the code
    exchange_code_url = 'https://identity.xero.com/connect/token'
    response = requests.post(exchange_code_url,
                             headers= {
                                'Authorization': 'Basic' + b64_id_secret
                             },
                             data= {
                                'grant_type': 'authorization_code',
                                'code': auth_code,
                                'redirect_uri': redirect_url
                             })
    json_response = response.json()
    print(json_response)
    print('\n')

    # 4. Receive your tokens
    return [json_response['access_token'], json['refresh_token']]

# 5. Check the full set of tenants you've been authorized to access
def XeroTenants(access_token):
        conntection_url = 'https://api.xero.com/connections'
        response = requests.get(conntection_url,
                                headers= {
                                        'Authorization' : 'Bearer' + access_token,
                                        'Content-Type': 'application/json'
                                })
        json_response = response.json()
        print(json_response)

        for tenants in json_response:
                json_dict = tenants
        return json_dict['tennantId']

# 6.1 Refreshing access_tokens
def XeroRefreshToken(refresh_token):
        token_refresh_url = 'https://identity.xero.com/connect/token'
        response = requests.post(token_refresh_url,
                                 headers= {
                                        'Authorization': 'Basic' + b64_id_secret,
                                        'Content-Type' : 'Application/x-www-form-urlencode'
                                        },
                                        data = {
                                            'grant_type': 'refresh_token',
                                            'refresh_token': refresh_token
                                        })
        json_response = response.json()
        print(json_response)

        new_refresh_token = json_response['refresh_token']
        rt_file = open('refresh_token.txt','w')
        rt_file.write(new_refresh_token)
        rt_file.close()

        return [json_response['access_token'], json_response['refresh_token']]


# 6.2 Call the API
def XeroRequests():
        old_refresh_token = open('refresh_token.txt','r').read()
        new_tokens = XeroRefreshToken(old_refresh_token)
        xero_tenant_id = XeroTenants(new_tokens[0])

        get_url = 'https://api.xero.com/api.xro/2.0/Invoices'
        response = requests.get(get_url,
                                headers= {
                                    'Authorization': 'Bearer' + new_tokens[0],
                                    'Xero-tenant-id': xero_tenant_id,
                                    'Accept' :'application/json'
                                })
        json_response = response.json()
        print(json_response)

        xero_output = open('xero_output.txt', 'w')
        xero_output.write(response.text)
        xero_output.close()



def export_csv():
        invoices = open('xero_output.txt','r').read()
        json_invoice = json.loads(invoices)
        analysis = open(r'analysis.csv','w')
        analysis.write('Type' + ',' + 'Total') 
        analysis.write('\n')
        for invoices in json_invoice['Invoices']:
                analysis.write(invoices['Type'] + ',' + str(invoices['Total']))
                analysis.write('\n')
        analysis.close()


import pandas as pd
import matplotlib.pyplot as plt

def chart_data():
        df = pd.read_csv('analysis.csv')
        pvt = df[ ['Type', 'Total']].groupby('Type').sum()
        print(pvt)

        pvt.plot.bar(stacked = True)
        plt.show()