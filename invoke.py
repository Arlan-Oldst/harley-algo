from src.controllers.controller import Controller
import json

if __name__ == '__main__':
    with open('event_v3.json', 'r') as f:
        event = json.load(f)
        authorization = 'Bearer eyJraWQiOiI5U3FPY3NGS25cL1pYalFaU1l5YjRKZnNjT2UyUkIxSlY1ak5nTjJCazZWVT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJiNDI1ZmQwZi1lNWFkLTQzYjYtYmQyMy1hMDBlMmE4OTkxYjEiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0yLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMl9YTWp1N2RYQnYiLCJjbGllbnRfaWQiOiI3djYwN2o3aWY0cXM5NzVnOGQ3OWFpbjdkZCIsIm9yaWdpbl9qdGkiOiI4YjM2Y2MxMC01NzFjLTQ2YTctYWM0Yi03NGI3YWY2MTg5NTYiLCJldmVudF9pZCI6ImY1ZTdlMGM1LTBiOGQtNDE3MS04ZGY3LTllNTMzZTc4OWU4NCIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3MDMwNTY5MTMsImV4cCI6MTcwMzA2MDUxMywiaWF0IjoxNzAzMDU2OTEzLCJqdGkiOiJjM2I4Nzk4Ni1iZGM2LTRiODktODEyMy1lMTlkNTZlNDc4ZDEiLCJ1c2VybmFtZSI6ImI0MjVmZDBmLWU1YWQtNDNiNi1iZDIzLWEwMGUyYTg5OTFiMSJ9.AANxNrXPIW7pC2sg9H1MBhBUTaAAv_TKnVqaMdmp0bFFoexOgrhYAxMZlOeKQUnkE_gVok7ambHHp83LKFgoJ9Pnr0DJcmG9ImnnfcsOB_ZK-rCqqNi6JY4iIBXAG6Y04oYiH8QjZz0xSpzMpk4tssOeUgxx5FymraU8FYQhTwo4zNmGAIRDMZ2caC_pnooqpI1nQq0JkuiPK2hcCDeJ4tUz5Q77Sl3WfmrkJurBcw9izw_kyk8w5dtdNH2kIArJkgmgP8Au5eVs9383Jm_664mrqSXbvv7DJD-pH6Fh8WGxff73fvU5l1eXmqjQkSuYFj-xvcpS5N9KckQaGjIHrw'
        print(Controller.retrieve_generated_scenario(authorization, **event))