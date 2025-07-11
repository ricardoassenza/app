import smtplib
from email.message import EmailMessage

EMAIL_ADDRESS = 'oficialloshunicos@gmail.com'
EMAIL_PASSWORD = 'eijwmireuryaouzw'  # sem espaços

print("Iniciando script...")

msg = EmailMessage()
msg['Subject'] = 'Teste de envio via Python com STARTTLS'
msg['From'] = EMAIL_ADDRESS
msg['To'] = 'assenzaricardo@gmail.com'
msg.set_content('Este é um e-mail enviado por script Python usando SMTP do Gmail com STARTTLS.')

print("Mensagem criada, tentando conectar ao servidor SMTP...")

try:
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        print("Conectado ao SMTP, iniciando TLS...")
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        print("TLS iniciado, tentando logar...")
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("Login realizado, enviando email...")
        smtp.send_message(msg)
        print("Email enviado com sucesso!")
except Exception as e:
    print("Erro aconteceu:", e)
