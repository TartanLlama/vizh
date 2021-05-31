import cv2
import numpy as np
from vizh.ir import *
import vizh.ocr
from enum import Enum, auto
import sys
from collections import namedtuple
import itertools

def crop_by_bounding_box(image, box):
    x,y,w,h = box
    return image[y:y+h,x:x+w]

InstructionData = namedtuple('InstructionData', 'bounding_box instruction')

def write_text(img, text, x, y): 
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0) )

def recognise_instruction_lines(instructions):
    # Sort the instructions by the lowest point in their symbol's bounding box
    instructions.sort(key=lambda i: i.bounding_box[1] + i.bounding_box[3])

    # Split instructions up into lines
    lines = []
    current_line = [instructions[0]]
    for i1, i2 in zip(instructions, instructions[1:]):
        if i2.bounding_box[1] > i1.bounding_box[1] + i1.bounding_box[3]:
            lines.append(current_line)
            current_line = []
        current_line.append(i2)
    lines.append(current_line)

    # Sort the lines horizontally
    for line in lines:
        line.sort(key=lambda i: i.bounding_box[0])

    return lines

def decorate_and_show_image(img, lines, y_offset):
    for line in lines:
        # We're going to draw a box around the line, so find the min y and max x for the line
        min_y = min(line, key=lambda i: i.bounding_box[1]).bounding_box[1]
        max_y = line[-1].bounding_box[1] + line[-1].bounding_box[3]

        # Calculate top left and bottom right points for the box, adding some padding
        buffer_space = 15
        top_left = (line[0].bounding_box[0]-buffer_space, min_y+y_offset-buffer_space)
        bottom_right = (line[-1].bounding_box[0] + line[-1].bounding_box[2] + buffer_space, max_y+y_offset + buffer_space)

        # Draw the box around the line and decorate every instruction with its name
        cv2.rectangle(img, top_left, bottom_right, (250,0,0), 3)
        for bounding_box, instruction in line:
            write_text(img, str(instruction), bounding_box[0], min_y+y_offset)

    cv2.imshow('Debug', img)
    cv2.waitKey(0)

