from src.controllers.controller import Controller
import json

if __name__ == '__main__':
    with open('event_v3.json', 'r') as f:
        event = json.load(f)
        authorization = 'Bearer eyJraWQiOiI5U3FPY3NGS25cL1pYalFaU1l5YjRKZnNjT2UyUkIxSlY1ak5nTjJCazZWVT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJiNDI1ZmQwZi1lNWFkLTQzYjYtYmQyMy1hMDBlMmE4OTkxYjEiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0yLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMl9YTWp1N2RYQnYiLCJjbGllbnRfaWQiOiI3djYwN2o3aWY0cXM5NzVnOGQ3OWFpbjdkZCIsIm9yaWdpbl9qdGkiOiIyZjRjMmY3YS1mNTQzLTRmNDEtYTEyZi1mYTBiZTljZTVmNzIiLCJldmVudF9pZCI6Ijk5OWE1NGNjLTI1OWEtNGQ1Mi1hZjZkLTNmYjllYTEwZmQyMCIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3MDMwNzcyMjYsImV4cCI6MTcwMzA4MDgyNiwiaWF0IjoxNzAzMDc3MjI2LCJqdGkiOiI5ZTRiYTgxZS03NDFjLTRhNjUtOTI3Zi1hZDI5ZGNjZTdlNDAiLCJ1c2VybmFtZSI6ImI0MjVmZDBmLWU1YWQtNDNiNi1iZDIzLWEwMGUyYTg5OTFiMSJ9.cTwNlX8cezFKlJ95wytnGyQ3HtZMwPmfySi86Fu7TOLzi7kgazFAKPOJoNA3siEnvd1Zu-PARVBJtOIXfkJylpTSSnN1CB-6N9FcLEJkIoZBNO7KyhFRCpOi9S9d0KeKoRAxgGLleSP0qGOextxOs60zdsCdCVisd3miOkmwY7wNxSApauqQ46ttR6IHomN2u0UNwXzq5U_gRaqpmX-2sd5Sm4PJnPK1gyIpHt9LKce46RqL5uuCAIJpA8OK52J6aYQMKyRGitVmQR5hQSqVwBSOyq8zCFWeD7a-sH0SRL0k_EmdxEV0iy6watdKdq2NP0_02WOEC0Vyoh84KyO77g'
        print(Controller.retrieve_generated_scenario(authorization, **event))