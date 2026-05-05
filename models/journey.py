import math
import pytz
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Journey(BaseModel):
    operator: str
    origin: str
    destination: str
    departure: str
    arrival: str
    duration: str
    price: Optional[float]
    currency: str = "MAD"
    available_seats: Optional[int]
    amenities: list[str] = []
    brand: Optional[str] = None
    for_sale: bool = True
    status: str = "scheduled"

def get_current_minutes() -> int:
    # Gets the current time in Morocco and converts it to total minutes since midnight
    current_time = datetime.now(pytz.timezone("Africa/Casablanca"))
    return (current_time.hour * 60) + current_time.minute

def track_exact_schedule(schedule: list[dict]):
    current_minutes = get_current_minutes()
    
    # 1. Parse the schedule into minutes so we can easily compare them
    parsed_schedule = []
    for stop in schedule:
        time_parts = stop["time_str"].split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        parsed_schedule.append({
            "name": stop["name"], 
            "time_mins": (hour * 60) + minute
        })
        
    # Sort them just in case the JSON is out of order
    parsed_schedule.sort(key=lambda x: x["time_mins"])
    
    # 2. Check if the bus hasn't started or already finished
    if current_minutes < parsed_schedule[0]["time_mins"]:
        return {"status": "scheduled", "progress": 0, "passed": None, "next": parsed_schedule[0]["name"]}
        
    if current_minutes >= parsed_schedule[-1]["time_mins"]:
        return {"status": "arrived", "progress": 100, "passed": parsed_schedule[-1]["name"], "next": None}
        
    # 3. Find which two stops the bus is currently between
    for index in range(len(parsed_schedule) - 1):
        current_stop = parsed_schedule[index]
        next_stop = parsed_schedule[index + 1]
        
        # If the current time is between these two stops
        if current_stop["time_mins"] <= current_minutes < next_stop["time_mins"]:
            # Calculate how far along the bus is between just these two stops
            segment_duration = next_stop["time_mins"] - current_stop["time_mins"]
            elapsed_time = current_minutes - current_stop["time_mins"]
            progress_percentage = (elapsed_time / segment_duration) * 100
            
            return {
                "status": "running", 
                "progress": round(progress_percentage, 1), 
                "passed": current_stop["name"], 
                "next": next_stop["name"]
            }
            
    return {"status": "unknown"}

def track_estimated_schedule(departures: list[str], duration_min: int, stops: list[str]):
    current_minutes = get_current_minutes()
    
    # Convert all departure times to minutes
    departure_minutes = []
    for time_str in departures:
        time_parts = time_str.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        departure_minutes.append((hour * 60) + minute)
        
    departure_minutes.sort()
    
    # Find the bus that is currently running
    active_departure = None
    for dep_min in departure_minutes:
        if dep_min <= current_minutes and current_minutes < (dep_min + duration_min):
            active_departure = dep_min
            break
            
    if active_departure is None:
        if len(departure_minutes) > 0 and current_minutes < departure_minutes[0]:
            return {"status": "scheduled", "progress": 0, "passed": None, "next": stops[0] if stops else None}
        
        # If we missed all buses for the day
        return {"status": "no_active_bus", "progress": 100, "passed": stops[-1] if stops else None, "next": None}
        
    # Calculate overall progress of the route
    elapsed_minutes = current_minutes - active_departure
    progress_ratio = elapsed_minutes / duration_min
    
    # Map that progress to the stops array
    stop_index = progress_ratio * (len(stops) - 1)
    
    current_stop_index = math.floor(stop_index)
    next_stop_index = math.ceil(stop_index)
    
    current_stop = stops[current_stop_index]
    
    # Prevent out of bounds errors if the math gets weird near the end
    if next_stop_index < len(stops):
        next_stop = stops[next_stop_index]
    else:
        next_stop = stops[-1]
    
    return {
        "status": "running",
        "progress": round(progress_ratio * 100, 1),
        "passed": current_stop,
        "next": next_stop
    }