class Parser(object):
    def __init__(self):
        self.ocr = vizh.ocr.TesseractOCR()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.ocr.__exit__(exception_type, exception_value, exception_traceback)

    def parse_function_signature(self, img, threshold):
        # We want to find largeish rectangles of text
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))
    
        # Dilate the image so that characters in the token aren't separated
        dilation = cv2.dilate(threshold, rect_kernel, iterations = 1)

        # Finding contours
        text_contours, text_hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, 
                                                         cv2.CHAIN_APPROX_NONE)

        # Sort to find the two contours closest to the top of the image
        y_sorter = lambda c: cv2.boundingRect(c)[1]
        text_contours.sort(reverse=False, key=y_sorter)

        # Sort by x to have the first element be the function name and the second be the number of args
        x_sorter = lambda c: cv2.boundingRect(c)[0]
        signature = sorted(text_contours[:2], key=x_sorter)

        # OCR the function name
        func_rect = cv2.boundingRect(signature[0])
        function_name = self.ocr.ocr(crop_by_bounding_box(img,func_rect)).strip()

        # OCR the number of arguments
        arg_rect = cv2.boundingRect(signature[1])
        n_args = self.ocr.ocr(crop_by_bounding_box(img,arg_rect)).strip()

        return ((function_name, func_rect), (int(n_args), arg_rect))

    def parse_contours(self, img, shape_contours):
        instructions = []
        errors = []
        for contour in shape_contours:
            approx = cv2.approxPolyDP(contour, 0.01* cv2.arcLength(contour, True), True)
            points = [point.ravel() for point in approx]
            bounding_rect = cv2.boundingRect(contour)
            try:
                instruction = self.parse_polygon(img, contour, points)
                if instruction:
                    instructions.append(InstructionData(bounding_rect, instruction))
            except ParseError as err:
                errors.append(ParseError(str(err), contour))

        return instructions, errors

    def parse_polygon(self, img, contour, polygon):
        # Triangle: either read or write
        if len(polygon) == 3:
            direction = detect_direction(polygon, slope_angle=30)
            if direction == ArrowDirection.UP:
                return Instruction(InstructionType.READ)
            if direction == ArrowDirection.DOWN:
                return Instruction(InstructionType.WRITE)
            raise ParseError("Found a triangle, but not sure what direction it's pointing")

        # Minus sign: decrement
        elif len(polygon) == 4:
            symbol = crop_by_bounding_box(img, cv2.boundingRect(contour))
            internal_contours, _ = cv2.findContours(symbol, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            # If there are more than 2 contours then this is a comment: ignore it
            if len(internal_contours) > 2:
                return None
            else:
                return Instruction(InstructionType.DEC)

        # Brace: either loop start or end
        elif len(polygon) == 6:
            # Check all pairs of adjacent points
            lines = zip(polygon, rotate(polygon,1))
            longest_vertical_line = max(lines, key=lambda p: abs(p[1][1] - p[0][1]))
            leftmost_point = min(polygon, key=lambda p: p[0])

            if min(longest_vertical_line[0][0], longest_vertical_line[1][0]) > leftmost_point[0]:
                return Instruction(InstructionType.LOOP_END)
            else:    
                return Instruction(InstructionType.LOOP_START)

        # Arrow: either up, down, left, or right
        elif len(polygon) == 7:
            direction = detect_direction(polygon, slope_angle=45)
            if direction == ArrowDirection.UNKNOWN:
                raise ParseError("Found an arrow, but not sure what direction it's pointing")
            return Instruction(direction.instruction_type())

        # Plus: increment
        elif len(polygon) == 8:
            return Instruction(InstructionType.INC)

        # Probably a circle, look for a function call
        elif len(polygon) > 10:
            # Draw over the circle to remove it before OCRing
            cv2.drawContours(img, [contour], 0, (0,0,0), 10)
            function_image = crop_by_bounding_box(img, cv2.boundingRect(contour))
            function_name = self.ocr.ocr(function_image).strip()
            
            if function_name == '':
                raise ParseError("Found a circle, but couldn't parse a function name inside it")
            return Instruction(InstructionType.CALL, function_name)

        raise ParseError("Didn't recognise the instruction")

    def parse(self, img_file, debug=False):
        img = cv2.imread(img_file)

        # Convert the image to grayscale
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        # Binarise the image
        ret, threshold = cv2.threshold(gray, 240 , 255, cv2.CHAIN_APPROX_NONE)

        (function_name, function_name_box), (n_args, argument_box) = self.parse_function_signature(img, threshold) 
        bottom_of_signature_area = max(function_name_box[1] + function_name_box[3], argument_box[1] + argument_box[3])

        # Crop the image from the bottom of the signature area to get the statements area
        statements = threshold[bottom_of_signature_area:, :]
        
        # Find all shapes in the statements area
        shape_contours, _ = cv2.findContours(statements, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        instructions, errors = self.parse_contours(statements, shape_contours)
        lines = recognise_instruction_lines(instructions)
            
        if len(errors) > 0:
            print(f"Error parsing {img_file} (see image for details)", file=sys.stdout)
            # Draw rectangles around all the bad tokens
            for err in errors:
                box = cv2.boundingRect(err.contour)
                top_left = (box[0], box[1]+bottom_of_signature_area)
                bottom_right = (box[0]+box[2], box[1]+box[3]+bottom_of_signature_area)
                cv2.rectangle(img, top_left, bottom_right, (0,0,255), 3)
                write_text(img, str(err), box[0], box[1] + bottom_of_signature_area - 20)
            cv2.imshow('Debug', img)
            cv2.waitKey(0)

        if debug:
            write_text(img, 'Function name: ' + function_name, function_name_box[0]+4, function_name_box[1]+function_name_box[3]+20)
            write_text(img, 'Arguments: ' + str(n_args), argument_box[0]-100,argument_box[1]+argument_box[3]+20)
            decorate_and_show_image(img, lines, bottom_of_signature_area)

        cv2.destroyAllWindows()

        if len(errors) > 0:
            return None

        final_instructions = [data.instruction 
        for line in lines 
        for data in line]
        return Function(FunctionSignature(function_name, n_args), final_instructions)

class ParseError(Exception):
    def __init__(self, err, contour=None):
        super().__init__(err)
        self.contour = contour

class ArrowDirection(Enum):
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    UNKNOWN = auto()

    def instruction_type(self):
        if self.value == self.LEFT.value:
            return InstructionType.LEFT  
        if self.value == self.RIGHT.value:
            return InstructionType.RIGHT
        if self.value == self.UP.value:
            return InstructionType.UP
        if self.value == self.DOWN.value:
            return InstructionType.DOWN
        return None

    def __str__(self):
        if self.value == self.LEFT.value:
            return 'Left'  
        if self.value == self.RIGHT.value:
            return 'Right'  
        if self.value == self.UP.value:
            return 'Up'  
        if self.value == self.DOWN.value:
            return 'Down'  
        if self.value == self.UNKNOWN.value:
            return 'Unknown'

def rotate(l, n):
    return l[-n:] + l[:-n]

def find_upwards_and_downwards_slopes(arrow, slope_angle, slope_threshold=15):
    downward_slope, upward_slope = None, None

    # Check all pairs of adjacent points
    for (p1, p2) in zip(arrow, rotate(arrow,1)):

        # Ensure all lines are moving from left to right
        if p1[0] > p2[0]:
            p1,p2 = p2,p1

        # Calculate the angle between the line and x-axis
        vector = p2 - p1
        unit_vector = vector / np.linalg.norm(vector)
        x_vector = [0,1]
        angle = np.arccos(np.dot(unit_vector, x_vector))
        deg = np.rad2deg(angle)

        # Which side of 90 degrees the angle is tells us if it's a down or up slope 
        if deg >= slope_angle-slope_threshold and deg <= slope_angle+slope_threshold:
            downward_slope = (p1,p2)
        elif deg >= 180-slope_angle-slope_threshold and deg <= 180-slope_angle+slope_threshold:
            upward_slope = (p1,p2)

    return (downward_slope, upward_slope)

def detect_direction(arrow, slope_angle):
    downward_slope, upward_slope = find_upwards_and_downwards_slopes(arrow, slope_angle)

    if upward_slope == None or downward_slope == None:
        return ArrowDirection.UNKNOWN

    # Sort the xs and ys of the slopes to help us find the direction
    downward_xs = sorted([downward_slope[0][0], downward_slope[1][0]])
    upward_xs = sorted([upward_slope[0][0], upward_slope[1][0]])
    downward_ys = sorted([downward_slope[0][1], downward_slope[1][1]])
    upward_ys = sorted([upward_slope[0][1], upward_slope[1][1]])
    
    if downward_xs[0] < upward_xs[0] and downward_xs[1] < upward_xs[1]:
        return ArrowDirection.DOWN
    if downward_xs[0] > upward_xs[0] and downward_xs[1] > upward_xs[1]:
        return ArrowDirection.UP
    if downward_ys[0] < upward_ys[0] and downward_ys[1] < upward_ys[1]:
        return ArrowDirection.RIGHT
    if downward_ys[0] > upward_ys[0] and downward_ys[1] > upward_ys[1]:
        return ArrowDirection.LEFT

    return ArrowDirection.UNKNOWN



    