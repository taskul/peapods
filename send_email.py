import smtplib
import os
from dotenv import load_dotenv

# has to be before evnironment variables are declared
load_dotenv()
PASSWORD = os.environ.get('PASSWORD')
EMAIL = os.environ.get('EMAIL')



def send_invite(reciever_email, sender_name, reciever_name, pod_name):
    '''Sending invitation to join a Pod to team members'''
    message = generate_message(reciever_name, sender_name, pod_name)
    with smtplib.SMTP("smtp.mail.yahoo.com") as connection:
        connection.starttls()
        connection.login(user=EMAIL, password=PASSWORD)
        connection.sendmail(
            from_addr=EMAIL,
            to_addrs=reciever_email,
            msg=f"Subject: You have been invited to join a {pod_name} Pod.\n\n {message}",
        )

def generate_message(reciever_name, sender_name, pod_name):
    return f'''Hello {reciever_name}!\n You have been invited by {sender_name} to join a {pod_name} Pod at PeaPods.\n
    What is a Pod you may ask? PeaPods is a place for teams to learn about eachother's hobbie and interests and be able to see who on your team matches your hobbies at a quick glance.\n 
    Sign up for an account at https://peapods.herokuapp.com/'''
    