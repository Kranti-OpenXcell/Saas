# # task.py
# from celery import shared_task
# import mailtrap as mt

# @shared_task
# def send_async_email(subject, recipient_email, body):
#     mail = mt.Mail(
#         sender=mt.Address(email="hello@demomailtrap.com", name="Mailtrap Test"),
#         to=[mt.Address(email=recipient_email)],
#         subject=subject,
#         text=body,
#         category="Integration Test"
#     )

#     client = mt.MailtrapClient(token="f7a0b8be19a80a96735576862bfef47b")
#     response = client.send(mail)

#     print(response)
