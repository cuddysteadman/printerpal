# imports for sensors and time
import board
import busio
from time import sleep
import datetime
import serial
from adafruit_pm25.uart import PM25_UART
import numpy as np
import Adafruit_MCP9808.MCP9808 as MCP9808
from time import strftime,localtime
# imports for flask web development
from flask import Flask, render_template, Response, jsonify
import plotly.graph_objects as go
# display package
import lcddriver

# setup app
app = Flask(__name__)
# temperature sensor initialisation
sensor = MCP9808.MCP9808()
sensor.begin()

# y temperature data
y_temp = []
 
# initialise and clear text
lcd = lcddriver.lcd()
lcd.lcd_clear()
lcd.lcd_display_string("Please wait.", 1)
lcd.lcd_display_string("Initialising...", 2)

# air quality sensor
uart = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=0.25)
pm25 = PM25_UART(uart, None)
# air quality data
y_air10 = []
y_air5 = []
y_air25 = []
y_air1 = []
y_air05 = []
y_air03 = []

@app.route("/c_to_f")
def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0

# x date data
x = []

# temperature data function called every 5 seconds
def update_temp():
    lcd.lcd_clear()
    
    # read and save temperature
    try:
        yi = sensor.readTempC()
    except RuntimeError:
        print("Unable to read from temperature sensor, retrying...")
        return
    
    y_temp.append(round(c_to_f(yi),1))
    
    # saves air quality data now so that we can display to text
    try:
        aqdata = pm25.read()
    except RuntimeError:
        print("Unable to read from air quality sensor, retrying...")
        return
    um100 = aqdata["particles 100um"]
    um50 = aqdata["particles 50um"]
    um25 = aqdata["particles 25um"]
    um10 = aqdata["particles 10um"]
    um05 = aqdata["particles 05um"]
    um03 = aqdata["particles 03um"]
    
    # um03 includes um05, um10, um25, um50, um100, etc. so we need to have um03 be just particles
    # from 0.3 to 0.5 rather than all particles greater than 0.3 
    y_air10.append(um100)
    y_air5.append(um50 - um100)
    y_air25.append(um25 - um50 - um100)
    y_air1.append(um10 - um25 - um50 - um100)
    y_air05.append(um05 - um10 - um25 - um50 - um100)
    y_air03.append(um03 - um05 - um10 - um25 - um50 - um100)
    
    # display info to screen
    lcd.lcd_display_string("Temp: {}".format(str(round(c_to_f(yi),1))), 1)
    lcd.lcd_display_string("0.3um: {}".format(str(um03 - um05 - um10 - um25 - um50 - um100)), 2)
    trace = go.Scatter(x = x, y = y_temp)
    
    fig = go.Figure()
    fig.add_trace(trace)
    
    fig.update_layout(
        title="Ambient Temperature",
        yaxis_title="Temperature (\u00B0F)",
        font=dict(
            family="sans serif",
            size=18,
            color="Black"
        )
    )
    return fig.to_dict()

def update_air():
    # adds current time
    local_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
    x.append(local_time)
    # all air quality data
    trace = go.Scatter(x = x, y = (y_air10), name="10um")
    trace1 = go.Scatter(x = x, y = (y_air5), name="5um")
    trace2 = go.Scatter(x = x, y = (y_air25), name="2.5um")
    trace3 = go.Scatter(x = x, y = (y_air1), name="1.0um")
    trace4 = go.Scatter(x = x, y = (y_air05), name="0.5um")
    trace5 = go.Scatter(x = x, y = (y_air03), name="0.3um")
    
    fig = go.Figure()
    fig.add_trace(trace)
    fig.add_trace(trace1)
    fig.add_trace(trace2)
    fig.add_trace(trace3)
    fig.add_trace(trace4)
    fig.add_trace(trace5)
    
    fig.update_layout(
        title="Approximate Air Quality",
        yaxis_title="Air Particles per 0.1L air",
        legend_title="Legend",
        font=dict(
            family="sans serif",
            size=18,
            color="Black"
        )
    )
    return fig.to_dict()

@app.route("/")
def air_quality():
    return render_template('index.html')

@app.route("/temp")
def temp_figure():
    return jsonify(update_temp())
@app.route("/air")
def air_figure():
    return jsonify(update_air())
    
if __name__ == '__main__':
    app.run(host='10.210.144.214', port='5000')