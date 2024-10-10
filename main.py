import base64
import os.path
import socket
import re
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2 import service_account

# grupo = "E:\home\\abs\Aplicativos\leitura_ults\whatsbot\grupo.txt"
grupo = '/home/abs/Aplicativos/leitura_ults/whatsbot/grupo.txt'

# Escopo necessário para acessar os e-mails e modificar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]
USER_EMAIL = 'sistemasabsengenharia@gmail.com'
SERVICE_ACCOUNT_FILE = "token_servico.json"
def main():
    #"""Exemplo de leitura de e-mails do Gmail com filtro de título."""
    try:
        creds = None
        # O arquivo token.json armazena as credenciais de acesso do usuário.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # Se não houver credenciais válidas, faça login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Salva as credenciais para futuras execuções
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        # credentials = service_account.Credentials.from_service_account_file(
        # SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        # delegated_credentials = credentials.with_subject(USER_EMAIL)
        # Conectar ao serviço Gmail API
        service = build('gmail', 'v1', credentials=creds)

        # Define o título (assunto) que você quer buscar
        subject_query = 'Localização GPS'

        # Filtrar mensagens usando o parâmetro 'q', e adicionei o is:unread para buscar só mensagens nao lidas
        query = f'subject:{subject_query} is:unread'

        # Chamada à API para listar os e-mails da caixa de entrada que correspondem à busca
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
    except Exception as e:
        datahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Erro ao configurar o serviço Gmail API as {datahora}:  {str(e)}")
        enviar_mensagem('27999438898@c.us',f"Erro no serviço do GMAIL - {str(e)}")
    
    if not messages:
        print('Nenhuma mensagem encontrada com o título especificado.')
    else:
        print('Mensagens encontradas:')
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            # print(f"Mensagem de: {msg['snippet']}")
            # print(f"Mensagem: {msg['payload']}")
            parts  = msg.get('payload').get('parts')
            body = ""
            if parts:
                    for part in parts:
                        #if part.get('mimeType') == 'text/plain':  # Corpo do e-mail em texto simples
                        if part.get('mimeType') == 'text/plain' or part.get('mimeType') == 'text/html':
                            data = part.get('body').get('data')
                            body += base64.urlsafe_b64decode(data).decode('utf-8').replace('<br>', '\n')
                        break
            else:
                body = base64.urlsafe_b64decode(msg.get('payload').get('body').get('data')).decode('utf-8').replace('<br>', '\n')
            # data = payload.get('parts').get('body').get('data')
            # body = base64.urlsafe_b64decode(data).decode('utf-8')
            print(f"Mensagem:\n{body}")
            padrao = r'Latitude\:(-[\d]+\.[\d]+)[\W<br>]+Longitude:(-[\d]+\.[\d]+)'
            matchs = re.search(padrao,body)
            msg_spot = re.search(r'Mensagem:\s*(.* ?)\W',body).group(1)
            
            if matchs:
                # Despacha no whatsapp
                with open(grupo, 'r') as f:
                    conteudo = f.read().strip()  # Lê todo o conteúdo e remove espaços em branco,
                    print(conteudo)
                    if conteudo == '': #Caso esteja vazio só envie para mim mesmo.
                        enviar_mensagem('27999438898@c.us',f"#L{matchs.group(1)};{matchs.group(2)};{msg_spot}")
                    else: #Caso tenha conteudo despache no grupo.
                        enviar_mensagem(conteudo,f"#L{matchs.group(1)};{matchs.group(2)};{msg_spot}")
            # Marca como lida
            service.users().messages().modify(
                userId='me',
                id=message['id'],
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
def enviar_mensagem(numero, mensagem):
    #HOST =  'ABSSERVER'  # O endereço IP do servidor JavaScript
    HOST =  '127.0.0.1'  # O endereço IP do servidor JavaScript
    PORT = 65432        # A porta em que o servidor JavaScript está ouvindo

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(f"{numero}${mensagem}\n".encode())
        
def enviar_localizacao(numero, mensagem, latitude, longitude):
    #HOST =  'ABSSERVER'  # O endereço IP do servidor JavaScript
    HOST =  '127.0.0.1'  # O endereço IP do servidor JavaScript
    PORT = 65432        # A porta em que o servidor JavaScript está ouvindo

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(f"{numero}${mensagem}\n".encode())


if __name__ == '__main__':
    main()