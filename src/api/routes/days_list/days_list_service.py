from dataclasses import dataclass
import os


@dataclass
class Days_list_service:
    def handle_route(self):
        base_path = "data/daily/5min"
        yearsWithMonthsAndDays = []
        for year in sorted(os.listdir(base_path)):
            yearsWithMonthsAndDays.append({"value": year, "months": []})
            for month in sorted(os.listdir(base_path + "/" + year)):
                yearsWithMonthsAndDays[-1]["months"].append(
                    {"value": month, "days": []})
                for day in sorted(os.listdir(base_path + "/" + year + "/" + month)):
                    yearsWithMonthsAndDays[-1]["months"][-1]["days"].append(
                        {"value": day})
        return yearsWithMonthsAndDays
