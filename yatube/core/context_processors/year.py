import datetime


def year(request):
    today = str(datetime.date.today())
    curr_year = int(today[:4])
    return {
        'year': curr_year,
    }
