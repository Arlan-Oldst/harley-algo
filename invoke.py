from src.controllers.controller import Controller
import json

if __name__ == '__main__':
    with open('event_v3.json', 'r') as f:
        event = json.load(f)
        authorization = 'Bearer eyJraWQiOiJOSk1ITitOYVd4UW03cThPK1ZhRnZPN2JjaDJZMFwvOVwvV05ZamJYa2g2eHc9IiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiJlZTBhMjNjNC1iODk3LTRmMmEtYWUxNS1kZmZmM2EyZGFiOTUiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0yLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMl9QeXo3b1hRam0iLCJjbGllbnRfaWQiOiI0ZzVnZjhhMXYxcWZrZnVocnFhbWFjbG4yMyIsIm9yaWdpbl9qdGkiOiIzYmY0ODUwNS1lNTBmLTQ2YmItODYxMC05ZTcxNmI3ZDk1MjMiLCJldmVudF9pZCI6ImY1MmE0MTlhLThjZTktNGJhMi1iMWVmLTljMjNhMTRlNmEwYiIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3MDQ5NjM3MDYsImV4cCI6MTcwNDk2NzMwNiwiaWF0IjoxNzA0OTYzNzA2LCJqdGkiOiI5MDEyYjIzYi02YmZhLTRjYmYtOWQxZC05YjE4NDM3MjNkNGQiLCJ1c2VybmFtZSI6ImVlMGEyM2M0LWI4OTctNGYyYS1hZTE1LWRmZmYzYTJkYWI5NSJ9.hX57G4YsiNSskesmNgfVd9T8GXJDpIGrjFMuIrRGR7f5TnKfVfLoXk86cp0SukO6KyqUoJwY3eFDo3BfAmEQpOzOnL-dUHIvaeZ2Tuibl9SaTKATfriQIYhh4v7pLUiMc2zqwYEr4u7q_o--XiD2Z54W4sK0GM8KqZduleEFlkuOwyolyv8AHWo_zAMTotHHYQVmaXEbB7aKEH_WpLOWyAZ0kLnDQ_Sq-21UcuhgGumwMHVwnhBqlphdVyeVMu1gN2mgTYvxBvFuOuj_OskFtiC_bYvpxaprayE5iPPUUEe6aZ8eR6pyyKP_YADOVj1RoSl7aa5PNJZpsiPcs8JzwQ'
        print(Controller.retrieve_generated_scenario(authorization, **event))