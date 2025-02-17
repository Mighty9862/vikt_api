from datetime import datetime
import pytz


moscow_tz = pytz.timezone('Europe/Moscow')
moscow_time = datetime.now(moscow_tz)

print()