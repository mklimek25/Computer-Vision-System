import cv2
# import matplotlib.pyplot as plt
import numpy as np
import math
from rotated_rect_crop import crop_rotated_rectangle
import time
import tkinter
from statistics import mode
import sqlite3
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from tkinter import ttk

"""Attempting to fix the graphing function lost by the button addition"""
pt0_list = []
ab = sqlite3.connect("Hawkeye_Testing_Database_2.sqlite")
# FRAME BANKS SERVE AS A REFERENCE POINT OF ANALYSIS IN THE EVENT THAT A FRAME CANNOT BE FOUND
west_height_frame_bank = None
east_height_frame_bank = None
frame_reset_time = 5  # THIS IS THE AMOUNT OF TIME BETWEEN THE RESETTING OF FRAMES
west_height_list = []  # LIST USED TO TAKE AN AVERAGE OF ALL COLLECTED WEST HEIGHT VALUES TO DISPLAY TO THE GUI
west_holes_list = []  # LIST USED TO TAKE AN AVERAGE OF ALL COLLECTED WEST HOLE VALUES TO DISPLAY TO THE GUI
east_height_list = []  # LIST USED TO TAKE AN AVERAGE OF ALL COLLECTED EAST HEIGHT VALUES TO DISPLAY TO THE GUI
east_holes_list = []  # LIST USED TO TAKE AN AVERAGE OF ALL COLLECTED EAST HOLE VALUES TO DISPLAY TO THE GUI
time_set = []  # SET OF TIME VARIABLES COLLECTED FOR THE GUI GRAPHING UNIT
y_set_east = []  # SET OF EAST SIDE HEIGHT VARIABLES COLLECTED FOR THE GUI GRAPHING UNIT
y_set_west = []  # SET OF WEST SIDE HEIGHT VARIABLES COLLECTED FOR THE GUI GRAPHING UNIT
frame_error_set = []
sp_error_set = []
image_error_set = []
products = ["2.0-STANDARD WIDE", "NARROWS", "4.0-STANDARD WIDE", "2.5-STANDARD WIDE", "HT",
            "4.0-STANDARD WIDE", "6.0-STANDARD WIDE"]
s_c = 0  # USED TO IGNORE FIRST POINT COLLECTED
f_c = 0  # USED TO IGNORE FIRST POINT COLLECTED
button_hist = 0
frame_iteration = 0
fram_stop = 0
alarm = 0
start_time = 0
# SQL QUERY USED FOR COLLECTING DATA IN A STORED DATABASE, COMMAND TO CALL DATABASE SET BELOW
ab.execute("CREATE TABLE IF NOT EXISTS hawkeye_test (timestamp TIMESTAMP PRIMARY KEY, product STRING, date STRING,"
           " time STRING, west_height REAL, east_height REAL, west_hole_result STRING, east_hole_result STRING)")
def angled_point_to_original(x_coordinate, y_coordinate, x0, y0, width, height, angle):
    if angle < 0:
        angle = 360 + angle
    """This code takes the location of an angled analysis portion of an image and returns the coordinates of the
    original image.
    Error: all backwards.. going to redo the process and see if I can get better results."""
    y_coordinate = height - y_coordinate
    angle_in_radians = angle * math.pi / 180.0
    # a and b are variables found in our trig equation to find x and y origin points
    b = math.cos(angle_in_radians) * 0.5
    a = math.sin(angle_in_radians) * 0.5
    x_origin, y_origin = (int(x0 - a * height - b * width),
                          int(y0 + b * height - a * width))
    new_width = width - 2 * x_coordinate
    new_height = height - 2 * y_coordinate
    pta = (int(x0 - a * new_height - b * new_width),
           int(y0 + b * new_height - a * new_width))
    return pta

def trig_function_y_value(y, img):  # Trig is often used with CV, but the y-axis is flipped. Function counters problem
    output = img.shape[0] - y
    return output

