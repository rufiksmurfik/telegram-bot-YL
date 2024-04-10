import datetime

def isOutdated(dt):
    return datetime.datetime.now() > datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S.%f")

print(isOutdated("2024-04-10 15:20:48.440586"))