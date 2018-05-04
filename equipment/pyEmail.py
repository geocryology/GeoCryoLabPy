import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText

class Emailer():

    def __init__(self, email, password):
        self.email    = email
        self.password = password

    def send(self, to, subject, files=[]):
        msg = MIMEMultipart()
        msg["From"]    = self.email
        msg["To"]      = to
        msg["Subject"] = subject
        msg.preamble   = ""

        for f in files:
            attachment = MIMEText(open(f).read(), _subtype="text")
            attachment.add_header("Content-Disposition", "attachment", filename=f)
            msg.attach(attachment)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(self.email, self.password)
        server.sendmail(self.email, to, msg.as_string())
        server.quit()