def draw_angled_rec(x0, y0, width, height, angle, img):
    """draws a rectangle that is tilted at a defined angle"""
    _angle = angle * math.pi / 180.0
    b = math.cos(_angle) * 0.5
    a = math.sin(_angle) * 0.5
    pt0 = (int(x0 - a * height - b * width),
           int(y0 + b * height - a * width))
    pt0_list.append(pt0)
    pt1 = (int(x0 + a * height - b * width),
           int(y0 - b * height - a * width))
    pt2 = (int(2 * x0 - pt0[0]), int(2 * y0 - pt0[1]))
    pt0_list.append(pt2)
    pt3 = (int(2 * x0 - pt1[0]), int(2 * y0 - pt1[1]))
    cv2.line(img, pt0, pt1, (0, 0, 255), 3)
    cv2.line(img, pt1, pt2, (0, 0, 255), 3)
    cv2.line(img, pt2, pt3, (0, 0, 255), 3)
    cv2.line(img, pt3, pt0, (0, 0, 255), 3)
def finding_frame(image, side):  # WE MUST CHANGE THIS TO THE VIDEOCAPTURE OBJEC
    global start_time
    global f_c
    global west_height_frame_bank  # where the height frame is recorded from
    global east_height_frame_bank
    global frame_reset_time
    left_calibration_points = []
    right_calibration_points = []
    img2 = image
    elapsed = int(round(time.time() - start_time, 0))  # an elapsed time variable


    image_width = img2.shape[1]
    image_height = img2.shape[0]
    if side == "WEST":
        low_light = 240  # recording the requirements to pick up the shelve set points which reflect light
        height_frame_bank = west_height_frame_bank
    else:
        low_light = 240
        # frame_set = frame_set_east
        height_frame_bank = east_height_frame_bank
    if elapsed == frame_reset_time or height_frame_bank == None or f_c == 1:
        lower_range = np.array([low_light, low_light, low_light])
        upper_range = np.array([255,255, 255])  # brightness serves as an indicator


        # MASK SEPERATES VLUES IN A COLOR RANGE FROM THE REST, USED TO FIND OUR CORNERS AS CONTOURS
        mask = cv2.inRange(img2, lower_range, upper_range)  # finding our indicators
        # cv2.imshow("{}_mask".format(side), mask)
        a = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]  # ^
        for contour in a:
            area = cv2.contourArea(contour)
            if area > 1000:
                m = cv2.moments(contour)
                cX = int(m["m10"] / m["m00"])
                cY = int(m["m01"] / m["m00"])  # The above code searches for middle values to indicate

                if cX > image_width/2:  # finding the indication point on each side of the screen
                    right_calibration_points.append((cX, cY))

                if cX < image_width/2:
                    left_calibration_points.append((cX, cY))
                cv2.circle(img2, (cX, cY), 7, (255, 0, 0), -1)
        """TIME FOR MATH:
        need to calculate the new angled rectangles based on the sections/sticker calculations.
        Finding the angle between the two top lines (adjusted y value for trig calcs)"""
        left_calibration_points.sort(key = lambda x: x[1] + x[0], reverse=True)  # finding the leftmost and rightmost corners
        right_calibration_points.sort(key = lambda x: x[1] - x[0], reverse=True)
        if len(left_calibration_points) < 1 or len(right_calibration_points) < 1:  # not applicable if there are no indication points
            print(side)
            print("ERROR - Location Points Not Detected")
            return None, "Location Points Not Detected"


        point_1 = (left_calibration_points[0][0], trig_function_y_value(left_calibration_points[0][1], img2))  # First Point
        point_2 = (right_calibration_points[len(right_calibration_points)-1][0],
                   trig_function_y_value(right_calibration_points[len(right_calibration_points)-1][1], img2))  # second point

        x_diff = (point_2[0] - point_1[0])
        y_diff = (point_2[1] - point_1[1])  # self explanitory
        angle = math.atan(y_diff/x_diff) #prints out in radians
        slope = y_diff/x_diff
        """GATHERING CORNERS BELOW"""
        if side == "WEST":

            corner1 = right_calibration_points[len(right_calibration_points)-1]

            corner2_y_trig = (trig_function_y_value(corner1[1], img2) - slope * corner1[0])  # b=y-mx
            second_point_y = img2.shape[0] - int(corner2_y_trig)
            corner2 = (0, second_point_y)
            vertical_angle = angle + 3 * math.pi/2
            vertical_slope = math.tan(vertical_angle)
            corner3 = (int(-1 * corner2_y_trig / vertical_slope), int(image_height - 50))  #if y=0, x= -b/m
        else:
            corner1 = left_calibration_points[0]
            corner2_y_trig = (trig_function_y_value(corner1[1], img2) - slope * corner1[0])  # b=y-mx
            second_point_y = int(trig_function_y_value(slope * img2.shape[1] + corner2_y_trig, img2))
            corner2 = (img2.shape[1], second_point_y)
            vertical_angle = angle + 3 * math.pi/2
            vertical_slope = math.tan(vertical_angle)
            corner3 = (image_width + int(-1 * second_point_y / vertical_slope), int(image_height - 50))  #if y=0, x= -b/m
        frame_width = ((corner1[0]-corner2[0])**2 + (corner1[1]-corner2[1])**2)**0.5
        frame_height = ((corner3[0]-corner2[0])**2 + (corner3[1]-corner2[1])**2)**0.5
        xmid_frame = (corner1[0] + corner3[0])/2
        ymid_frame = (corner1[1] + corner3[1])/2
        new_angle = 360 - angle * 180/math.pi
        """LOOKING FOR 4 CORNERS OF ANGLED FRAME"""

        if side == "WEST":
            print("west frame")
            west_height_frame_bank = ((int(xmid_frame), int(ymid_frame)), (int(frame_width-50), int(frame_height)), int(new_angle))

        else:
            print("east frame")
            east_height_frame_bank = ((int(xmid_frame), int(ymid_frame)), (int(frame_width-75), int(frame_height)), int(new_angle))
            print("done")
        print("We have worked")
        f_c += 1
        if f_c > 1:
            f_c = 0
            start_time = time.time()

    """COLLECT THE HEIGHT FRAME BELOW"""

    if side == "WEST":
        height_frame = crop_rotated_rectangle(img2, west_height_frame_bank)
    else:
        height_frame = crop_rotated_rectangle(img2, east_height_frame_bank)
    return height_frame, None

class mainWindow(tkinter.Tk):  # CLASS USED TO DEFINE THE GUI USED BY OPERATORS
    """Will be the object that will perform as it is called"""
    def __init__(self):
        global x_set
        super().__init__()
        # configure the root window
        self.title = tkinter.Label(self, text="Project Demo", borderwidth=2, relief='solid', font=('Arial', 40), background='tan')
        self.geometry('800x750')
        self.resizable(0, 0)
        self.configure(background='tan')
        # Labels Generated Below
        self.east_side_label = tkinter.Label(self, text="EAST SIDE", borderwidth=2, relief='solid', font=('Arial', 25), background='tan')
        self.west_side_label = tkinter.Label(self, text="WEST SIDE", borderwidth=2, relief='solid', font=('Arial', 25), background='tan')
        self.suggestions_title = tkinter.Label(self, text="Suggestions", borderwidth=2, relief='solid', font=('Arial', 25), background='tan')
        self.west_height_label = tkinter.Label(self, text="Waiting...", borderwidth=2, relief='solid', font=('Arial', 25), background='tan')
        self.east_height_label = tkinter.Label(self, text="Waiting...", borderwidth=2, relief='solid', font=('Arial', 25), background='tan')
        self.west_holes_label = tkinter.Label(self, text="Waiting...", borderwidth=2, relief='solid', font=('Arial', 25), background='tan')
        self.east_holes_label = tkinter.Label(self, text="Waiting...", borderwidth=2, relief='solid', font=('Arial', 25), background='tan')
        self.suggestions_label = tkinter.Label(self, text="Enjoy the\ndemo", borderwidth=2, relief='solid', font=('Arial', 25), background='tan')
        self.product_type = tkinter.StringVar()  # Product type chose in dropdown menu
        """Error Values Below"""
        self.image_read_error = tkinter.BooleanVar()
        self.sidepaper_error = tkinter.BooleanVar()
        self.frame_error = tkinter.BooleanVar()
        self.height_read_errpr = tkinter.BooleanVar()
        """Height Values Below"""
        self.west_side_height = tkinter.DoubleVar()
        self.east_side_height = tkinter.DoubleVar()
        """Holes Results Below"""
        self.west_holes = tkinter.BooleanVar()
        self.east_holes = tkinter.BooleanVar()
        """Record Values is a variable that will determine whether the program shall record values, read frame determines
        whether the frame will ve read at all"""
        self.read_frame = tkinter.BooleanVar()
        self.read_frame.set(False)
        self.record_values = tkinter.BooleanVar()
        self.record_values.set(True)
        self.product_selection = ttk.Combobox(textvariable=self.product_type)
        self.product_selection['values'] = products

        """The Start Button controls the function"""
        self.start_button = tkinter.Button(self, text="Start", command=self.camera_read)


        # Grid System
        self.columnconfigure(0, weight=10)  # Weights only really affect spacing
        self.columnconfigure(1, weight=10)  # Weights are preference based
        self.columnconfigure(2, weight=10)
        self.rowconfigure(0, weight=10)
        self.rowconfigure(1, weight=10)
        self.rowconfigure(2, weight=10)
        self.rowconfigure(3, weight=10)
        self.rowconfigure(4, weight=10)
        self.rowconfigure(5, weight=10)
        self.rowconfigure(5, weight=10)
        self.rowconfigure(6, weight=10)
        self.title.grid(row=0, column=0, columnspan=2, sticky='nsew')  # Label Location, grid
        self.east_side_label.grid(row=1, column=1, sticky='nsew')
        self.west_side_label.grid(row=1, column=0, sticky='nsew')
        self.east_height_label.grid(row=2, column=1, sticky='nsew')  # placement of label
        self.west_height_label.grid(row=2, column=0, sticky='nsew')
        self.east_holes_label.grid(row=3, column=1, sticky='nsew')
        self.west_holes_label.grid(row=3, column=0, sticky='nsew')
        self.suggestions_title.grid(row=4, column=0, columnspan=2, sticky='nsew')
        self.suggestions_label.grid(row=5, column=0, columnspan=2, sticky='nsew')
        self.start_button.grid(row=6, column=0, columnspan=3, sticky='nsew')
        fig = Figure(figsize=(5, 5))
        self.plot1 = fig.add_subplot(111)
        self.plot1.scatter(x=time_set, y=y_set_east, color='red', label='EAST SIDE HEIGHTS')
        self.plot1.scatter(x=time_set, y=y_set_west, color='blue', label='WEST SIDE HEIGHTS')
        self.plot1.legend(loc='best')
        self.canvas = FigureCanvasTkAgg(fig,master=self)
        self.canvas.get_tk_widget().grid(row=1, column=2, rowspan=5, sticky='nsew')
        self.product_selection.grid(row=0, column=2, sticky='nsew')
        self.frame_west = None
        self.frame_east = None
        self.west_height_list = []
        self.east_height_list = []
        self.west_holes_list = []
        self.east_holes_list = []
        self.sidepaper_error_list = []
        self.recent_reading = None
        # self.camera_read()
        # action
    def start_read(self):
        print("THIS IS HAPPENING")
        if self.product_type.get() != "":
            self.read_frame.set(True)
            self.after(5000, self.timed_change)
        elif self.image_read_error.get() == True:  # This may not do jack shit :)
            self.record_values.set(False)
            self.error_function()
    def camera_read(self):
        global fram_stop
        print("HELLO")
        """We are reading the two Cameras at this point. This function needs to change. It needs to change in a way
        where the button starts the reading of the frames."""
        """The frames will be captured and presented, but the analysis will not take place until button is pressed"""
        self.set_product()

        file_name_west = '4-5_west_side1 copy.mp4'
        file_name_east = '4-5_east_side1 copy.mp4'
        cap = cv2.VideoCapture(file_name_west)
        cap1 = cv2.VideoCapture(file_name_east)
        self.after(5000, self.timed_change)  # CALLING ON THE FUNCTION THAT COLLECTS DATA FROM THE CV APPLICATION
        while cap.isOpened():
            self.record_values.set(True)
            self.read_frame.set(True)
            if self.record_values.get() is False or self.read_frame.get() is False:
                if self.image_read_error.get() is True and self.sidepaper_error.get() is False and \
                        self.height_read_errpr is False and self.frame_error is False:
                    self.record_values.set(True)  # We need to reset the record values and the image read post error if everything is alright
            ret, frame = cap.read()
            ret1, frame1 = cap1.read()
            self.frame_west = frame
            self.frame_east = frame1
            if frame is None or frame1 is None:
                self.image_read_error.set(True)
                self.record_values.set(False)
                self.read_frame.set(False)
                self.error_function()
            elif self.read_frame.get() == True:
                if fram_stop == 0:
                    cv2.destroyAllWindows()
                    fram_stop += 1
            self.process("WEST")
            self.process("EAST")
            # else:
            #     cv2.imshow("west_frame_unread", frame)
            #     cv2.imshow("east_frame_unread", frame1)
            #     fram_stop = 0



            frametime=50
            if cv2.waitKey(frametime) & 0xFF == ord('q'):
                break
            self.update()

        cap.release()
        cap1.release()
    def set_product(self):
        self.product_type.set(self.product_selection.get())
    def error_function(self):
        error_list = []
        if self.sidepaper_error.get() is True:
            error_list.append("SIDEPAPER INTERFERENCE DETECTED")
        if self.height_read_errpr.get() is True:
            error_list.append("FOAM IS NOT BEING READ PROPERLY")
        if self.frame_error.get() is True:
            error_list.append("FRAME IS NOT BEING READ PROPERLY")
        if self.image_read_error is True:
            error_list.append("IMAGE NOT BEING READ, CHECK CAMERAS")
        error_message = "\n".join(error_list)

        self.configure(background='red')
        self.east_holes_label.configure(background='red', foreground='white')
        self.west_holes_label.configure(background='red', foreground='white')
        self.east_height_label.configure(background='red', foreground='white')
        self.west_height_label.configure(background='red', foreground='white')
        self.suggestions_title.configure(background='red', foreground='white')
        self.west_side_label.configure(background='red', foreground='white')
        self.east_side_label.configure(background='red', foreground='white')
        self.title.configure(background='red', foreground='white')
        self.suggestions_label.configure(text='{}'.format(error_message), background='red', foreground='white')
    def suggestion(self):

        """Lets talk about what suggestions we can give:
        1. Heights too high
        2. Heights too low
        3. Heights uneven
        4. Sideholes messed up
        5. Error Messages  """
    def timed_change(self):
        """Shift every 5 seconds"""
        global x_set
        global y_set_east
        global y_set_west
        global time_set

        # VALUES BELOW MAINLY USED FOR SQL DATA STORAGE
        now = datetime.now()
        timestamp = now.timestamp()
        date = now.strftime('%m:%d:%Y')
        time = now.strftime('%H:%M:%S')
        product = self.product_type.get()
        if product == "2.0-STANDARD WIDE" or product == "2.5-STANDARD WIDE" or product == "HT":
            max_height = 26.5
            min_height = 25.0
        elif product == "NARROWS":
            max_height = 28.5
            min_height = 27.0
        elif product == "4.0-STANDARD WIDE":
            max_height = 18.5
            min_height = 17.0
        else:
            max_height = 13.5
            min_height = 12.0

        # OFFICIAL RESULTS SHOWN ON THE GUI ARE GATHERED BELOW. HEIGHTS ARE RECORDED BY AVERAGES WHILE HOLES ARE
        # DETERMINED BY MOST COMMON OUTPUT IN A LIST OF RECENTLY COLLECTED DATA
        if self.record_values.get() != False:
            west_height_result = sum(self.west_height_list)/len(self.west_height_list)
            west_hole_result = mode(self.west_holes_list)
            east_height_result = sum(self.east_height_list)/len(self.east_height_list)
            east_hole_result = mode(self.east_holes_list)

            if west_height_result is None:
                west_height = "Waiting for foam image"
            else:
                west_height = round(west_height_result, 2)
            if west_hole_result is None:
                west_holes = "Waiting for foam image"
            else:
                west_holes = west_hole_result
            if east_height_list is None:
                east_height = "Waiting for foam image"
            else:
                east_height = round(east_height_result, 2)
            if east_holes_list is None:
                east_holes = "Waiting for foam image"
            else:
                east_holes = east_hole_result

            west_height_label = "West Height:\n{}".format(west_height)
            if west_height > min_height and west_height < max_height:
                # print("WE DID THIS")
                self.west_height_label.configure(text=west_height_label, background='green', foreground='black')
            else:
                self.west_height_label.configure(text=west_height_label, background='red', foreground='white')

            east_height_label = "East Height:\n{}".format(east_height)

            if east_height > min_height and east_height < max_height:
                # print("WE DID THIS")
                self.east_height_label.configure(text=east_height_label, background='green', foreground='black')
            else:
                self.east_height_label.configure(text=east_height_label, background='red', foreground='white')

            west_holes_label = "West Holes:\n{}".format(west_holes)
            if west_holes == False:
                self.west_holes_label.configure(text=west_holes_label, background='green', foreground='black')
            else:
                self.west_holes_label.configure(text=west_holes_label, background='red', foreground='white')

            east_holes_label = "East Holes:\n{}".format(east_holes)
            if east_holes == False:
                self.east_holes_label.configure(text=east_holes_label, background='green', foreground='black')
            else:
                self.east_holes_label.configure(text=east_holes_label, background='red', foreground='white')
            suggestion = "welcome back"
            self.suggestions_label.configure(text=suggestion)
            # ab.execute("INSERT INTO hawkeye_test (timestamp, product, date, time, west_height, east_height, west_hole_result"
            #            ", east_hole_result) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (timestamp, product, date, time, west_height,
            #                                                                    east_height, west_hole_result, east_hole_result))
            if len(time_set) < 20:
                y_set_east.append(east_height)
                y_set_west.append(west_height)
                time_set.append(now)  # TRYING THIS
            else:
                del y_set_east[0]
                y_set_east.append(east_height)
                del y_set_west[0]
                y_set_west.append(west_height)
                del time_set[0]
                time_set.append(now)
            print(self.record_values.get())

            self.update()
        self.after(5000, self.timed_change)
    def process(self, side):
        global frame_iteration
        global start_time

        """Contaains the motion of the camera_work. Should be helpful for understanding process flow"""
        if frame_iteration < 2:
            if side == "WEST":
                height_frame = finding_frame(self.frame_west, side)[0]
            else:
                height_frame = finding_frame(self.frame_east, side)[0]
        elif self.frame_west is None or self.frame_east is None:
            self.image_read_error.set(True)
            return None

        else:
            if side == "WEST":
                height_frame = crop_rotated_rectangle(self.frame_west, west_height_frame_bank)
            else:
                height_frame = crop_rotated_rectangle(self.frame_east, east_height_frame_bank)
        if height_frame is None:
            self.frame_error.set(True)
            self.error_function()
            self.record_values.set(False)
            self.read_frame.set(False)
            return None


        if self.record_values.get() == True:
            results = self.extreme_points(height_frame, side)  # Go to extreme_points at the top
            if len(sp_error_set) > 0 and mode(sp_error_set) is not None:
                self.sidepaper_error.set(True)
                self.error_function()
                self.record_values.set(False)
            else:

                self.sidepaper_error.set(False)  # must undo the error function after problem is resolved
        else:
            return None
        if results is not None:
            if results[0] is not None:
                if side == "WEST":

                    if len(self.west_height_list) < 25:
                        print("fuck off")
                        print(results)
                        self.west_height_list.append(results[0])

                    elif abs(results[0] - sum(self.west_height_list)/len(self.west_height_list)) > 5 and self.recent_reading is not None:
                        return None
                    else:
                        del self.west_height_list[0]
                        self.west_height_list.append(results[0])
                    if len(self.west_holes_list) < 10:
                        self.west_holes_list.append(results[1])
                    else:
                        del self.west_holes_list[0]
                        self.west_holes_list.append(results[1])

                if side == "EAST":
                    if len(self.east_height_list) < 25:
                        self.east_height_list.append(results[0])
                    elif abs(results[0] - sum(self.east_height_list)/len(self.east_height_list)) > 5 and self.recent_reading is not None:
                        return None
                    else:
                        del self.east_height_list[0]
                        self.east_height_list.append(results[0])
                    if len(self.east_holes_list) < 10:
                        self.east_holes_list.append(results[1])
                    else:
                        del self.east_holes_list[0]
                        self.east_holes_list.append(results[1])
                # print(west_height_list)



                frame_iteration += 1
    def extreme_points(self, img, side):
        """This function collects frames and results given an input frame to read. Resets timers on a 5 second basis"""
        global s_c  # side_count
        global start_time

        global frame_reset_time
        elapsed = int(round(time.time() - start_time, 0))  # an elapsed time variable
        sidehole_box_size = 10
        sidehole_rectangle_width = 400
        sidehole_rectangle_height = 200
        hole_count = 0  # probably used to set a first loop in order
        gray_img_base = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # converting image to grayscale
        image_bottom_left_section = gray_img_base[gray_img_base.shape[0] - 500:gray_img_base.shape[0], 0:900]  # may want to move these in the future for efficiency (this line and the one below)
        image_bottom_right_section = gray_img_base[gray_img_base.shape[0] - 300:gray_img_base.shape[0], gray_img_base.shape[1] - 300:gray_img_base.shape[1]]
        rect_adj = 5
        if side == "WEST":
            average = image_bottom_left_section.mean(axis=0).mean(axis=0)
            cut_point = 120  # Cut away for reading purposes
            thresh_assist = 15  # adjustment variable to read the heights through a generated mask using parameter
            thresh_assist_height = -45
            gray_img = gray_img_base[0:gray_img_base.shape[0], 0:gray_img_base.shape[1] - cut_point]
            gray_img_height = gray_img[0:gray_img.shape[0], gray_img.shape[1]-100: gray_img.shape[1]]
            indicator_height = 40
            height_pixel_converter = .0616  # Based on calibration efforts
            height_adjustment_parameter = 0.25  # 0.30



        else:
            average = image_bottom_right_section.mean(axis=0).mean(axis=0)
            cut_point = 135
            thresh_assist = 15
            thresh_assist_height = -20
            gray_img = gray_img_base[0:gray_img_base.shape[0], cut_point:gray_img_base.shape[1]]  # cutting off the conveyor point and side paper foam
            gray_img_height = gray_img[0:gray_img.shape[0], 0:100]
            indicator_height = 40.25
            height_pixel_converter = .0573  # Based on calibration efforts
            height_adjustment_parameter = 1.0  # -.4


        thresh_point = average-thresh_assist  # Using adjustment variable
        thresh_point_height = average-thresh_assist_height
        ret, mask = cv2.threshold(gray_img, thresh_point, 255, cv2.THRESH_BINARY)  # creating mask
        """Below two lines are used in processing to 'smoothen out' an image"""
        reth, maskh = cv2.threshold(gray_img_height, thresh_point_height, 255, cv2.THRESH_BINARY)
        # cv2.imshow("{}_side_heightcut".format(side), maskh)

        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=1)
        contours = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]  # reading the foam as a contour
        contours_h = cv2.findContours(maskh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]  # reading the foam as a contour
        # cv2.imshow("{}-MASK".format(side), mask)
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)  # getting the largest contour (the foam)
        sorted_contours_h = sorted(contours_h, key=cv2.contourArea, reverse=True)  # getting the largest contour (the foam)
        try:
            c = sorted_contours[0]
            ch = sorted_contours_h[0]
        except IndexError:
            self.height_read_errpr.set(True)
            self.record_values.set(False)
            return None
        if self.height_read_errpr.get() is False:  # If the frame is reading and the error is on, we will turn the error off
            self.height_read_errpr.set(True)
        cont_list = []
        cont_list_h = []
        paper_watch_list = []  # keeping an eye on the foam corner looking for the prescence of side paper
        """After identifying the foam contour we must read the corner of interest (done below)
        to find the point to measure our heights"""
        for cont in c:
            cont_list.append((cont[0][0], cont[0][1]))


        for cont in ch:
            cont_list_h.append((cont[0][0], cont[0][1]))
        if side == "WEST":
            cont_list.sort(key=lambda x: x[0] - x[1], reverse=True)
            # print(cont_list[0][1])
            if cont_list[0][1] < 140:
                self.sidepaper_error.set(True)
                self.record_values.set(False)
                return None, None
            cont_list_h.sort(key=lambda x: x[0] - x[1], reverse=True)
            cv2.line(img, (cont_list_h[0][0] + gray_img.shape[1] - 100, cont_list_h[0][1]), (cont_list_h[0][0] + gray_img.shape[1]-100, 0), (0, 255, 0), 3)
            top = indicator_height - cont_list_h[0][1] * height_pixel_converter + height_adjustment_parameter
            cont_list.sort(key=lambda x: x[0] + x[1], reverse=False)
            # cv2.line(img, (cont_list[0][0] + cut_point, cont_list[0][1]), (cont_list[0][0] + cut_point, 0), (0, 255, 0), 3)
            cv2.rectangle(img, (cont_list[0][0] + cut_point - rect_adj, cont_list[0][1] + 75 - rect_adj),
                          (cont_list[0][0] + sidehole_rectangle_width + cut_point + rect_adj,
                           cont_list[0][1] + 75 + sidehole_rectangle_height + rect_adj), (255, 0, 0), 3)


        else:
            cont_list_h.sort(key=lambda x: x[0] + x[1], reverse=False)
            cv2.line(img, (cont_list_h[0][0] + cut_point, cont_list_h[0][1]), (cont_list_h[0][0] + cut_point, 0), (0, 255, 0), 3)
            top = 40 - cont_list_h[0][1] * height_pixel_converter + height_adjustment_parameter - 1.5
            cont_list.sort(key=lambda x: x[0] - x[1], reverse=True)
            # cv2.line(img, (cont_list[0][0], cont_list[0][1]), (cont_list[0][0], 0), (0, 255, 0), 3)
            cv2.rectangle(img, (cont_list[0][0] - sidehole_rectangle_width - rect_adj, cont_list[0][1] + 50 - rect_adj),
                          (cont_list[0][0] + rect_adj, cont_list[0][1] + 50 + sidehole_rectangle_height + rect_adj), (255, 0, 0), 3)



        # Finding the height using this equation. Height estimate is 40.5 at the markings


        """NEED A HOLE ANALYSIS FRAME FROM THIS"""
        if elapsed == frame_reset_time or s_c == 1:
            s_c += 1
            if s_c > 1:
                s_c = 0
                start_time = time.time()

        if side == "WEST""":
            sidehole_crop = img[(cont_list[0][1] + 75):(cont_list[0][1] + 75 + sidehole_rectangle_height), (cont_list[0][0] + cut_point):(cont_list[0][0] + sidehole_rectangle_width + cut_point)]
            y_start = cont_list[0][1] + 75
            x_start = cont_list[0][0] + cut_point
            hole_dif_marker =45

        else:
            sidehole_crop = img[(cont_list[0][1] + 50):(cont_list[0][1] + 50 + sidehole_rectangle_height),
                            (cont_list[0][0] - sidehole_rectangle_width): (cont_list[0][0])]
            y_start = cont_list[0][1] + 50
            x_start = cont_list[0][0] - sidehole_rectangle_width
            hole_dif_marker = 45


        sidehole_crop = cv2.cvtColor(sidehole_crop, cv2.COLOR_BGR2GRAY)
        # cv2.imshow("SIDEHOLE_CROP_{}".format(side), sidehole_crop)




        if sidehole_crop is not None:
            sc_bottom = sidehole_crop[int(sidehole_crop.shape[0]/2):sidehole_crop.shape[0], 0:sidehole_crop.shape[1]]
            hole_thresh = sc_bottom.mean()-hole_dif_marker
            ret, sidehole_thresh = cv2.threshold(sidehole_crop, hole_thresh, 255, cv2.THRESH_BINARY)

            side_holes, heiarchy = cv2.findContours(sidehole_thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for side_hole in side_holes[0:len(side_holes)-1]:
                if cv2.contourArea(side_hole) >= 200:
                    s = cv2.moments(side_hole)
                    sX = int(s["m10"] / s["m00"])
                    sY = int(s["m01"] / s["m00"])  # The above code searches for middle values to indicate
                    hole_x = x_start + sX
                    hole_y = y_start + sY

                    if side == "WEST":
                        cv2.rectangle(img=img, pt1=(hole_x-sidehole_box_size,hole_y-sidehole_box_size), pt2=(hole_x+sidehole_box_size,hole_y+sidehole_box_size),
                                      color=(255, 0, 0), thickness=3)
                    else:
                        cv2.rectangle(img=img, pt1=(hole_x-sidehole_box_size,hole_y-sidehole_box_size),
                                      pt2=(hole_x+sidehole_box_size,hole_y+sidehole_box_size),
                                      color=(255, 0, 0), thickness=3)

                    hole_count += 1
                else:
                    pass
            if hole_count == 0:
                hole_result = False
            else:
                hole_result = True
            if side == "EAST":
                img = img[115:, :]
            else:
                img = img[140:,:]

            # print(img.shape)

            cv2.imshow(side, img)
            # cv2.imshow("sdhls_{}".format(side), sidehole_thresh)
            return top, hole_result
        else:
            cv2.imshow(side, img)

            return None, None










root = mainWindow()
elapsed = 0
ab.commit()
ab.close()
root.mainloop()

cv2.destroyAllWindows()
